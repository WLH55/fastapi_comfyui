"""
WebSocket 领域依赖项

定义 WebSocket 路由的依赖项
"""

from typing import Optional
from fastapi import WebSocket, status
from fastapi.exceptions import WebSocketDisconnect as FastAPIWebSocketDisconnect

from src.websocket.exceptions import WebSocketConnectionError


async def verify_websocket_connection(websocket: WebSocket, client_id: str) -> bool:
    """
    验证 WebSocket 连接

    Args:
        websocket: WebSocket 连接
        client_id: 客户端 ID

    Returns:
        是否验证成功

    Raises:
        WebSocketConnectionError: 验证失败时
    """
    if not client_id:
        raise WebSocketConnectionError("客户端 ID 不能为空")

    try:
        await websocket.accept()
        return True

    except Exception as e:
        raise WebSocketConnectionError(f"WebSocket 连接接受失败: {str(e)}", client_id)


async def handle_websocket_disconnect(
    websocket: WebSocket,
    client_id: str
) -> None:
    """
    处理 WebSocket 断开连接

    Args:
        websocket: WebSocket 连接
        client_id: 客户端 ID
    """
    try:
        await websocket.close()

    except Exception:
        pass


def parse_websocket_message_type(message: dict) -> str:
    """
    解析 WebSocket 消息类型

    Args:
        message: 消息数据

    Returns:
        消息类型
    """
    return message.get("type", "unknown")


def validate_websocket_submit_data(data: dict) -> bool:
    """
    验证 WebSocket 提交数据

    Args:
        data: 提交数据

    Returns:
        是否有效
    """
    return "workflow" in data and isinstance(data["workflow"], dict)
