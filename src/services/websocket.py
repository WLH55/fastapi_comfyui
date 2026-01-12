"""
WebSocket 处理服务

负责 WebSocket 连接管理和消息处理
"""

import json
from typing import Any, Dict, Callable, Optional
from fastapi import WebSocket, WebSocketDisconnect

from src.exceptions import WebSocketError


async def send_websocket_message(websocket: WebSocket, message_type: str, data: Dict[str, Any]) -> None:
    """
    发送 WebSocket 消息

    Args:
        websocket: WebSocket 连接
        message_type: 消息类型
        data: 消息数据

    Raises:
        WebSocketError: 发送失败时
    """
    try:
        message = {
            "type": message_type,
            "data": data
        }
        await websocket.send_json(message)

    except WebSocketDisconnect:
        raise WebSocketError("WebSocket 连接已断开")

    except Exception as e:
        raise WebSocketError(f"发送消息失败: {str(e)}")


async def receive_websocket_message(websocket: WebSocket) -> Dict[str, Any]:
    """
    接收 WebSocket 消息

    Args:
        websocket: WebSocket 连接

    Returns:
        消息数据

    Raises:
        WebSocketError: 接收失败时
    """
    try:
        data = await websocket.receive_json()
        return data

    except WebSocketDisconnect:
        raise WebSocketError("WebSocket 连接已断开")

    except json.JSONDecodeError:
        raise WebSocketError("无效的 JSON 消息")

    except Exception as e:
        raise WebSocketError(f"接收消息失败: {str(e)}")


def validate_websocket_message(message: Dict[str, Any], required_fields: list) -> bool:
    """
    验证 WebSocket 消息格式

    Args:
        message: 消息数据
        required_fields: 必需字段列表

    Returns:
        是否有效
    """
    for field in required_fields:
        if field not in message:
            return False
    return True


async def websocket_broadcaster(
    websocket: WebSocket,
    message_handler: Callable[[Dict[str, Any]], None],
    disconnect_handler: Optional[Callable[[], None]] = None
) -> None:
    """
    WebSocket 消息广播处理器

    Args:
        websocket: WebSocket 连接
        message_handler: 消息处理函数
        disconnect_handler: 断开连接处理函数
    """
    try:
        while True:
            message = await websocket.receive_json()
            message_handler(message)

    except WebSocketDisconnect:
        if disconnect_handler:
            disconnect_handler()

    except Exception:
        if disconnect_handler:
            disconnect_handler()
        raise
