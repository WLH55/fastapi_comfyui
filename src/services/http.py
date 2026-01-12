"""
HTTP 通信服务

负责与 ComfyUI 服务进行 HTTP 通信
"""

import httpx
from typing import Any, Dict, Optional

from src.config import settings
from src.exceptions import ComfyUIConnectionError


async def post_json(url: str, data: Dict[str, Any], timeout: int = None) -> Dict[str, Any]:
    """
    发送 POST JSON 请求

    Args:
        url: 请求 URL
        data: 请求数据
        timeout: 超时时间（秒）

    Returns:
        响应 JSON 数据

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    if timeout is None:
        timeout = settings.COMFYUI_TIMEOUT

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError as e:
        raise ComfyUIConnectionError(f"连接 ComfyUI 失败: {str(e)}")

    except httpx.TimeoutException as e:
        raise ComfyUIConnectionError(f"请求超时: {str(e)}")

    except httpx.HTTPStatusError as e:
        raise ComfyUIConnectionError(
            f"HTTP 错误: {e.response.status_code} - {e.response.text}"
        )


async def get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = None) -> Dict[str, Any]:
    """
    发送 GET JSON 请求

    Args:
        url: 请求 URL
        params: 查询参数
        timeout: 超时时间（秒）

    Returns:
        响应 JSON 数据

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    if timeout is None:
        timeout = settings.COMFYUI_TIMEOUT

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError as e:
        raise ComfyUIConnectionError(f"连接 ComfyUI 失败: {str(e)}")

    except httpx.TimeoutException as e:
        raise ComfyUIConnectionError(f"请求超时: {str(e)}")

    except httpx.HTTPStatusError as e:
        raise ComfyUIConnectionError(
            f"HTTP 错误: {e.response.status_code} - {e.response.text}"
        )


async def get_binary(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = None) -> bytes:
    """
    发送 GET 请求获取二进制数据

    Args:
        url: 请求 URL
        params: 查询参数
        timeout: 超时时间（秒）

    Returns:
        响应二进制数据

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    if timeout is None:
        timeout = settings.COMFYUI_TIMEOUT

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.content

    except httpx.ConnectError as e:
        raise ComfyUIConnectionError(f"连接 ComfyUI 失败: {str(e)}")

    except httpx.TimeoutException as e:
        raise ComfyUIConnectionError(f"请求超时: {str(e)}")

    except httpx.HTTPStatusError as e:
        raise ComfyUIConnectionError(
            f"HTTP 错误: {e.response.status_code} - {e.response.text}"
        )


async def post_multipart(
    url: str,
    files: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None,
    timeout: int = None
) -> Dict[str, Any]:
    """
    发送 multipart/form-data 请求

    Args:
        url: 请求 URL
        files: 文件数据
        data: 表单数据
        timeout: 超时时间（秒）

    Returns:
        响应 JSON 数据

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    if timeout is None:
        timeout = settings.COMFYUI_TIMEOUT

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError as e:
        raise ComfyUIConnectionError(f"连接 ComfyUI 失败: {str(e)}")

    except httpx.TimeoutException as e:
        raise ComfyUIConnectionError(f"请求超时: {str(e)}")

    except httpx.HTTPStatusError as e:
        raise ComfyUIConnectionError(
            f"HTTP 错误: {e.response.status_code} - {e.response.text}"
        )
