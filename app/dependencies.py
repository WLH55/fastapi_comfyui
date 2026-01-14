"""
公共依赖项模块

包含签名验证等 FastAPI 依赖注入函数
"""

from fastapi import Request, Query, HTTPException, status

from app.config import settings
from app.internal.signature import SignatureManager, SignatureException


async def verify_signature(
    request: Request,
    signature: str = Query(..., description="RSA 签名字符串"),
    timestamp: int = Query(..., description="请求时间戳（秒）")
) -> None:
    """
    签名验证依赖

    验证请求签名的有效性，防止参数篡改和重放攻击

    Args:
        request: FastAPI 请求对象
        signature: Query 参数中的签名字符串
        timestamp: Query 参数中的时间戳

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

        # 获取所有请求参数（Query + FormData + JSON）
        params = {}

        # Query 参数
        params.update(request.query_params)

        # 处理 FormData/Body 参数
        content_type = request.headers.get("content-type", "")

        if "application/x-www-form-urlencoded" in content_type:
            # Form 数据
            form_data = await request.form()
            params.update(dict(form_data))
        elif "application/json" in content_type:
            # JSON 数据（签名验证时需要原始 JSON）
            # 注意：由于 request.body() 只能读取一次，需要特殊处理
            # 这里我们使用客户端应该传递的参数方式
            # 对于 JSON 请求，客户端需要将参数也放在 Query 中或使用 FormData
            # 或者我们使用 middleware 在请求到达前缓存 body
            pass

        # 执行签名验证
        SignatureManager.verify_signature(
            method=method,
            path=path,
            params=params,
            signature=signature,
            public_key_pem=settings.SIGNATURE_PUBLIC_KEY,
            timestamp=timestamp
        )

        # 验证时间戳（防重放攻击）
        if settings.SIGNATURE_TIMESTAMP_TOLERANCE > 0:
            if not SignatureManager.is_timestamp_valid(
                timestamp,
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
