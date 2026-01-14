"""
签名验签模块

使用 RSA-PSS 算法进行请求签名和验证

采用规范化签名字符串：METHOD\nPATH\nQUERY\nBODY_HASH\nTIMESTAMP\nNONCE
"""

import time
import base64
import hashlib
import secrets
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

    提供基于规范化字符串的 RSA 签名生成和验证功能

    签名字符串格式：METHOD\nPATH\nQUERY\nBODY_HASH\nTIMESTAMP\nNONCE
    """

    # 签名字符串格式版本（用于未来兼容性）
    VERSION = "v1"

    # Header 名称常量
    HEADER_SIGNATURE = "X-Signature"
    HEADER_TIMESTAMP = "X-Timestamp"
    HEADER_NONCE = "X-Nonce"

    @staticmethod
    def generate_nonce() -> str:
        """
        生成随机 Nonce 字符串

        用于防止重放攻击，保证即使参数完全一致，每次签名的结果也不同

        Returns:
            32 位随机十六进制字符串
        """
        return secrets.token_hex(16)

    @staticmethod
    def calculate_body_hash(body_bytes: Optional[bytes]) -> str:
        """
        计算请求体的 SHA256 哈希值

        Args:
            body_bytes: 请求体的原始字节（可能是 None）

        Returns:
            十六进制格式的哈希值，空 body 返回空字符串
        """
        if not body_bytes:
            return ""
        return hashlib.sha256(body_bytes).hexdigest()

    @staticmethod
    def _build_canonical_string(
        method: str,
        path: str,
        query_params: Dict[str, Any],
        body_hash: str,
        timestamp: int,
        nonce: str
    ) -> str:
        """
        构造规范化待签名字符串

        格式：METHOD\nPATH\nQUERY\nBODY_HASH\nTIMESTAMP\nNONCE

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            path: 请求路径 (不含域名和 query)
            query_params: Query 参数字典
            body_hash: 请求体的 SHA256 哈希值
            timestamp: Unix 时间戳（秒）
            nonce: 随机字符串

        Returns:
            规范化的待签名字符串
        """
        # 1. 方法名转大写
        method = method.upper()

        # 2. 路径保持原样

        # 3. Query 参数排序并 URL 编码
        # 过滤掉签名相关的 Header 参数（如果误放入 Query）
        filtered_params = {
            k: v for k, v in query_params.items()
            if k not in (SignatureManager.HEADER_SIGNATURE.lower(),
                        SignatureManager.HEADER_TIMESTAMP.lower(),
                        SignatureManager.HEADER_NONCE.lower())
        }
        # 按参数名字典序排序
        sorted_params = dict(sorted(filtered_params.items()))
        # URL 编码
        query_string = urlencode(sorted_params, doseq=True) if sorted_params else ""

        # 4. 拼接规范化字符串
        canonical_string = f"{method}\n{path}\n{query_string}\n{body_hash}\n{timestamp}\n{nonce}"

        return canonical_string

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
        query_params: Optional[Dict[str, Any]] = None,
        body_bytes: Optional[bytes] = None,
        timestamp: Optional[int] = None,
        nonce: Optional[str] = None,
        private_key_pem: str = ""
    ) -> Dict[str, str]:
        """
        生成签名

        Args:
            method: HTTP 方法
            path: 请求路径
            query_params: Query 参数字典（可选）
            body_bytes: 请求体的原始字节（可选）
            timestamp: Unix 时间戳（秒），不传则自动生成
            nonce: 随机字符串，不传则自动生成
            private_key_pem: PEM 格式的私钥

        Returns:
            包含签名相关信息的字典：
            {
                "signature": Base64 编码的签名字符串,
                "timestamp": Unix 时间戳,
                "nonce": 随机字符串
            }
        """
        if not private_key_pem:
            raise SignatureException("私钥不能为空")

        # 自动生成时间戳和 Nonce
        if timestamp is None:
            timestamp = int(time.time())
        if nonce is None:
            nonce = SignatureManager.generate_nonce()

        # 计算 Body Hash
        body_hash = SignatureManager.calculate_body_hash(body_bytes)

        # 确保 query_params 不为 None
        if query_params is None:
            query_params = {}

        # 构造规范化字符串
        canonical_string = SignatureManager._build_canonical_string(
            method=method,
            path=path,
            query_params=query_params,
            body_hash=body_hash,
            timestamp=timestamp,
            nonce=nonce
        )

        # 加载私钥并签名
        private_key = SignatureManager._load_private_key(private_key_pem)

        try:
            signature_bytes = private_key.sign(
                canonical_string.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            signature = base64.b64encode(signature_bytes).decode("utf-8")
        except Exception as e:
            raise SignatureException(f"签名生成失败: {str(e)}")

        return {
            "signature": signature,
            "timestamp": str(timestamp),
            "nonce": nonce
        }

    @staticmethod
    def verify_signature(
        method: str,
        path: str,
        query_params: Optional[Dict[str, Any]] = None,
        body_bytes: Optional[bytes] = None,
        signature: str = "",
        timestamp: str = "",
        nonce: str = "",
        public_key_pem: str = ""
    ) -> bool:
        """
        验证签名

        Args:
            method: HTTP 方法
            path: 请求路径
            query_params: Query 参数字典（可选）
            body_bytes: 请求体的原始字节（可选）
            signature: 待验证的签名字符串
            timestamp: Unix 时间戳字符串
            nonce: 随机字符串
            public_key_pem: PEM 格式的公钥

        Returns:
            验证成功返回 True，失败抛出 SignatureException
        """
        # 参数校验
        if not signature:
            raise SignatureException("签名字符串不能为空")
        if not timestamp:
            raise SignatureException("时间戳不能为空")
        if not nonce:
            raise SignatureException("Nonce 不能为空")
        if not public_key_pem:
            raise SignatureException("公钥不能为空")

        # 计算 Body Hash
        body_hash = SignatureManager.calculate_body_hash(body_bytes)

        # 确保 query_params 不为 None
        if query_params is None:
            query_params = {}

        # 构造规范化字符串
        canonical_string = SignatureManager._build_canonical_string(
            method=method,
            path=path,
            query_params=query_params,
            body_hash=body_hash,
            timestamp=int(timestamp),
            nonce=nonce
        )

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
                canonical_string.encode("utf-8"),
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
