"""
WebSocket 路由

提供实时通信功能，用于监听 ComfyUI 工作流执行进度
"""

import asyncio
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.internal.comfyui import comfyui_client


router = APIRouter()


class ConnectionManager:
    """
    WebSocket 连接管理器

    管理所有活跃的 WebSocket 连接，支持向特定客户端发送消息
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """
        接受新的 WebSocket 连接

        Args:
            client_id: 客户端唯一标识
            websocket: WebSocket 实例
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        """
        断开连接

        Args:
            client_id: 客户端唯一标识
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send(self, client_id: str, message_type: str, data: dict) -> None:
        """
        向指定客户端发送消息

        Args:
            client_id: 客户端唯一标识
            message_type: 消息类型
            data: 消息数据
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": message_type,
                "data": data
            })

    async def broadcast(self, message_type: str, data: dict) -> None:
        """
        向所有连接的客户端广播消息

        Args:
            message_type: 消息类型
            data: 消息数据
        """
        for connection in self.active_connections.values():
            await connection.send_json({
                "type": message_type,
                "data": data
            })


manager = ConnectionManager()


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket 端点

    支持的消息类型:
    - submit: 提交工作流
    - ping: 心跳检测

    Args:
        websocket: WebSocket 实例
        client_id: 客户端唯一标识
    """
    await manager.connect(client_id, websocket)
    await manager.send(client_id, "connected", {
        "message": "WebSocket 连接已建立",
        "client_id": client_id
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "submit":
                # 提交工作流
                workflow = data.get("data", {}).get("workflow")
                if workflow:
                    try:
                        prompt_id = await comfyui_client.submit_prompt(workflow, client_id)
                        await manager.send(client_id, "submit_success", {
                            "prompt_id": prompt_id,
                            "message": "工作流已提交"
                        })
                    except Exception as e:
                        await manager.send(client_id, "submit_error", {
                            "message": f"提交失败: {str(e)}"
                        })

            elif msg_type == "ping":
                # 心跳响应
                await manager.send(client_id, "pong", {
                    "timestamp": asyncio.get_event_loop().time()
                })

            else:
                await manager.send(client_id, "error", {
                    "message": f"未知消息类型: {msg_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        manager.disconnect(client_id)
        raise
