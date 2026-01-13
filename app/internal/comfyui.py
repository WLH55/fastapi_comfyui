"""
ComfyUI 客户端模块

负责与 ComfyUI 服务进行通信
"""

import httpx
import json
from typing import Dict, Any, Optional, List

from app.config import settings
from app.exceptions import ComfyUIConnectionError, ImageNotFoundError


class ComfyUIClient:
    """ComfyUI HTTP 客户端"""

    def __init__(self):
        self.base_url = settings.COMFYUI_BASE_URL
        self.timeout = settings.COMFYUI_TIMEOUT

    async def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送 POST 请求"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}{path}", json=data)
                response.raise_for_status()

                # 处理空响应
                if not response.content:
                    return {}

                return response.json()

        except httpx.ConnectError as e:
            raise ComfyUIConnectionError(f"连接失败: {str(e)}")
        except httpx.TimeoutException as e:
            raise ComfyUIConnectionError(f"请求超时: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ComfyUIConnectionError(
                f"HTTP 错误: {e.response.status_code}"
            )
        except json.JSONDecodeError as e:
            raise ComfyUIConnectionError(
                f"ComfyUI 返回无效 JSON: {str(e)}"
            )

    async def _get(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送 GET 请求"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}{path}", params=params)
                response.raise_for_status()

                # 处理空响应
                if not response.content:
                    return {}

                return response.json()

        except httpx.ConnectError as e:
            raise ComfyUIConnectionError(f"连接失败: {str(e)}")
        except httpx.TimeoutException as e:
            raise ComfyUIConnectionError(f"请求超时: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ComfyUIConnectionError(
                f"HTTP 错误: {e.response.status_code}"
            )
        except json.JSONDecodeError as e:
            raise ComfyUIConnectionError(
                f"ComfyUI 返回无效 JSON: {str(e)}"
            )

    async def submit_prompt(
            self,
            workflow: Dict[str, Any],
            client_id: Optional[str] = None
    ) -> str:
        """
        提交工作流

        Args:
            workflow: workflow JSON
            client_id: 客户端 ID

        Returns:
            prompt_id
        """
        payload = {"prompt": workflow}
        if client_id:
            payload["client_id"] = client_id

        response = await self._post("/prompt", payload)

        if "node_errors" in response and response["node_errors"]:
            raise ComfyUIConnectionError(
                f"工作流验证失败: {response['node_errors']}"
            )

        return response["prompt_id"]

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """获取工作流历史"""
        response = await self._get(f"/history/{prompt_id}")
        return response.get(prompt_id, {})

    async def interrupt(self, prompt_id: Optional[str] = None) -> Dict[str, Any]:
        """中断工作流执行"""
        payload = {}
        if prompt_id:
            payload["prompt_id"] = prompt_id
        return await self._post("/interrupt", payload)

    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return await self._get("/queue")

    async def clear_queue(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清空队列或删除指定项

        Args:
            request_data: 请求数据，支持:
                - {"clear": true} 清空整个队列
                - {"delete": ["id1", "id2"]} 删除指定项

        Returns:
            ComfyUI 响应（通常为空）
        """
        return await self._post("/queue", request_data)

    async def upload_image(
            self,
            image_data: bytes,
            filename: str,
            overwrite: bool = True
    ) -> Dict[str, Any]:
        """上传图片"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"image": (filename, image_data, "image/png")}
                data = {"overwrite": "true" if overwrite else "false"}
                response = await client.post(
                    f"{self.base_url}/upload/image",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            raise ComfyUIConnectionError(f"上传失败: {str(e)}")

    async def download_image(
            self,
            filename: str,
            subfolder: str = "",
            img_type: str = "output"
    ) -> bytes:
        """下载图片"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "filename": filename,
                    "subfolder": subfolder,
                    "type": img_type
                }
                response = await client.get(f"{self.base_url}/view", params=params)
                response.raise_for_status()
                return response.content

        except Exception:
            raise ImageNotFoundError(filename)


# 全局客户端实例
comfyui_client = ComfyUIClient()
