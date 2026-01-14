"""
签名验签模块单元测试

测试基于规范化字符串的签名验证流程
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from app.internal.signature import (
    SignatureManager,
    SignatureException
)


class TestSignatureManager:
    """签名管理器测试类"""

    @pytest.fixture
    def rsa_keypair(self):
        """生成测试用的 RSA 密钥对"""
        private_key_pem, public_key_pem = SignatureManager.generate_rsa_keypair(key_size=2048)
        return {
            "private_key": private_key_pem,
            "public_key": public_key_pem
        }

    @pytest.fixture
    def valid_request_params(self):
        """有效的 Query 参数"""
        return {
            "workflow": "test_workflow",
            "client_id": "test_client_123",
            "param1": "value1"
        }

    # ========== 密钥生成测试 ==========

    def test_generate_rsa_keypair(self, rsa_keypair):
        """测试 RSA 密钥对生成"""
        private_key, public_key = rsa_keypair["private_key"], rsa_keypair["public_key"]

        # 验证私钥格式
        assert private_key.startswith("-----BEGIN PRIVATE KEY-----")
        assert private_key.endswith("-----END PRIVATE KEY-----\n")
        assert "PRIVATE KEY" in private_key

        # 验证公钥格式
        assert public_key.startswith("-----BEGIN PUBLIC KEY-----")
        assert public_key.endswith("-----END PUBLIC KEY-----\n")
        assert "PUBLIC KEY" in public_key

    # ========== Nonce 生成测试 ==========

    def test_generate_nonce(self):
        """测试 Nonce 生成"""
        nonce1 = SignatureManager.generate_nonce()
        nonce2 = SignatureManager.generate_nonce()

        # Nonce 应该是 32 位十六进制字符串（16 bytes = 32 hex chars）
        assert len(nonce1) == 32
        assert all(c in "0123456789abcdef" for c in nonce1)

        # 两次生成的 Nonce 应该不同
        assert nonce1 != nonce2

    # ========== Body Hash 测试 ==========

    def test_calculate_body_hash_with_content(self):
        """测试计算有内容的 Body Hash"""
        body = b'{"key": "value"}'
        hash_value = SignatureManager.calculate_body_hash(body)

        # SHA256 哈希应该是 64 位十六进制字符串
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

        # 相同内容应该产生相同哈希
        hash_value2 = SignatureManager.calculate_body_hash(b'{"key": "value"}')
        assert hash_value == hash_value2

    def test_calculate_body_hash_empty(self):
        """测试空 Body 的哈希"""
        assert SignatureManager.calculate_body_hash(b"") == ""
        assert SignatureManager.calculate_body_hash(None) == ""

    def test_calculate_body_hash_different_content(self):
        """测试不同内容产生不同哈希"""
        hash1 = SignatureManager.calculate_body_hash(b'{"a": 1}')
        hash2 = SignatureManager.calculate_body_hash(b'{"a": 2}')

        assert hash1 != hash2

    # ========== 规范化字符串测试 ==========

    def test_build_canonical_string_basic(self, rsa_keypair):
        """测试基本规范化字符串构造"""
        result = SignatureManager._build_canonical_string(
            method="post",
            path="/api/v1/test",
            query_params={"b": "2", "a": "1"},
            body_hash="abc123",
            timestamp=1704614400,
            nonce="test_nonce"
        )

        expected = "POST\n/api/v1/test\na=1&b=2\nabc123\n1704614400\ntest_nonce"
        assert result == expected

    def test_build_canonical_string_method_case(self):
        """测试 HTTP 方法名转大写"""
        result = SignatureManager._build_canonical_string(
            method="post",
            path="/api/v1/test",
            query_params={},
            body_hash="",
            timestamp=1704614400,
            nonce="nonce"
        )

        assert result.startswith("POST\n")

    def test_build_canonical_string_filters_signature_params(self):
        """测试过滤签名相关参数"""
        result = SignatureManager._build_canonical_string(
            method="GET",
            path="/api/v1/test",
            query_params={
                "data": "test",
                "x-signature": "should_be_filtered",
                "x-timestamp": "should_be_filtered",
                "x-nonce": "should_be_filtered"
            },
            body_hash="",
            timestamp=1704614400,
            nonce="nonce"
        )

        # 只应该包含 data 参数
        assert "data=test" in result
        assert "x-signature" not in result.lower()
        assert "x-timestamp" not in result.lower()
        assert "x-nonce" not in result.lower()

    # ========== 签名生成测试 ==========

    def test_generate_signature_success(self, rsa_keypair, valid_request_params):
        """测试成功生成签名"""
        body = b'{"workflow": "test"}'

        result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            query_params=valid_request_params,
            body_bytes=body,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证返回值包含所需字段
        assert "signature" in result
        assert "timestamp" in result
        assert "nonce" in result

        # 签名应该是 Base64 编码
        import base64
        try:
            base64.b64decode(result["signature"])
        except Exception:
            pytest.fail("签名应该是有效的 Base64 编码")

        # Nonce 应该是 32 字符（16 bytes = 32 hex chars）
        assert len(result["nonce"]) == 32

        # Timestamp 应该是当前时间附近的整数
        ts = int(result["timestamp"])
        current_ts = int(time.time())
        assert abs(current_ts - ts) < 10  # 允许 10 秒误差

    def test_generate_signature_without_private_key(self, valid_request_params):
        """测试没有私钥时生成签名失败"""
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.generate_signature(
                method="POST",
                path="/api/v1/test",
                query_params=valid_request_params,
                private_key_pem=""
            )
        assert "私钥不能为空" in str(exc_info.value)

    def test_generate_signature_with_invalid_private_key(self, valid_request_params):
        """测试使用无效私钥时生成签名失败"""
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.generate_signature(
                method="POST",
                path="/api/v1/test",
                query_params=valid_request_params,
                private_key_pem="invalid_key"
            )
        assert "加载私钥失败" in str(exc_info.value)

    def test_generate_signature_auto_generates_timestamp_and_nonce(self, rsa_keypair, valid_request_params):
        """测试自动生成时间戳和 Nonce"""
        result = SignatureManager.generate_signature(
            method="GET",
            path="/api/v1/test",
            query_params=valid_request_params,
            private_key_pem=rsa_keypair["private_key"],
            timestamp=None,  # 自动生成
            nonce=None  # 自动生成
        )

        assert "timestamp" in result
        assert "nonce" in result
        assert len(result["nonce"]) == 32  # 16 bytes = 32 hex chars

    # ========== 签名验证测试 ==========

    def test_verify_signature_success(self, rsa_keypair, valid_request_params):
        """测试成功验证签名"""
        body = b'{"data": "test"}'

        # 生成签名
        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            query_params=valid_request_params,
            body_bytes=body,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证签名应该成功
        result = SignatureManager.verify_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            query_params=valid_request_params,
            body_bytes=body,
            signature=sig_result["signature"],
            timestamp=sig_result["timestamp"],
            nonce=sig_result["nonce"],
            public_key_pem=rsa_keypair["public_key"]
        )

        assert result is True

    def test_verify_signature_with_tampered_body(self, rsa_keypair, valid_request_params):
        """测试 Body 被篡改时签名验证失败"""
        original_body = b'{"data": "original"}'
        tampered_body = b'{"data": "tampered"}'

        # 用原始 body 生成签名
        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/submit",
            query_params=valid_request_params,
            body_bytes=original_body,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 用篡改后的 body 验证应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/submit",
                query_params=valid_request_params,
                body_bytes=tampered_body,
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                nonce=sig_result["nonce"],
                public_key_pem=rsa_keypair["public_key"]
            )
        assert "签名验证失败" in str(exc_info.value)

    def test_verify_signature_with_tampered_query_params(self, rsa_keypair):
        """测试 Query 参数被篡改时签名验证失败"""
        original_params = {"key": "value1"}
        tampered_params = {"key": "value2"}

        # 用原始参数生成签名
        sig_result = SignatureManager.generate_signature(
            method="GET",
            path="/api/v1/test",
            query_params=original_params,
            body_bytes=None,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 用篡改后的参数验证应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="GET",
                path="/api/v1/test",
                query_params=tampered_params,
                body_bytes=None,
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                nonce=sig_result["nonce"],
                public_key_pem=rsa_keypair["public_key"]
            )
        assert "签名验证失败" in str(exc_info.value)

    def test_verify_signature_missing_required_params(self, rsa_keypair):
        """测试缺少必需参数时验证失败"""
        # 缺少签名
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                signature="",
                timestamp="123",
                nonce="abc",
                public_key_pem=rsa_keypair["public_key"]
            )
        assert "签名字符串不能为空" in str(exc_info.value)

        # 缺少时间戳
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                signature="abc",
                timestamp="",
                nonce="abc",
                public_key_pem=rsa_keypair["public_key"]
            )
        assert "时间戳不能为空" in str(exc_info.value)

        # 缺少 Nonce
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                signature="abc",
                timestamp="123",
                nonce="",
                public_key_pem=rsa_keypair["public_key"]
            )
        assert "Nonce 不能为空" in str(exc_info.value)

    def test_verify_signature_with_wrong_public_key(self, rsa_keypair, valid_request_params):
        """测试使用错误公钥时验证失败"""
        # 生成签名
        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/test",
            query_params=valid_request_params,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 生成另一对密钥的公钥
        _, wrong_public_key = SignatureManager.generate_rsa_keypair()

        # 使用错误的公钥验证应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                query_params=valid_request_params,
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                nonce=sig_result["nonce"],
                public_key_pem=wrong_public_key
            )
        assert "签名验证失败" in str(exc_info.value)

    # ========== JSON Body 验证测试 ==========

    def test_verify_signature_with_json_body(self, rsa_keypair):
        """测试 JSON Body 的签名验证"""
        # 模拟 JSON 请求
        json_body = b'{"workflow": "test", "client_id": "123"}'

        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/submit",
            query_params={},
            body_bytes=json_body,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证应该成功
        assert SignatureManager.verify_signature(
            method="POST",
            path="/api/v1/submit",
            query_params={},
            body_bytes=json_body,
            signature=sig_result["signature"],
            timestamp=sig_result["timestamp"],
            nonce=sig_result["nonce"],
            public_key_pem=rsa_keypair["public_key"]
        ) is True

    def test_verify_signature_json_body_with_different_format(self, rsa_keypair):
        """测试相同内容不同格式的 JSON Body 产生不同哈希"""
        json1 = b'{"a":1,"b":2}'
        json2 = b'{"b":2,"a":1}'  # 键顺序不同

        hash1 = SignatureManager.calculate_body_hash(json1)
        hash2 = SignatureManager.calculate_body_hash(json2)

        # 原始字节不同，哈希应该不同
        assert hash1 != hash2

    # ========== 时间戳验证测试 ==========

    def test_timestamp_valid_within_tolerance(self):
        """测试时间戳在容忍范围内有效"""
        current_time = int(time.time())
        tolerance = 300

        # 当前时间戳
        assert SignatureManager.is_timestamp_valid(current_time, tolerance) is True

        # 边界值
        assert SignatureManager.is_timestamp_valid(current_time - tolerance, tolerance) is True
        assert SignatureManager.is_timestamp_valid(current_time + tolerance, tolerance) is True

    def test_timestamp_invalid_outside_tolerance(self):
        """测试时间戳超出容忍范围无效"""
        current_time = int(time.time())
        tolerance = 300

        # 超出容忍范围
        assert SignatureManager.is_timestamp_valid(current_time - tolerance - 1, tolerance) is False
        assert SignatureManager.is_timestamp_valid(current_time + tolerance + 1, tolerance) is False

    # ========== 不同 HTTP 方法测试 ==========

    def test_signature_different_methods(self, rsa_keypair):
        """测试不同 HTTP 方法的签名验证"""
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            sig_result = SignatureManager.generate_signature(
                method=method,
                path="/api/v1/test",
                query_params={"key": "value"},
                private_key_pem=rsa_keypair["private_key"]
            )

            # 验证签名
            result = SignatureManager.verify_signature(
                method=method,
                path="/api/v1/test",
                query_params={"key": "value"},
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                nonce=sig_result["nonce"],
                public_key_pem=rsa_keypair["public_key"]
            )

            assert result is True, f"{method} 方法签名验证失败"

    def test_signature_wrong_method_fails(self, rsa_keypair):
        """测试使用错误 HTTP 方法时签名验证失败"""
        # 用 POST 生成签名
        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/test",
            private_key_pem=rsa_keypair["private_key"]
        )

        # 用 GET 验证应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="GET",
                path="/api/v1/test",
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                nonce=sig_result["nonce"],
                public_key_pem=rsa_keypair["public_key"]
            )
        assert "签名验证失败" in str(exc_info.value)

    # ========== 端到端场景测试 ==========

    def test_end_to_end_signature_flow(self, rsa_keypair):
        """测试完整的签名验证流程"""
        # 模拟客户端请求
        method = "POST"
        path = "/api/v1/workflows/submit"
        query_params = {"client_id": "123", "format": "json"}
        body = b'{"workflow": "advanced", "steps": 20}'

        # 客户端生成签名
        sig_result = SignatureManager.generate_signature(
            method=method,
            path=path,
            query_params=query_params,
            body_bytes=body,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 服务端验证签名
        assert SignatureManager.verify_signature(
            method=method,
            path=path,
            query_params=query_params,
            body_bytes=body,
            signature=sig_result["signature"],
            timestamp=sig_result["timestamp"],
            nonce=sig_result["nonce"],
            public_key_pem=rsa_keypair["public_key"]
        ) is True

    def test_get_request_without_body(self, rsa_keypair):
        """测试无 Body 的 GET 请求"""
        method = "GET"
        path = "/api/v1/queue/status"
        query_params = {"details": "true"}

        # 生成签名
        sig_result = SignatureManager.generate_signature(
            method=method,
            path=path,
            query_params=query_params,
            body_bytes=None,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证签名
        assert SignatureManager.verify_signature(
            method=method,
            path=path,
            query_params=query_params,
            body_bytes=None,
            signature=sig_result["signature"],
            timestamp=sig_result["timestamp"],
            nonce=sig_result["nonce"],
            public_key_pem=rsa_keypair["public_key"]
        ) is True
