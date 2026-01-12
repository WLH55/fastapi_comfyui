"""
统一响应模型
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式

    Attributes:
        code: 响应码
        message: 响应消息
        data: 响应数据
    """

    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

    class Config:
        """Pydantic 配置"""
        json_encoders = {
            # 自定义 JSON 编码器（如果需要）
        }

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "ApiResponse[T]":
        """成功响应"""
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str, data: Any = None) -> "ApiResponse[T]":
        """错误响应"""
        return cls(code=code, message=message, data=data)


# 常用的响应码定义
class ResponseCode:
    """响应码常量"""

    # 成功
    SUCCESS = 200
    CREATED = 201

    # 客户端错误
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    VALIDATION_ERROR = 422

    # 服务器错误
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503

    # 业务错误码
    ERROR_COMFYUI_CONNECTION = 1001
    ERROR_WORKFLOW_VALIDATION = 1002
    ERROR_QUEUE_OPERATION = 1003
    ERROR_FILE_OPERATION = 1004
    ERROR_IMAGE_NOT_FOUND = 1005
    ERROR_WEBSOCKET = 1006
    ERROR_TEMPLATE_NOT_FOUND = 1007
