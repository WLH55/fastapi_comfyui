"""
公共依赖项模块

包含签名验证等 FastAPI 依赖注入函数
"""

from fastapi import Request, Header, HTTPException, status

from app.config import settings
from app.internal.signature import SignatureManager, SignatureException


async def verify_signature(
    request: Request,
    x_signature: str = Header(..., description="RSA 签名字符串"),
    x_timestamp: str = Header(..., description="请求时间戳（秒）"),
    x_nonce: str = Header(..., description="随机字符串")
) -> None:
    """
    签名验证依赖

    从 HTTP Header 中读取签名参数并验证，防止参数篡改和重放攻击

    Header 参数：
        X-Signature: Base64 编码的 RSA 签名
        X-Timestamp: Unix 时间戳（秒）
        X-Nonce: 随机字符串（防止重放）

    Args:
        request: FastAPI 请求对象
        x_signature: Header 中的签名字符串
        x_timestamp: Header 中的时间戳
        x_nonce: Header 中的随机字符串

    Raises:
        HTTPException: 签名验证失败时抛出 401 错误

    Usage:
        ```python
        @router.post("/workflows/submit", dependencies=[Depends(verify_signature)])
        async def submit_workflow(...):
            ...
        ```
    """
    # 全局开关控制
    if not settings.SIGNATURE_ENABLED:
        return

    # 检查公钥配置
    if not settings.SIGNATURE_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器签名配置错误：公钥未配置"
        )

    try:
        # 获取请求方法和路径
        method = request.method
        path = request.url.path

        # 获取 Query 参数
        query_params = dict(request.query_params)

        # 获取请求体原始字节
        body_bytes = await request.body()

        # 执行签名验证
        SignatureManager.verify_signature(
            method=method,
            path=path,
            query_params=query_params,
            body_bytes=body_bytes,
            signature=x_signature,
            timestamp=x_timestamp,
            nonce=x_nonce,
            public_key_pem=settings.SIGNATURE_PUBLIC_KEY
        )

        # 验证时间戳（防重放攻击）
        if settings.SIGNATURE_TIMESTAMP_TOLERANCE > 0:
            try:
                timestamp_int = int(x_timestamp)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="时间戳格式无效"
                )

            if not SignatureManager.is_timestamp_valid(
                timestamp_int,
                settings.SIGNATURE_TIMESTAMP_TOLERANCE
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"请求时间戳过期，允许时间差: {settings.SIGNATURE_TIMESTAMP_TOLERANCE} 秒"
                )

    except SignatureException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"签名验证失败: {e.message}"
        )
