"""
签名验签模块单元测试

测试基于 HMAC-SHA256 的签名验证流程（简化版）
"""

import time
import pytest

from app.internal.signature import (
    SignatureManager,
    SignatureException
)


class TestSignatureManager:
    """签名管理器测试类"""

    @pytest.fixture
    def secret(self):
        """测试用的密钥"""
        return "test_secret_key_12345678"

    # ========== 签名生成测试 ==========

    def test_generate_signature_success(self, secret):
        """测试成功生成签名"""
        result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            secret=secret
        )

        # 验证返回值
        assert "signature" in result
        assert "timestamp" in result

        # 签名应该是 64 位十六进制字符串（SHA256）
        assert len(result["signature"]) == 64
        assert all(c in "0123456789abcdef" for c in result["signature"])

        # Timestamp 应该是当前时间附近的整数
        ts = int(result["timestamp"])
        current_ts = int(time.time())
        assert abs(current_ts - ts) < 10

    def test_generate_signature_without_secret(self):
        """测试没有密钥时生成签名失败"""
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.generate_signature(
                method="POST",
                path="/api/v1/test",
                secret=""
            )
        assert "密钥不能为空" in str(exc_info.value)

    def test_generate_signature_custom_timestamp(self, secret):
        """测试使用自定义时间戳"""
        custom_ts = 1704614400

        result = SignatureManager.generate_signature(
            method="GET",
            path="/api/v1/test",
            timestamp=custom_ts,
            secret=secret
        )

        assert int(result["timestamp"]) == custom_ts

    def test_generate_signature_method_case_insensitive(self, secret):
        """测试 HTTP 方法大小写不敏感"""
        result1 = SignatureManager.generate_signature(
            method="post",
            path="/api/v1/test",
            secret=secret
        )

        result2 = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/test",
            secret=secret
        )

        # 签名应该相同（方法都转大写）
        assert result1["signature"] == result2["signature"]

    # ========== 签名验证测试 ==========

    def test_verify_signature_success(self, secret):
        """测试成功验证签名"""
        # 生成签名
        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            secret=secret
        )

        # 验证签名应该成功
        result = SignatureManager.verify_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            signature=sig_result["signature"],
            timestamp=sig_result["timestamp"],
            secret=secret
        )

        assert result is True

    def test_verify_signature_wrong_method(self, secret):
        """测试错误的 HTTP 方法导致签名验证失败"""
        # 用 POST 生成签名
        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/test",
            secret=secret
        )

        # 用 GET 验证应该失败
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="GET",
                path="/api/v1/test",
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                secret=secret
            )
        assert "签名验证失败" in str(exc_info.value)

    def test_verify_signature_wrong_path(self, secret):
        """测试错误的路径导致签名验证失败"""
        sig_result = SignatureManager.generate_signature(
            method="GET",
            path="/api/v1/test",
            secret=secret
        )

        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="GET",
                path="/api/v1/wrong",
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                secret=secret
            )
        assert "签名验证失败" in str(exc_info.value)

    def test_verify_signature_wrong_secret(self):
        """测试错误的密钥导致签名验证失败"""
        secret1 = "secret_111"
        secret2 = "secret_222"

        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/test",
            secret=secret1
        )

        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                secret=secret2
            )
        assert "签名验证失败" in str(exc_info.value)

    def test_verify_signature_missing_params(self, secret):
        """测试缺少必需参数"""
        # 缺少签名
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                signature="",
                timestamp="123",
                secret=secret
            )
        assert "签名字符串不能为空" in str(exc_info.value)

        # 缺少时间戳
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                signature="abc",
                timestamp="",
                secret=secret
            )
        assert "时间戳不能为空" in str(exc_info.value)

        # 缺少密钥
        with pytest.raises(SignatureException) as exc_info:
            SignatureManager.verify_signature(
                method="POST",
                path="/api/v1/test",
                signature="abc",
                timestamp="123",
                secret=""
            )
        assert "密钥不能为空" in str(exc_info.value)

    # ========== 时间戳验证测试 ==========

    def test_timestamp_valid_within_tolerance(self):
        """测试时间戳在容忍范围内有效"""
        current_time = int(time.time())
        tolerance = 300

        assert SignatureManager.is_timestamp_valid(current_time, tolerance) is True
        assert SignatureManager.is_timestamp_valid(current_time - tolerance, tolerance) is True
        assert SignatureManager.is_timestamp_valid(current_time + tolerance, tolerance) is True

    def test_timestamp_invalid_outside_tolerance(self):
        """测试时间戳超出容忍范围无效"""
        current_time = int(time.time())
        tolerance = 300

        assert SignatureManager.is_timestamp_valid(current_time - tolerance - 1, tolerance) is False
        assert SignatureManager.is_timestamp_valid(current_time + tolerance + 1, tolerance) is False

    # ========== 不同 HTTP 方法测试 ==========

    def test_signature_different_methods(self, secret):
        """测试不同 HTTP 方法的签名"""
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            sig_result = SignatureManager.generate_signature(
                method=method,
                path="/api/v1/test",
                secret=secret
            )

            result = SignatureManager.verify_signature(
                method=method,
                path="/api/v1/test",
                signature=sig_result["signature"],
                timestamp=sig_result["timestamp"],
                secret=secret
            )

            assert result is True

    # ========== 端到端场景测试 ==========

    def test_end_to_end_flow(self, secret):
        """测试完整的签名验证流程"""
        # 生成签名
        sig_result = SignatureManager.generate_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            secret=secret
        )

        # 验证签名
        assert SignatureManager.verify_signature(
            method="POST",
            path="/api/v1/workflows/submit",
            signature=sig_result["signature"],
            timestamp=sig_result["timestamp"],
            secret=secret
        ) is True

    def test_get_request(self, secret):
        """测试 GET 请求"""
        sig_result = SignatureManager.generate_signature(
            method="GET",
            path="/api/v1/queue/status",
            secret=secret
        )

        assert SignatureManager.verify_signature(
            method="GET",
            path="/api/v1/queue/status",
            signature=sig_result["signature"],
            timestamp=sig_result["timestamp"],
            secret=secret
        ) is True
