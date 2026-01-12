"""
自定义异常模块

全局异常基类定义
"""

from typing import Optional, Any


class ComfyUIException(Exception):
    """ComfyUI 基础异常类"""

    def __init__(
        self,
        message: str,
        detail: Optional[Any] = None,
        code: Optional[str] = None
    ):
        self.message = message
        self.detail = detail
        self.code = code
        super().__init__(self.message)


class ComfyUIConnectionError(ComfyUIException):
    """ComfyUI 连接错误"""

    def __init__(self, message: str = "无法连接到 ComfyUI 服务"):
        super().__init__(message, code="CONNECTION_ERROR")


class WorkflowValidationError(ComfyUIException):
    """工作流验证错误"""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, detail=detail, code="WORKFLOW_VALIDATION_ERROR")


class WorkflowExecutionError(ComfyUIException):
    """工作流执行错误"""

    def __init__(self, message: str, prompt_id: Optional[str] = None):
        super().__init__(message, detail={"prompt_id": prompt_id}, code="WORKFLOW_EXECUTION_ERROR")


class QueueOperationError(ComfyUIException):
    """队列操作错误"""

    def __init__(self, message: str):
        super().__init__(message, code="QUEUE_OPERATION_ERROR")


class FileOperationError(ComfyUIException):
    """文件操作错误"""

    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message, detail={"file_path": file_path}, code="FILE_OPERATION_ERROR")


class ImageNotFoundError(ComfyUIException):
    """图片未找到错误"""

    def __init__(self, filename: str):
        super().__init__(
            f"图片未找到: {filename}",
            detail={"filename": filename},
            code="IMAGE_NOT_FOUND"
        )


class TaskTimeoutError(ComfyUIException):
    """任务超时错误"""

    def __init__(self, prompt_id: str, timeout: int):
        super().__init__(
            f"任务执行超时: {prompt_id}",
            detail={"prompt_id": prompt_id, "timeout": timeout},
            code="TASK_TIMEOUT"
        )


class WebSocketError(ComfyUIException):
    """WebSocket 错误"""

    def __init__(self, message: str, client_id: Optional[str] = None):
        super().__init__(
            message,
            detail={"client_id": client_id},
            code="WEBSOCKET_ERROR"
        )
