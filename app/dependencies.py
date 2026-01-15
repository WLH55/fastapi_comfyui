"""
公共依赖项模块

包含签名验证等 FastAPI 依赖注入函数
"""

from fastapi import Request, Header, HTTPException, status

from app.config import settings
from app.internal.signature import SignatureManager, SignatureException


async def verify_signature(
    request: Request,
    x_timestamp: str | None = Header(None,description="请求时间戳（秒）"),
    x_signature: str | None = Header(None,description="HMAC-SHA256 签名")
) -> None:
    """
    签名验证依赖

    从 HTTP Header 中读取签名参数并验证，防止参数篡改和重放攻击

    Header 参数：
        X-Timestamp: Unix 时间戳（秒）
        X-Signature: HMAC-SHA256 签名

    Args:
        request: FastAPI 请求对象
        x_timestamp: Header 中的时间戳
        x_signature: Header 中的签名字符串

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

    # 检查密钥配置
    if not settings.APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器配置错误：签名密钥未配置"
        )

    try:
        # 获取请求方法和路径
        method = request.method
        path = request.url.path

        # 验证时间戳（防重放攻击）
        try:
            timestamp_int = int(x_timestamp)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="时间戳格式无效"
            )

        if settings.SIGNATURE_TIMESTAMP_TOLERANCE > 0:
            if not SignatureManager.is_timestamp_valid(
                timestamp_int,
                settings.SIGNATURE_TIMESTAMP_TOLERANCE
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"请求时间戳过期，允许时间差: {settings.SIGNATURE_TIMESTAMP_TOLERANCE} 秒"
                )

        # 执行签名验证
        SignatureManager.verify_signature(
            method=method,
            path=path,
            signature=x_signature,
            timestamp=x_timestamp,
            secret=settings.APP_SECRET
        )

    except SignatureException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"签名验证失败: {e.message}"
        )
