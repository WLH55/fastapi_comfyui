"""
队列领域数据模型

定义队列请求和响应的数据结构
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueueItem(BaseModel):
    """
    队列项模型

    Attributes:
        prompt_id: 任务 ID
        number: 队列编号
        timestamp: 时间戳
    """

    prompt_id: str = Field(..., description="任务 ID")
    number: int = Field(..., description="队列编号")
    timestamp: int = Field(..., description="提交时间戳")


class QueueStatusResponse(BaseModel):
    """
    队列状态响应模型

    Attributes:
        queue_running: 正在运行的任务列表
        queue_pending: 等待中的任务列表
        running_count: 运行中任务数量
        pending_count: 等待中任务数量
    """

    queue_running: List[QueueItem] = Field(
        default_factory=list, description="正在运行的任务列表"
    )
    queue_pending: List[QueueItem] = Field(
        default_factory=list, description="等待中的任务列表"
    )
    running_count: int = Field(default=0, description="运行中任务数量")
    pending_count: int = Field(default=0, description="等待中任务数量")


class QueueClearRequest(BaseModel):
    """
    队列清空请求模型

    Attributes:
        clear: 是否清空队列
    """

    clear: bool = Field(..., description="是否清空队列")
