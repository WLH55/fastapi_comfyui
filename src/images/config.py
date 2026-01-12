"""
图片领域配置

定义图片模块的特定配置
"""

from pathlib import Path
from src.config import settings


class ImageConfig:
    """图片模块配置类"""

    # 图片上传超时时间（秒）
    UPLOAD_TIMEOUT: int = settings.COMFYUI_TIMEOUT

    # 图片下载超时时间（秒）
    DOWNLOAD_TIMEOUT: int = settings.COMFYUI_TIMEOUT

    # 输入目录
    INPUT_DIR: Path = settings.INPUT_DIR

    # 输出目录
    OUTPUT_DIR: Path = settings.OUTPUT_DIR

    # 是否覆盖同名文件
    OVERWRITE_DEFAULT: bool = True

    # 允许的 MIME 类型
    ALLOWED_MIME_TYPES = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/gif",
    ]


# 创建配置实例
image_config = ImageConfig()
