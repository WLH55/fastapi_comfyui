"""
图片领域异常

定义图片模块的特定异常
"""

from src.exceptions import ComfyUIException


class InvalidImageFormatError(ComfyUIException):
    """无效图片格式错误"""

    def __init__(self, filename: str, allowed_formats: list):
        super().__init__(
            f"无效的图片格式: {filename}",
            detail={
                "filename": filename,
                "allowed_formats": allowed_formats
            },
            code="INVALID_IMAGE_FORMAT"
        )


class ImageUploadError(ComfyUIException):
    """图片上传错误"""

    def __init__(self, message: str, filename: str = None):
        super().__init__(
            message,
            detail={"filename": filename} if filename else None,
            code="IMAGE_UPLOAD_ERROR"
        )


class ImageDownloadError(ComfyUIException):
    """图片下载错误"""

    def __init__(self, message: str, filename: str = None):
        super().__init__(
            message,
            detail={"filename": filename} if filename else None,
            code="IMAGE_DOWNLOAD_ERROR"
        )


class FileSizeExceededError(ComfyUIException):
    """文件大小超限错误"""

    def __init__(self, filename: str, size: int, max_size: int):
        super().__init__(
            f"文件大小超限: {filename} ({size} > {max_size})",
            detail={
                "filename": filename,
                "size": size,
                "max_size": max_size
            },
            code="FILE_SIZE_EXCEEDED"
        )
