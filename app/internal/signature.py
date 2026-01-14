"""
签名验签模块

使用 RSA-PSS 算法进行请求签名和验证
"""

import time
import base64
import hashlib
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature


class SignatureException(Exception):
    """签名验签异常"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class SignatureManager:
    """
    签名管理器

    提供 RSA 签名生成和验证功能
    """

    @staticmethod
    def _build_sign_string(method: str, path: str, params: Dict[str, Any], timestamp: int) -> str:
        """
        构造待签名字符串

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            path: 请求路径 (不含域名和 query)
            params: 请求参数 (不含 signature 和 timestamp)
            timestamp: 时间戳

        Returns:
            待签名字符串
        """
        # 过滤掉签名相关的参数
        filtered_params = {k: v for k, v in params.items() if k not in ("signature", "timestamp")}

        # 按参数名字典序排序
        sorted_params = dict(sorted(filtered_params.items()))

        # 构造签名字符串: method\npath\nsorted_query\ntimestamp
        query_string = urlencode(sorted_params, doseq=True) if sorted_params else ""
        sign_string = f"{method}\n{path}\n{query_string}\n{timestamp}"

        return sign_string

    @staticmethod
    def _load_private_key(private_key_pem: str) -> rsa.RSAPrivateKey:
        """
        加载 RSA 私钥

        Args:
            private_key_pem: PEM 格式的私钥字符串

        Returns:
            RSA 私钥对象
        """
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            if not isinstance(private_key, rsa.RSAPrivateKey):
                raise SignatureException("无效的私钥格式，需要 RSA 私钥")
            return private_key
        except Exception as e:
            raise SignatureException(f"加载私钥失败: {str(e)}")

    @staticmethod
    def _load_public_key(public_key_pem: str) -> rsa.RSAPublicKey:
        """
        加载 RSA 公钥

        Args:
            public_key_pem: PEM 格式的公钥字符串

        Returns:
            RSA 公钥对象
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            if not isinstance(public_key, rsa.RSAPublicKey):
                raise SignatureException("无效的公钥格式，需要 RSA 公钥")
            return public_key
        except Exception as e:
            raise SignatureException(f"加载公钥失败: {str(e)}")

    @staticmethod
    def generate_signature(
        method: str,
        path: str,
        params: Dict[str, Any],
        timestamp: int,
        private_key_pem: str
    ) -> str:
        """
        生成签名

        Args:
            method: HTTP 方法
            path: 请求路径
            params: 请求参数
            timestamp: 时间戳（秒）
            private_key_pem: PEM 格式的私钥

        Returns:
            Base64 编码的签名字符串
        """
        if not timestamp:
            raise SignatureException("时间戳不能为空")

        # 构造待签名字符串
        sign_string = SignatureManager._build_sign_string(method, path, params, timestamp)

        # 加载私钥
        private_key = SignatureManager._load_private_key(private_key_pem)

        # 计算签名
        try:
            signature = private_key.sign(
                sign_string.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            # Base64 编码
            return base64.b64encode(signature).decode("utf-8")
        except Exception as e:
            raise SignatureException(f"签名生成失败: {str(e)}")

    @staticmethod
    def verify_signature(
        method: str,
        path: str,
        params: Dict[str, Any],
        signature: str,
        public_key_pem: str,
        timestamp: Optional[int] = None
    ) -> bool:
        """
        验证签名

        Args:
            method: HTTP 方法
            path: 请求路径
            params: 请求参数（包含 signature 和 timestamp）
            signature: 待验证的签名字符串
            public_key_pem: PEM 格式的公钥
            timestamp: 时间戳（可选，用于验证时效性）

        Returns:
            验证成功返回 True，失败抛出 SignatureException
        """
        if not signature:
            raise SignatureException("签名字符串不能为空")

        # 解析时间戳
        effective_timestamp = timestamp
        if effective_timestamp is None and "timestamp" in params:
            try:
                effective_timestamp = int(params["timestamp"])
            except (ValueError, TypeError):
                raise SignatureException("时间戳格式无效")

        if effective_timestamp is None:
            raise SignatureException("时间戳参数缺失")

        # 构造待签名字符串
        sign_string = SignatureManager._build_sign_string(method, path, params, effective_timestamp)

        # 加载公钥
        public_key = SignatureManager._load_public_key(public_key_pem)

        # 解码签名
        try:
            signature_bytes = base64.b64decode(signature)
        except Exception:
            raise SignatureException("签名字符串 Base64 解码失败")

        # 验证签名
        try:
            public_key.verify(
                signature_bytes,
                sign_string.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            raise SignatureException("签名验证失败")
        except Exception as e:
            raise SignatureException(f"签名验证异常: {str(e)}")

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

    @staticmethod
    def generate_rsa_keypair(key_size: int = 2048) -> tuple[str, str]:
        """
        生成 RSA 密钥对

        Args:
            key_size: 密钥长度，默认 2048 位

        Returns:
            (private_key_pem, public_key_pem) 私钥和公钥的 PEM 格式字符串
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        return private_key_pem, public_key_pem
