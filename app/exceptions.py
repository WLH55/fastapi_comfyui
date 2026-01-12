"""
自定义异常模块
"""

from typing import Optional


class ComfyUIException(Exception):
    """
    ComfyUI 基础异常类

    Attributes:
        message: 错误消息
        code: 错误码
    """

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ComfyUIConnectionError(ComfyUIException):
    """ComfyUI 连接错误"""
    code = "CONNECTION_ERROR"

    def __init__(self, message: str = "无法连接到 ComfyUI 服务"):
        super().__init__(message, code=self.code)


class WorkflowValidationError(ComfyUIException):
    """工作流验证错误"""
    code = "WORKFLOW_VALIDATION_ERROR"

    def __init__(self, message: str):
        super().__init__(message, code=self.code)


class QueueOperationError(ComfyUIException):
    """队列操作错误"""
    code = "QUEUE_OPERATION_ERROR"

    def __init__(self, message: str):
        super().__init__(message, code=self.code)


class FileOperationError(ComfyUIException):
    """文件操作错误"""
    code = "FILE_OPERATION_ERROR"

    def __init__(self, message: str):
        super().__init__(message, code=self.code)


class ImageNotFoundError(ComfyUIException):
    """图片未找到错误"""
    code = "IMAGE_NOT_FOUND"

    def __init__(self, filename: str):
        super().__init__(f"图片未找到: {filename}", code=self.code)


class WebSocketError(ComfyUIException):
    """WebSocket 错误"""
    code = "WEBSOCKET_ERROR"

    def __init__(self, message: str):
        super().__init__(message, code=self.code)


class TemplateNotFoundError(ComfyUIException):
    """模板未找到错误"""
    code = "TEMPLATE_NOT_FOUND"

    def __init__(self, template_id: str):
        super().__init__(f"模板未找到: {template_id}", code=self.code)
