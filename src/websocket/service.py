"""
WebSocket 领域服务

WebSocket 业务逻辑层
"""

import asyncio
import json
from typing import Dict, Any, Optional, Callable, Awaitable
from fastapi import WebSocket
from websockets.client import connect as ws_connect

from src.config import settings
from src.exceptions import WebSocketError, ComfyUIConnectionError
from src.websocket.constants import WebSocketMessageType
from src.services import send_websocket_message


async def connect_to_comfyui_websocket(
    client_id: str,
    message_handler: Callable[[Dict[str, Any]], Awaitable[None]],
    error_handler: Optional[Callable[[Exception], Awaitable[None]]] = None
) -> None:
    """
    连接到 ComfyUI WebSocket 并处理消息

    Args:
        client_id: 客户端 ID
        message_handler: 消息处理函数
        error_handler: 错误处理函数

    Raises:
        WebSocketError: 连接失败时
    """
    uri = f"ws://{settings.COMFYUI_HOST}:{settings.COMFYUI_PORT}/ws?clientId={client_id}"

    try:
        async with ws_connect(uri) as websocket:
            while True:
                try:
                    message_str = await websocket.recv()
                    message = json.loads(message_str)

                    await message_handler(message)

                except Exception as e:
                    if error_handler:
                        await error_handler(e)
                    else:
                        raise

    except Exception as e:
        raise WebSocketError(f"WebSocket 连接失败: {str(e)}", client_id)


async def wait_for_workflow_completion(
    client_id: str,
    prompt_id: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    等待工作流完成并通过 WebSocket 接收进度

    Args:
        client_id: 客户端 ID
        prompt_id: 任务 ID
        progress_callback: 进度回调函数
        timeout: 超时时间（秒）

    Returns:
        最终结果字典

    Raises:
        TaskTimeoutError: 任务超时时
    """
    from src.exceptions import TaskTimeoutError

    result = {
        "prompt_id": prompt_id,
        "success": False,
        "outputs": {},
        "error": None
    }

    async def message_handler(message: Dict[str, Any]) -> None:
        """处理 ComfyUI WebSocket 消息"""
        msg_type = message.get("type")
        msg_data = message.get("data", {})

        if msg_type == WebSocketMessageType.STATUS:
            # 状态消息
            if progress_callback:
                await progress_callback({
                    "type": "status",
                    "data": msg_data
                })

        elif msg_type == WebSocketMessageType.EXECUTING:
            # 执行中消息
            node_id = msg_data.get("node")
            if node_id is None:
                # 执行完成
                result["success"] = True
            else:
                if progress_callback:
                    await progress_callback({
                        "type": "executing",
                        "node": node_id
                    })

        elif msg_type == WebSocketMessageType.PROGRESS:
            # 进度消息
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "value": msg_data.get("value", 0),
                    "max": msg_data.get("max", 0)
                })

        elif msg_type == WebSocketMessageType.EXECUTED:
            # 节点执行完成
            if progress_callback:
                await progress_callback({
                    "type": "executed",
                    "node": msg_data.get("node"),
                    "output": msg_data.get("output", {})
                })

        elif msg_type == WebSocketMessageType.EXECUTION_ERROR:
            # 执行错误
            result["success"] = False
            result["error"] = msg_data.get("exception_message", "Unknown error")

    async def error_handler(error: Exception) -> None:
        """处理错误"""
        result["success"] = False
        result["error"] = str(error)

    try:
        # 连接 WebSocket 并等待完成
        await asyncio.wait_for(
            connect_to_comfyui_websocket(client_id, message_handler, error_handler),
            timeout=timeout
        )

    except asyncio.TimeoutError:
        raise TaskTimeoutError(prompt_id, timeout)

    return result


class WebSocketConnectionManager:
    """
    WebSocket 连接管理器

    管理客户端 WebSocket 连接，支持消息广播和点对点通信
    """

    def __init__(self):
        """初始化连接管理器"""
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_prompts: Dict[str, Optional[str]] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """
        接受新的 WebSocket 连接

        Args:
            client_id: 客户端 ID
            websocket: WebSocket 连接
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_prompts[client_id] = None

    def disconnect(self, client_id: str) -> None:
        """
        断开 WebSocket 连接

        Args:
            client_id: 客户端 ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_prompts:
            del self.client_prompts[client_id]

    def set_current_prompt(self, client_id: str, prompt_id: str) -> None:
        """
        设置客户端当前执行的任务

        Args:
            client_id: 客户端 ID
            prompt_id: 任务 ID
        """
        self.client_prompts[client_id] = prompt_id

    def get_current_prompt(self, client_id: str) -> Optional[str]:
        """
        获取客户端当前执行的任务

        Args:
            client_id: 客户端 ID

        Returns:
            任务 ID
        """
        return self.client_prompts.get(client_id)

    async def send_to_client(
        self,
        client_id: str,
        message_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        发送消息给指定客户端

        Args:
            client_id: 客户端 ID
            message_type: 消息类型
            data: 消息数据

        Returns:
            是否发送成功
        """
        if client_id not in self.active_connections:
            return False

        try:
            await send_websocket_message(
                self.active_connections[client_id],
                message_type,
                data
            )
            return True

        except Exception:
            return False

    async def broadcast(self, message_type: str, data: Dict[str, Any]) -> None:
        """
        广播消息给所有连接的客户端

        Args:
            message_type: 消息类型
            data: 消息数据
        """
        for client_id in list(self.active_connections.keys()):
            await self.send_to_client(client_id, message_type, data)

    def get_connected_clients(self) -> list:
        """
        获取所有连接的客户端 ID

        Returns:
            客户端 ID 列表
        """
        return list(self.active_connections.keys())


# 全局连接管理器实例
connection_manager = WebSocketConnectionManager()
