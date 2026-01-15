"""
签名验签模块

使用 HMAC-SHA256 算法进行请求签名和验证

简化版：单端点，全局配置一个密钥
"""

import time
import hmac
import hashlib
from typing import Dict, Optional


class SignatureException(Exception):
    """签名验签异常"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class SignatureManager:
    """
    签名管理器

    使用 HMAC-SHA256 进行签名生成和验证

    签名字符串格式：METHOD\nPATH\nTIMESTAMP\nSECRET
    """

    @staticmethod
    def generate_signature(
        method: str,
        path: str,
        timestamp: Optional[int] = None,
        secret: str = ""
    ) -> Dict[str, str]:
        """
        生成签名

        Args:
            method: HTTP 方法
            path: 请求路径
            timestamp: Unix 时间戳（秒），不传则自动生成
            secret: 应用密钥

        Returns:
            {
                "signature": 十六进制签名字符串,
                "timestamp": Unix 时间戳字符串
            }
        """
        if not secret:
            raise SignatureException("密钥不能为空")

        # 自动生成时间戳
        if timestamp is None:
            timestamp = int(time.time())

        # 构造签名字符串
        sign_string = f"{method.upper()}\n{path}\n{timestamp}\n{secret}"

        # HMAC-SHA256 签名
        signature = hmac.new(
            secret.encode("utf-8"),
            sign_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return {
            "signature": signature,
            "timestamp": str(timestamp)
        }

    @staticmethod
    def verify_signature(
        method: str,
        path: str,
        signature: str = "",
        timestamp: str = "",
        secret: str = ""
    ) -> bool:
        """
        验证签名

        Args:
            method: HTTP 方法
            path: 请求路径
            signature: 待验证的签名字符串
            timestamp: Unix 时间戳字符串
            secret: 应用密钥

        Returns:
            验证成功返回 True，失败抛出 SignatureException
        """
        # 参数校验
        if not signature:
            raise SignatureException("签名字符串不能为空")
        if not timestamp:
            raise SignatureException("时间戳不能为空")
        if not secret:
            raise SignatureException("密钥不能为空")

        # 重新生成签名进行对比
        expected = SignatureManager.generate_signature(
            method=method,
            path=path,
            timestamp=int(timestamp),
            secret=secret
        )

        # 使用恒定时间比较，防止时序攻击
        if not hmac.compare_digest(expected["signature"], signature):
            raise SignatureException("签名验证失败")

        return True

    @staticmethod
    def is_timestamp_valid(timestamp: int, tolerance: int = 300) -> bool:
        """
        验证时间戳有效性（防重放攻击）

        Args:
            timestamp: 待验证的时间戳（秒）
            tolerance: 容忍时间差（秒），默认 5 分钟

        Returns:
            有效返回 True，否则返回 False
        """
        current_time = int(time.time())
        time_diff = abs(current_time - timestamp)

        return time_diff <= tolerance
