"""
图片路由
"""
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, Response, HTTPException

from app.internal.comfyui import comfyui_client
from app.config import settings
from app.internal.utils import save_file
from app.schemas import ApiResponse

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
    content = await file.read()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")

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


@router.get("/download", summary="下载图片")
async def download_image(
        filename: str,
        subfolder: str = "",
        img_type: str = "output"
) -> Response:
    """
    下载图片

    直接返回图片二进制内容

    参数:
    - filename: 图片文件名
    - subfolder: 子文件夹 (默认: 空)
    - img_type: 图片类型 output/input (默认: output)
    """

    # 从 ComfyUI 下载图片
    content = await comfyui_client.download_image(filename, subfolder, img_type)

    # 根据文件扩展名推断 Content-Type
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_type_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
    }
    media_type = content_type_map.get(ext, "image/png")

    return Response(content=content, media_type=media_type)

