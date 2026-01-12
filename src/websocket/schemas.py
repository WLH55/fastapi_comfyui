"""
WebSocket 领域数据模型

定义 WebSocket 消息的数据结构
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """
    WebSocket 消息基础模型

    Attributes:
        type: 消息类型
        data: 消息数据
    """

    type: str = Field(..., description="消息类型")
    data: dict = Field(default_factory=dict, description="消息数据")


class WebSocketStatusMessage(WebSocketMessage):
    """
    WebSocket 状态消息

    Attributes:
        data.status_data: 状态数据
    """

    type: str = "status"


class WebSocketProgressMessage(WebSocketMessage):
    """
    WebSocket 进度消息

    Attributes:
        data.value: 当前进度值
        data.max: 最大进度值
    """

    type: str = "progress"


class WebSocketExecutingMessage(WebSocketMessage):
    """
    WebSocket 执行中消息

    Attributes:
        data.node: 节点 ID
    """

    type: str = "executing"


class WebSocketExecutedMessage(WebSocketMessage):
    """
    WebSocket 执行完成消息

    Attributes:
        data.node: 节点 ID
        data.output: 输出结果
    """

    type: str = "executed"


class WebSocketErrorMessage(WebSocketMessage):
    """
    WebSocket 错误消息

    Attributes:
        data.error_type: 错误类型
        data.error_message: 错误信息
    """

    type: str = "execution_error"


class WebSocketResultMessage(WebSocketMessage):
    """
    WebSocket 结果消息（工作流全部完成）

    Attributes:
        data.prompt_id: 任务 ID
        data.success: 是否成功
        data.outputs: 输出结果
        data.error: 错误信息（如果有）
    """

    type: str = "result"
    data: dict = Field(
        default_factory=dict,
        description="包含 prompt_id, success, outputs, error 等字段"
    )


class WebSocketSubmitRequest(BaseModel):
    """
    通过 WebSocket 提交工作流的请求

    Attributes:
        workflow: 工作流 JSON
    """

    workflow: dict = Field(..., description="工作流 JSON（API 格式）")
