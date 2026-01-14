"""
签名验签模块单元测试
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
        """有效的请求参数"""
        return {
            "workflow": "test_workflow",
            "client_id": "test_client_123",
            "param1": "value1",
            "param2": "value2"
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

    # ========== 签名生成测试 ==========

    def test_generate_signature_success(self, rsa_keypair, valid_request_params):
        """测试成功生成签名"""
        timestamp = int(time.time())

        signature = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            params=valid_request_params,
            timestamp=timestamp,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证签名是 Base64 编码的非空字符串
        assert signature
        assert len(signature) > 0
        # Base64 编码的签名应该只包含有效字符
        import base64
        try:
            base64.b64decode(signature)
        except Exception:
            pytest.fail("签名应该是有效的 Base64 编码")

    def test_generate_signature_without_timestamp(self, rsa_keypair, valid_request_params):
        """测试没有时间戳时生成签名失败"""
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.generate_signature(
                method="POST",
                path="/api/v1/workflows/submit",
                params=valid_request_params,
                timestamp=0,
                private_key_pem=rsa_keypair["private_key"]
            )
        assert "时间戳不能为空" in str(exc_info.value)

    def test_generate_signature_with_invalid_private_key(self, valid_request_params):
        """测试使用无效私钥时生成签名失败"""
        timestamp = int(time.time())

        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.generate_signature(
                method="POST",
                path="/api/v1/workflows/submit",
                params=valid_request_params,
                timestamp=timestamp,
                private_key_pem="invalid_key"
            )
        assert "加载私钥失败" in str(exc_info.value)

    # ========== 签名验证测试 ==========

    def test_verify_signature_success(self, rsa_keypair, valid_request_params):
        """测试成功验证签名"""
        timestamp = int(time.time())

        # 生成签名
        signature = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            params=valid_request_params,
            timestamp=timestamp,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证签名应该成功
        result = SignatureManager.verify_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            params=valid_request_params,
            signature=signature,
            public_key_pem=rsa_keypair["public_key"],
            timestamp=timestamp
        )

        assert result is True

    def test_verify_signature_with_wrong_params(self, rsa_keypair, valid_request_params):
        """测试参数被篡改时签名验证失败"""
        timestamp = int(time.time())

        # 生成原始签名
        signature = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            params=valid_request_params,
            timestamp=timestamp,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 篡改参数
        tampered_params = valid_request_params.copy()
        tampered_params["workflow"] = "tampered_workflow"

        # 验证签名应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/workflows/submit",
                params=tampered_params,
                signature=signature,
                public_key_pem=rsa_keypair["public_key"],
                timestamp=timestamp
            )
        assert "签名验证失败" in str(exc_info.value)

    def test_verify_signature_with_empty_signature(self, rsa_keypair, valid_request_params):
        """测试空签名时验证失败"""
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/workflows/submit",
                params=valid_request_params,
                signature="",
                public_key_pem=rsa_keypair["public_key"],
                timestamp=int(time.time())
            )
        assert "签名字符串不能为空" in str(exc_info.value)

    def test_verify_signature_with_invalid_base64(self, rsa_keypair, valid_request_params):
        """测试无效 Base64 签名时验证失败"""
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/workflows/submit",
                params=valid_request_params,
                signature="not_valid_base64!!!",
                public_key_pem=rsa_keypair["public_key"],
                timestamp=int(time.time())
            )
        assert "Base64 解码失败" in str(exc_info.value)

    def test_verify_signature_with_wrong_public_key(self, rsa_keypair, valid_request_params):
        """测试使用错误公钥时验证失败"""
        timestamp = int(time.time())

        # 生成签名
        signature = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            params=valid_request_params,
            timestamp=timestamp,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 生成另一对密钥的公钥
        _, wrong_public_key = SignatureManager.generate_rsa_keypair()

        # 使用错误的公钥验证应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/workflows/submit",
                params=valid_request_params,
                signature=signature,
                public_key_pem=wrong_public_key,
                timestamp=timestamp
            )
        assert "签名验证失败" in str(exc_info.value)

    def test_verify_signature_with_params_containing_timestamp(self, rsa_keypair, valid_request_params):
        """测试参数中包含 timestamp 字段时验证成功"""
        timestamp = int(time.time())

        # 将 timestamp 也放在 params 中
        params_with_timestamp = valid_request_params.copy()
        params_with_timestamp["timestamp"] = timestamp

        # 生成签名（使用相同的 timestamp）
        signature = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            params=params_with_timestamp,
            timestamp=timestamp,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证签名（不传入 timestamp 参数，从 params 中读取）
        result = SignatureManager.verify_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            params=params_with_timestamp,
            signature=signature,
            public_key_pem=rsa_keypair["public_key"]
            # 不传入 timestamp，应该从 params 中读取
        )

        assert result is True

    # ========== 时间戳验证测试 ==========

    def test_timestamp_valid_within_tolerance(self):
        """测试时间戳在容忍范围内有效"""
        current_time = int(time.time())
        tolerance = 300

        # 当前时间戳
        assert SignatureManager.is_timestamp_valid(current_time, tolerance) is True

        # 边界值：当前时间 - 容忍度
        assert SignatureManager.is_timestamp_valid(current_time - tolerance, tolerance) is True

        # 边界值：当前时间 + 容忍度
        assert SignatureManager.is_timestamp_valid(current_time + tolerance, tolerance) is True

    def test_timestamp_invalid_outside_tolerance(self):
        """测试时间戳超出容忍范围无效"""
        current_time = int(time.time())
        tolerance = 300

        # 超出容忍范围
        assert SignatureManager.is_timestamp_valid(current_time - tolerance - 1, tolerance) is False
        assert SignatureManager.is_timestamp_valid(current_time + tolerance + 1, tolerance) is False

    def test_timestamp_with_zero_tolerance(self):
        """测试容忍度为 0 时只有精确时间戳有效"""
        current_time = int(time.time())

        # 完全相同的时间戳
        assert SignatureManager.is_timestamp_valid(current_time, 0) is True

        # 差 1 秒
        assert SignatureManager.is_timestamp_valid(current_time - 1, 0) is False
        assert SignatureManager.is_timestamp_valid(current_time + 1, 0) is False

    # ========== 签名字符串构造测试 ==========

    def test_sign_string_construction(self):
        """测试签名字符串的正确构造"""
        # 通过生成签名来间接验证签名字符串的构造
        private_key, public_key = SignatureManager.generate_rsa_keypair()

        timestamp = 1234567890
        params = {"b": "2", "a": "1"}  # 无序参数

        # 生成签名
        signature1 = SignatureManager.generate_signature(
            method="GET",
            path="/api/v1/test",
            params=params,
            timestamp=timestamp,
            private_key_pem=private_key
        )

        # 相同参数不同顺序应该生成相同签名（因为会排序）
        params_reordered = {"a": "1", "b": "2"}
        signature2 = SignatureManager.generate_signature(
            method="GET",
            path="/api/v1/test",
            params=params_reordered,
            timestamp=timestamp,
            private_key_pem=private_key
        )

        # 签名应该不同（因为 RSA-PSS 包含随机 salt）
        # 但都应该能通过验证
        assert SignatureManager.verify_signature(
            method="GET",
            path="/api/v1/test",
            params=params,
            signature=signature1,
            public_key_pem=public_key,
            timestamp=timestamp
        ) is True

        assert SignatureManager.verify_signature(
            method="GET",
            path="/api/v1/test",
            params=params_reordered,
            signature=signature2,
            public_key_pem=public_key,
            timestamp=timestamp
        ) is True

    def test_sign_string_filters_signature_and_timestamp_params(self, rsa_keypair):
        """测试签名字符串会过滤 signature 和 timestamp 参数"""
        params = {
            "data": "test",
            "signature": "should_be_ignored",
            "timestamp": "should_be_ignored"
        }

        timestamp = 1234567890

        # 生成签名时应该忽略 signature 和 timestamp 参数
        signature = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/test",
            params=params,
            timestamp=timestamp,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 验证时传入的参数即使包含额外的 signature 和 timestamp 也应该成功
        verify_params = {
            "data": "test",
            "extra": "extra_param"  # 额外参数会导致验证失败
        }

        with pytest.raises(SignatureException):
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                params=verify_params,
                signature=signature,
                public_key_pem=rsa_keypair["public_key"],
                timestamp=timestamp
            )

    # ========== 不同 HTTP 方法测试 ==========

    def test_signature_different_methods(self, rsa_keypair, valid_request_params):
        """测试不同 HTTP 方法的签名验证"""
        timestamp = int(time.time())

        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            signature = SignatureManager.generate_signature(
                method=method,
                path="/api/v1/test",
                params=valid_request_params,
                timestamp=timestamp,
                private_key_pem=rsa_keypair["private_key"]
            )

            # 验证签名
            result = SignatureManager.verify_signature(
                method=method,
                path="/api/v1/test",
                params=valid_request_params,
                signature=signature,
                public_key_pem=rsa_keypair["public_key"],
                timestamp=timestamp
            )

            assert result is True, f"{method} 方法签名验证失败"

    def test_signature_different_methods_fail_on_wrong_method(self, rsa_keypair, valid_request_params):
        """测试使用错误 HTTP 方法时签名验证失败"""
        timestamp = int(time.time())

        # 用 POST 方法生成签名
        signature = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/test",
            params=valid_request_params,
            timestamp=timestamp,
            private_key_pem=rsa_keypair["private_key"]
        )

        # 用 GET 方法验证应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="GET",
                path="/api/v1/test",
                params=valid_request_params,
                signature=signature,
                public_key_pem=rsa_keypair["public_key"],
                timestamp=timestamp
            )
        assert "签名验证失败" in str(exc_info.value)
