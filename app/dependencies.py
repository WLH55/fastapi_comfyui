"""
公共依赖项模块
"""

from typing import Optional
from fastapi import Header, HTTPException


async def get_client_id(x_client_id: Optional[str] = Header(None)) -> Optional[str]:
    """
    获取客户端 ID

    Args:
        x_client_id: 请求头中的客户端 ID

    Returns:
        客户端 ID
    """
    if x_client_id and len(x_client_id) > 100:
        raise HTTPException(
            status_code=400,
            detail={"message": "客户端 ID 长度不能超过 100 个字符"}
        )
    return x_client_id
