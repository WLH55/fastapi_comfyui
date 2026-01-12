"""
文件操作服务

负责文件的读取、写入、上传等操作
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from src.config import settings
from src.exceptions import FileOperationError


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一的文件名

    Args:
        original_filename: 原始文件名

    Returns:
        唯一的文件名（带 UUID 前缀）
    """
    ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}_{original_filename}"


def save_upload_file(
    file_content: bytes,
    filename: str,
    directory: Optional[Path] = None
) -> str:
    """
    保存上传的文件

    Args:
        file_content: 文件二进制内容
        filename: 文件名
        directory: 保存目录（默认为 INPUT_DIR）

    Returns:
        保存后的文件路径

    Raises:
        FileOperationError: 文件操作失败时
    """
    if directory is None:
        directory = settings.INPUT_DIR

    try:
        # 确保目录存在
        directory.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        unique_filename = generate_unique_filename(filename)
        file_path = directory / unique_filename

        # 写入文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    except IOError as e:
        raise FileOperationError(f"保存文件失败: {str(e)}", filename)


def read_file(file_path: Path) -> bytes:
    """
    读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        文件二进制内容

    Raises:
        FileOperationError: 文件操作失败时
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()

    except IOError as e:
        raise FileOperationError(f"读取文件失败: {str(e)}", str(file_path))


def delete_file(file_path: Path) -> bool:
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否删除成功
    """
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    except IOError:
        return False


def file_exists(file_path: Path) -> bool:
    """
    检查文件是否存在

    Args:
        file_path: 文件路径

    Returns:
        文件是否存在
    """
    return file_path.exists() and file_path.is_file()


def get_file_size(file_path: Path) -> int:
    """
    获取文件大小

    Args:
        file_path: 文件路径

    Returns:
        文件大小（字节）

    Raises:
        FileOperationError: 文件不存在时
    """
    if not file_exists(file_path):
        raise FileOperationError("文件不存在", str(file_path))

    return file_path.stat().st_size
