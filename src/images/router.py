"""
图片领域路由

图片 API 路由定义
"""

from typing import Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from src.images.schemas import ImageUploadResponse, ImageDownloadRequest
from src.images.service import (
    upload_image_to_comfyui,
    download_image_from_comfyui,
    save_upload_file_local,
    get_image_url,
)
from src.config import settings
from src.exceptions import FileOperationError, ComfyUIConnectionError


# 创建路由器
router = APIRouter(prefix="/images", tags=["images"])


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    summary="上传图片",
    description="上传图片到 ComfyUI input 目录",
)
async def upload_image_endpoint(
    file: UploadFile = File(..., description="图片文件"),
    overwrite: bool = Form(True, description="是否覆盖同名文件"),
) -> ImageUploadResponse:
    """
    上传图片
    """
    try:
        # 读取文件内容
        file_content = await file.read()

        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": "只支持图片文件"
                }
            )

        # 保存到本地 input 目录
        local_filename = await save_upload_file_local(file_content, file.filename)

        # 上传到 ComfyUI
        comfyui_filename = await upload_image_to_comfyui(
            str(settings.INPUT_DIR / local_filename),
            overwrite
        )

        return ImageUploadResponse(
            filename=file.filename,
            name=comfyui_filename,
            subfolder="",
            type="input"
        )

    except FileOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": e.code,
                "message": e.message,
                "detail": e.detail
            }
        )

    except ComfyUIConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": e.code,
                "message": e.message
            }
        )


@router.get(
    "/download",
    summary="下载图片",
    description="从 ComfyUI 下载生成的图片",
)
async def download_image_endpoint(
    filename: str,
    subfolder: str = "",
    img_type: str = "output",
) -> StreamingResponse:
    """
    下载图片
    """
    request = ImageDownloadRequest(
        filename=filename,
        subfolder=subfolder,
        type=img_type
    )

    try:
        # 下载图片数据
        image_data = await download_image_from_comfyui(
            request.filename,
            request.subfolder,
            request.type
        )

        return StreamingResponse(
            iter([image_data]),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={request.filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "IMAGE_NOT_FOUND",
                "message": f"图片不存在: {request.filename}",
                "detail": str(e)
            }
        )


@router.get(
    "/url",
    summary="获取图片 URL",
    description="获取图片的访问 URL",
)
async def get_image_url_endpoint(
    filename: str,
    subfolder: str = "",
    img_type: str = "output",
) -> Dict[str, str]:
    """
    获取图片 URL
    """
    request = ImageDownloadRequest(
        filename=filename,
        subfolder=subfolder,
        type=img_type
    )

    try:
        url = await get_image_url(
            request.filename,
            request.subfolder,
            request.type
        )

        return {
            "url": url,
            "filename": request.filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"获取图片 URL 失败: {str(e)}"
            }
        )
