"""
图片领域工具函数

定义图片模块的非业务逻辑函数
"""

from typing import Dict, Any
from pathlib import Path
from urllib.parse import urlencode

from src.config import settings


def build_image_url(filename: str, subfolder: str = "", img_type: str = "output") -> str:
    """
    构建图片访问 URL

    Args:
        filename: 文件名
        subfolder: 子文件夹
        img_type: 图片类型

    Returns:
        图片 URL
    """
    base_url = settings.COMFYUI_BASE_URL

    params = []
    params.append(f"filename={filename}")
    if subfolder:
        params.append(f"subfolder={subfolder}")
    params.append(f"type={img_type}")

    return f"{base_url}/view?{'&'.join(params)}"


def get_image_extension(filename: str) -> str:
    """
    获取图片文件扩展名

    Args:
        filename: 文件名

    Returns:
        扩展名（包含点号）
    """
    return Path(filename).suffix.lower()


def get_mime_type(filename: str) -> str:
    """
    根据文件名获取 MIME 类型

    Args:
        filename: 文件名

    Returns:
        MIME 类型
    """
    ext = get_image_extension(filename)

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    return mime_types.get(ext, "application/octet-stream")


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的文件大小字符串
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 保留文件扩展名
    name = Path(filename).stem
    ext = Path(filename).suffix

    # 移除不安全字符
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in unsafe_chars:
        name = name.replace(char, '_')

    return f"{name}{ext}"
