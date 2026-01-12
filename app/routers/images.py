"""
图片路由
"""
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form

from app.internal.comfyui import comfyui_client
from app.config import settings
from app.internal.utils import save_file
from app.exceptions import ComfyUIConnectionError
from app.schemas import ApiResponse, ResponseCode


router = APIRouter(prefix="/images", tags=["images"])


@router.post("/upload", summary="上传图片", response_model=ApiResponse)
async def upload_image(
    file: UploadFile = File(...),
    overwrite: bool = Form(True)
) -> ApiResponse:
    """
    上传图片到 ComfyUI input 目录

    参数:
    - file: 图片文件
    - overwrite: 是否覆盖同名文件 (默认: True)
    """
    try:
        content = await file.read()

        if not file.content_type or not file.content_type.startswith("image/"):
            return ApiResponse.error(
                code=ResponseCode.BAD_REQUEST,
                message="只支持图片文件"
            )

        # 保存到本地
        save_file(content, file.filename, settings.INPUT_DIR)

        # 上传到 ComfyUI
        result = await comfyui_client.upload_image(content, file.filename, overwrite)

        return ApiResponse.success(
            data={
                "filename": file.filename,
                "name": result.get("name", file.filename)
            },
            message="上传成功"
        )

    except ComfyUIConnectionError as e:
        return ApiResponse.error(
            code=e.code,
            message=e.message
        )
    except Exception as e:
        return ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"上传失败: {str(e)}"
        )


@router.get("/url", summary="获取图片 URL", response_model=ApiResponse)
async def get_image_url(
    filename: str,
    subfolder: str = "",
    img_type: str = "output"
) -> ApiResponse:
    """
    获取图片访问 URL

    返回可直接访问图片的 URL 地址
    """
    try:
        base_url = settings.COMFYUI_BASE_URL
        url = f"{base_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
        return ApiResponse.success(
            data={"url": url, "filename": filename},
            message="获取图片 URL 成功"
        )
    except Exception as e:
        return ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"获取 URL 失败: {str(e)}"
        )
