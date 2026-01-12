"""
图片领域常量

定义图片相关的常量
"""

from enum import Enum


class ComfyUIAPIPath(str, Enum):
    """ComfyUI API 路径枚举"""

    VIEW = "/view"
    UPLOAD_IMAGE = "/upload/image"
    MODELS = "/models"


class ImageType(str, Enum):
    """图片类型枚举"""

    OUTPUT = "output"
    INPUT = "input"


class AllowedImageExtension(str, Enum):
    """允许的图片扩展名"""

    PNG = ".png"
    JPG = ".jpg"
    JPEG = ".jpeg"
    WEBP = ".webp"
    GIF = ".gif"


# 允许的图片扩展名列表
ALLOWED_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
]

# 最大文件大小（字节）- 默认 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024
