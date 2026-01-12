"""
队列领域常量

定义队列相关的常量
"""

from enum import Enum


class ComfyUIAPIPath(str, Enum):
    """ComfyUI API 路径枚举"""

    QUEUE = "/queue"


class QueueStatus(str, Enum):
    """队列状态枚举"""

    RUNNING = "running"
    PENDING = "pending"
