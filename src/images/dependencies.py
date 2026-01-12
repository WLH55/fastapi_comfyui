"""
图片领域依赖项

定义图片路由的依赖项
"""

from typing import Optional
from fastapi import Header, HTTPException

from src.images.config import image_config


async def validate_image_upload(
    content_length: Optional[int] = None,
    content_type: Optional[str] = None
) -> dict:
    """
    验证图片上传请求

    Args:
        content_length: 内容长度
        content_type: 内容类型

    Returns:
        验证上下文字典

    Raises:
        HTTPException: 验证失败时
    """
    # 验证 MIME 类型
    if content_type and content_type not in image_config.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_CONTENT_TYPE",
                "message": f"不支持的图片类型: {content_type}",
                "allowed_types": image_config.ALLOWED_MIME_TYPES
            }
        )

    return {
        "content_length": content_length,
        "content_type": content_type,
        "validated": True
    }


def parse_image_params(
    filename: str,
    subfolder: str = "",
    img_type: str = "output"
) -> dict:
    """
    解析图片参数

    Args:
        filename: 文件名
        subfolder: 子文件夹
        img_type: 图片类型

    Returns:
        解析后的参数字典
    """
    return {
        "filename": filename,
        "subfolder": subfolder,
        "type": img_type
    }
