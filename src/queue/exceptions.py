"""
队列领域异常

定义队列模块的特定异常
"""

from src.exceptions import ComfyUIException


class QueueNotFoundError(ComfyUIException):
    """队列未找到错误"""

    def __init__(self):
        super().__init__(
            "队列未找到或不可用",
            code="QUEUE_NOT_FOUND"
        )


class TaskNotInQueueError(ComfyUIException):
    """任务不在队列中错误"""

    def __init__(self, prompt_id: str):
        super().__init__(
            f"任务不在队列中: {prompt_id}",
            detail={"prompt_id": prompt_id},
            code="TASK_NOT_IN_QUEUE"
        )


class QueueClearError(ComfyUIException):
    """队列清空错误"""

    def __init__(self, message: str):
        super().__init__(
            message,
            code="QUEUE_CLEAR_ERROR"
        )
