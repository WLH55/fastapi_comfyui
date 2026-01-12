"""
WebSocket 领域异常

定义 WebSocket 模块的特定异常
"""

from src.exceptions import ComfyUIException


class WebSocketConnectionError(ComfyUIException):
    """WebSocket 连接错误"""

    def __init__(self, message: str, client_id: str = None):
        super().__init__(
            message,
            detail={"client_id": client_id} if client_id else None,
            code="WS_CONNECTION_ERROR"
        )


class WebSocketMessageError(ComfyUIException):
    """WebSocket 消息错误"""

    def __init__(self, message: str, message_type: str = None):
        super().__init__(
            message,
            detail={"message_type": message_type} if message_type else None,
            code="WS_MESSAGE_ERROR"
        )


class WebSocketClientNotFoundError(ComfyUIException):
    """WebSocket 客户端未找到错误"""

    def __init__(self, client_id: str):
        super().__init__(
            f"WebSocket 客户端未找到: {client_id}",
            detail={"client_id": client_id},
            code="WS_CLIENT_NOT_FOUND"
        )


class WebSocketTimeoutError(ComfyUIException):
    """WebSocket 超时错误"""

    def __init__(self, client_id: str, timeout: int):
        super().__init__(
            f"WebSocket 连接超时: {client_id} ({timeout}s)",
            detail={
                "client_id": client_id,
                "timeout": timeout
            },
            code="WS_TIMEOUT"
        )
