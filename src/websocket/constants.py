"""
WebSocket 领域常量

定义 WebSocket 相关的常量
"""

from enum import Enum


class ComfyUIAPIPath(str, Enum):
    """ComfyUI API 路径枚举"""

    WS = "/ws"


class WebSocketMessageType(str, Enum):
    """WebSocket 消息类型枚举"""

    # 状态消息
    STATUS = "status"

    # 执行中消息
    EXECUTING = "executing"

    # 进度消息
    PROGRESS = "progress"

    # 执行完成消息
    EXECUTED = "executed"

    # 错误消息
    EXECUTION_ERROR = "execution_error"

    # 系统消息（自定义）
    SYSTEM = "system"
    RESULT = "result"
