"""
自定义异常模块

包含异常类定义和全局异常处理器
"""

from typing import Optional
from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import ApiResponse, ResponseCode


# ========== 异常类定义 ==========


class ComfyUIException(Exception):
    """
    ComfyUI 基础异常类

    Attributes:
        message: 错误消息
        code: 错误码
    """

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ComfyUIConnectionError(ComfyUIException):
    """ComfyUI 连接错误"""
    code = ResponseCode.ERROR_COMFYUI_CONNECTION

    def __init__(self, message: str = "无法连接到 ComfyUI 服务"):
        super().__init__(message, code=self.code)


class WorkflowValidationError(ComfyUIException):
    """工作流验证错误"""
    code = ResponseCode.ERROR_WORKFLOW_VALIDATION

    def __init__(self, message: str):
        super().__init__(message, code=self.code)


class QueueOperationError(ComfyUIException):
    """队列操作错误"""
    code = ResponseCode.ERROR_QUEUE_OPERATION

    def __init__(self, message: str):
        super().__init__(message, code=self.code)


class FileOperationError(ComfyUIException):
    """文件操作错误"""
    code = ResponseCode.ERROR_FILE_OPERATION

    def __init__(self, message: str):
        super().__init__(message, code=self.code)


class ImageNotFoundError(ComfyUIException):
    """图片未找到错误"""
    code = ResponseCode.ERROR_IMAGE_NOT_FOUND

    def __init__(self, filename: str):
        super().__init__(f"图片未找到: {filename}", code=self.code)




# ========== 异常处理器 ==========


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    处理 HTTP 异常

    Args:
        request: 请求对象
        exc: HTTP 异常

    Returns:
        统一格式的错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(
            code=exc.status_code,
            message=exc.detail,
            data=None
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求参数验证异常

    Args:
        request: 请求对象
        exc: 验证异常

    Returns:
        统一格式的错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ApiResponse.error(
            code=ResponseCode.VALIDATION_ERROR,
            message="请求参数验证失败",
            data=None
        ).model_dump()
    )


async def comfyui_exception_handler(request: Request, exc: ComfyUIException) -> JSONResponse:
    """
    处理 ComfyUI 业务异常

    Args:
        request: 请求对象
        exc: ComfyUI 异常

    Returns:
        统一格式的错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.error(
            code=getattr(exc, "code", ResponseCode.INTERNAL_ERROR),
            message=exc.message,
            data=None
        ).model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理所有未捕获的异常

    Args:
        request: 请求对象
        exc: 通用异常

    Returns:
        统一格式的错误响应
    """


    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message="服务器内部错误",
            data=None
        ).model_dump()
    )


# ========== 注册函数 ==========


def register_exception_handlers(app) -> None:
    """
    注册全局异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ComfyUIException, comfyui_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

