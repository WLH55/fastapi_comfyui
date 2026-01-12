"""
工作流领域依赖项

定义工作流路由的依赖项
"""

from typing import Optional
from fastapi import Header, HTTPException

from src.workflows.exceptions import WorkflowSubmitError


async def verify_client_id(x_client_id: Optional[str] = Header(None)) -> Optional[str]:
    """
    验证客户端 ID（可选）

    Args:
        x_client_id: 请求头中的客户端 ID

    Returns:
        客户端 ID

    Raises:
        HTTPException: 验证失败时
    """
    if x_client_id and len(x_client_id) > 100:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_CLIENT_ID",
                "message": "客户端 ID 长度不能超过 100 个字符"
            }
        )

    return x_client_id


async def validate_workflow_submit(
    x_client_id: Optional[str] = Header(None)
) -> dict:
    """
    验证工作流提交请求

    Args:
        x_client_id: 请求头中的客户端 ID

    Returns:
        验证上下文字典
    """
    return {
        "client_id": x_client_id,
        "validated": True
    }
