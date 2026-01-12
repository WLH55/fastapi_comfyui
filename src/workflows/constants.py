"""
工作流领域常量

定义工作流相关的常量
"""

from enum import Enum


class ComfyUIAPIPath(str, Enum):
    """ComfyUI API 路径枚举"""

    # 工作流相关
    PROMPT = "/prompt"
    OBJECT_INFO = "/object_info"
    HISTORY = "/history"
    INTERRUPT = "/interrupt"


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
