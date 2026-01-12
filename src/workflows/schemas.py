"""
工作流领域数据模型

定义工作流请求和响应的数据结构
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class WorkflowSubmitRequest(BaseModel):
    """
    工作流提交请求模型

    Attributes:
        workflow: 工作流 JSON（API 格式）
        client_id: 客户端标识（可选，用于 WebSocket）
    """

    workflow: Dict[str, Any] = Field(
        ..., description="工作流 JSON（API 格式）"
    )
    client_id: Optional[str] = Field(
        None, description="客户端标识，用于 WebSocket 推送"
    )


class WorkflowSubmitResponse(BaseModel):
    """
    工作流提交响应模型

    Attributes:
        prompt_id: 任务 ID
        number: 队列编号
        client_id: 客户端标识
    """

    prompt_id: str = Field(..., description="任务 ID")
    number: int = Field(..., description="队列编号")
    client_id: Optional[str] = Field(None, description="客户端标识")


class WorkflowInterruptRequest(BaseModel):
    """
    工作流中断请求模型

    Attributes:
        prompt_id: 任务 ID（可选，不传则中断所有）
    """

    prompt_id: Optional[str] = Field(
        None, description="任务 ID，不传则中断所有正在运行的任务"
    )


class NodeOutput(BaseModel):
    """
    节点输出模型

    Attributes:
        node_id: 节点 ID
        images: 输出图片列表
        videos: 输出视频列表
    """

    node_id: str
    images: list = Field(default_factory=list)
    videos: list = Field(default_factory=list)


class WorkflowHistoryResponse(BaseModel):
    """
    工作流历史响应模型

    Attributes:
        prompt_id: 任务 ID
        outputs: 输出结果
        status: 执行状态
    """

    prompt_id: str = Field(..., description="任务 ID")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="输出结果")
    status: str = Field(default="unknown", description="执行状态")
