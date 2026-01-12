"""
图片领域服务

图片业务逻辑层
"""

from typing import Optional
from pathlib import Path

from src.config import settings
from src.exceptions import ComfyUIConnectionError, ImageNotFoundError, FileOperationError
from src.images.constants import ComfyUIAPIPath
from src.services import (
    get_binary,
    post_multipart,
    save_upload_file,
    read_file,
    generate_unique_filename,
)


async def upload_image_to_comfyui(
    image_path: str,
    overwrite: bool = True
) -> str:
    """
    上传图片到 ComfyUI

    Args:
        image_path: 本地图片路径
        overwrite: 是否覆盖同名文件

    Returns:
        上传后的文件名

    Raises:
        FileOperationError: 文件操作失败时
        ComfyUIConnectionError: 连接失败时
    """
    # 读取图片文件
    image_content = read_file(Path(image_path))
    filename = Path(image_path).name

    # 构建 multipart 请求
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.UPLOAD_IMAGE}"

    files = {
        "image": (filename, image_content, "image/png")
    }

    data = {
        "overwrite": "true" if overwrite else "false"
    }

    # 发送请求
    response = await post_multipart(url, files, data)

    return response.get("name", filename)


async def download_image_from_comfyui(
    filename: str,
    subfolder: str = "",
    img_type: str = "output"
) -> bytes:
    """
    从 ComfyUI 下载图片

    Args:
        filename: 文件名
        subfolder: 子文件夹
        img_type: 图片类型（output/input）

    Returns:
        图片二进制数据

    Raises:
        ComfyUIConnectionError: 连接失败时
        ImageNotFoundError: 图片不存在时
    """
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.VIEW}"

    params = {
        "filename": filename,
        "subfolder": subfolder,
        "type": img_type
    }

    try:
        return await get_binary(url, params)

    except Exception as e:
        raise ImageNotFoundError(filename)


async def save_upload_file_local(
    file_content: bytes,
    filename: str
) -> str:
    """
    保存上传的文件到本地 input 目录

    Args:
        file_content: 文件二进制内容
        filename: 文件名

    Returns:
        保存后的文件名

    Raises:
        FileOperationError: 文件操作失败时
    """
    file_path = save_upload_file(file_content, filename, settings.INPUT_DIR)
    return Path(file_path).name


async def download_and_save_image(
    filename: str,
    subfolder: str = "",
    img_type: str = "output",
    output_dir: Optional[Path] = None
) -> str:
    """
    下载图片并保存到本地

    Args:
        filename: 文件名
        subfolder: 子文件夹
        img_type: 图片类型
        output_dir: 输出目录（默认为 OUTPUT_DIR）

    Returns:
        保存后的文件路径

    Raises:
        ComfyUIConnectionError: 连接失败时
        FileOperationError: 文件操作失败时
    """
    if output_dir is None:
        output_dir = settings.OUTPUT_DIR

    # 下载图片
    image_content = await download_image_from_comfyui(filename, subfolder, img_type)

    # 生成唯一文件名
    unique_filename = generate_unique_filename(filename)
    save_path = output_dir / unique_filename

    # 保存文件
    save_upload_file(image_content, unique_filename, output_dir)

    return str(save_path)


async def get_image_url(
    filename: str,
    subfolder: str = "",
    img_type: str = "output"
) -> str:
    """
    获取图片的访问 URL

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

    return f"{base_url}{ComfyUIAPIPath.VIEW}?{'&'.join(params)}"
