"""
WebSocket 领域模块

提供 WebSocket 实时通信功能
"""

from src.websocket.router import router
from src.websocket.schemas import (
    WebSocketMessage,
    WebSocketStatusMessage,
    WebSocketProgressMessage,
    WebSocketExecutingMessage,
    WebSocketExecutedMessage,
    WebSocketErrorMessage,
    WebSocketResultMessage,
    WebSocketSubmitRequest,
)
from src.websocket.service import (
    connect_to_comfyui_websocket,
    wait_for_workflow_completion,
    WebSocketConnectionManager,
    connection_manager,
)

__all__ = [
    "router",
    "WebSocketMessage",
    "WebSocketStatusMessage",
    "WebSocketProgressMessage",
    "WebSocketExecutingMessage",
    "WebSocketExecutedMessage",
    "WebSocketErrorMessage",
    "WebSocketResultMessage",
    "WebSocketSubmitRequest",
    "connect_to_comfyui_websocket",
    "wait_for_workflow_completion",
    "WebSocketConnectionManager",
    "connection_manager",
]
