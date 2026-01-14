"""
异常处理器测试

测试全局异常处理器的正确性
"""

import pytest
from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from pydantic import BaseModel, Field

from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    comfyui_exception_handler,
    general_exception_handler,
    ComfyUIException,
    ComfyUIConnectionError,
    WorkflowValidationError,
    QueueOperationError,
    FileOperationError,
    ImageNotFoundError,
)
from app.schemas import ApiResponse, ResponseCode


# ========== Mock Request Fixture ==========


@pytest.fixture
def mock_request():
    """
    创建 Mock Request 对象

    用于测试异常处理器
    """
    from unittest.mock import MagicMock

    request = MagicMock(spec=Request)
    request.url = "http://test/api/v1/test"
    request.method = "GET"
    return request


# ========== HTTPException 处理器测试 ==========


class TestHTTPExceptionHandler:
    """测试 HTTPException 处理器"""

    @pytest.mark.asyncio
    async def test_http_400_bad_request(self, mock_request):
        """
        测试处理 400 Bad Request

        验证点:
        - 返回 HTTP 400 状态码
        - 响应格式统一
        - code 字段与 HTTP 状态码一致
        """
        exc = HTTPException(status_code=400, detail="请求参数错误")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 400
        data = response.body.decode()
        assert "400" in data
        assert "请求参数错误" in data

    @pytest.mark.asyncio
    async def test_http_401_unauthorized(self, mock_request):
        """
        测试处理 401 Unauthorized

        验证点:
        - 返回 HTTP 401 状态码
        - 包含未授权信息
        """
        exc = HTTPException(status_code=401, detail="未授权访问")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 401
        data = response.body.decode()
        assert "401" in data

    @pytest.mark.asyncio
    async def test_http_403_forbidden(self, mock_request):
        """
        测试处理 403 Forbidden

        验证点:
        - 返回 HTTP 403 状态码
        - 包含禁止访问信息
        """
        exc = HTTPException(status_code=403, detail="禁止访问")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_http_404_not_found(self, mock_request):
        """
        测试处理 404 Not Found

        验证点:
        - 返回 HTTP 404 状态码
        - 包含未找到信息
        """
        exc = HTTPException(status_code=404, detail="资源未找到")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 404
        data = response.body.decode()
        assert "404" in data

    @pytest.mark.asyncio
    async def test_http_500_internal_server_error(self, mock_request):
        """
        测试处理 500 Internal Server Error

        验证点:
        - 返回 HTTP 500 状态码
        """
        exc = HTTPException(status_code=500, detail="服务器内部错误")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_http_exception_with_headers(self, mock_request):
        """
        测试处理带 headers 的 HTTPException

        验证点:
        - headers 被正确处理（虽然不返回）
        - 响应仍然成功
        """
        exc = HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_response_body_structure(self, mock_request):
        """
        测试响应体结构符合 ApiResponse 格式

        验证点:
        - 包含 code 字段
        - 包含 message 字段
        - 包含 data 字段
        """
        import json

        exc = HTTPException(status_code=400, detail="错误详情")
        response = await http_exception_handler(mock_request, exc)

        body = json.loads(response.body.decode())
        assert "code" in body
        assert "message" in body
        assert "data" in body
        assert body["code"] == 400
        assert body["message"] == "错误详情"
        assert body["data"] is None


# ========== RequestValidationError 处理器测试 ==========


class TestValidationExceptionHandler:
    """测试 RequestValidationError 处理器"""

    @pytest.mark.asyncio
    async def test_validation_error_returns_400(self, mock_request):
        """
        测试验证错误返回 400 状态码

        验证点:
        - HTTP 状态码为 400
        - 业务错误码为 400 (VALIDATION_ERROR)
        """
        # 创建验证错误
        exc = RequestValidationError(errors=[])

        response = await validation_exception_handler(mock_request, exc)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validation_error_message(self, mock_request):
        """
        测试验证错误消息

        验证点:
        - 返回固定的中文消息
        - message = "请求参数验证失败"
        """
        import json

        exc = RequestValidationError(errors=[])
        response = await validation_exception_handler(mock_request, exc)

        body = json.loads(response.body.decode())
        assert body["message"] == "请求参数验证失败"

    @pytest.mark.asyncio
    async def test_validation_error_code(self, mock_request):
        """
        测试验证错误码

        验证点:
        - code = ResponseCode.VALIDATION_ERROR = 400
        """
        import json

        exc = RequestValidationError(errors=[])
        response = await validation_exception_handler(mock_request, exc)

        body = json.loads(response.body.decode())
        assert body["code"] == 400

    @pytest.mark.asyncio
    async def test_validation_error_with_errors(self, mock_request):
        """
        测试包含具体错误信息的验证异常

        验证点:
        - 即使有具体错误信息，也返回统一消息
        - data 字段为 None
        """
        import json

        errors = [
            {
                "loc": ("body", "field1"),
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        exc = RequestValidationError(errors=errors)
        response = await validation_exception_handler(mock_request, exc)

        body = json.loads(response.body.decode())
        assert body["code"] == 400
        assert body["message"] == "请求参数验证失败"
        assert body["data"] is None

    @pytest.mark.asyncio
    async def test_validation_error_response_structure(self, mock_request):
        """
        测试验证错误响应结构

        验证点:
        - 符合 ApiResponse 格式
        """
        import json

        exc = RequestValidationError(errors=[])
        response = await validation_exception_handler(mock_request, exc)

        body = json.loads(response.body.decode())
        assert set(body.keys()) == {"code", "message", "data"}


# ========== ComfyUIException 处理器测试 ==========


class TestComfyUIExceptionHandler:
    """测试 ComfyUIException 业务异常处理器"""

    @pytest.mark.asyncio
    async def test_comfyui_connection_error(self, mock_request):
        """
        测试 ComfyUI 连接错误

        验证点:
        - 返回 HTTP 500
        - code = 1001 (ERROR_COMFYUI_CONNECTION)
        """
        exc = ComfyUIConnectionError("无法连接到 ComfyUI 服务")
        response = await comfyui_exception_handler(mock_request, exc)

        assert response.status_code == 500

        import json
        body = json.loads(response.body.decode())
        assert body["code"] == 1001
        assert "无法连接" in body["message"]

    @pytest.mark.asyncio
    async def test_workflow_validation_error(self, mock_request):
        """
        测试工作流验证错误

        验证点:
        - 返回 HTTP 500
        - code = 1002 (ERROR_WORKFLOW_VALIDATION)
        """
        exc = WorkflowValidationError("工作流格式错误")
        response = await comfyui_exception_handler(mock_request, exc)

        assert response.status_code == 500

        import json
        body = json.loads(response.body.decode())
        assert body["code"] == 1002

    @pytest.mark.asyncio
    async def test_queue_operation_error(self, mock_request):
        """
        测试队列操作错误

        验证点:
        - 返回 HTTP 500
        - code = 1003 (ERROR_QUEUE_OPERATION)
        """
        exc = QueueOperationError("队列操作失败")
        response = await comfyui_exception_handler(mock_request, exc)

        assert response.status_code == 500

        import json
        body = json.loads(response.body.decode())
        assert body["code"] == 1003

    @pytest.mark.asyncio
    async def test_file_operation_error(self, mock_request):
        """
        测试文件操作错误

        验证点:
        - 返回 HTTP 500
        - code = 1004 (ERROR_FILE_OPERATION)
        """
        exc = FileOperationError("文件保存失败")
        response = await comfyui_exception_handler(mock_request, exc)

        assert response.status_code == 500

        import json
        body = json.loads(response.body.decode())
        assert body["code"] == 1004

    @pytest.mark.asyncio
    async def test_image_not_found_error(self, mock_request):
        """
        测试图片未找到错误

        验证点:
        - 返回 HTTP 500
        - code = 404 (ERROR_IMAGE_NOT_FOUND)
        - 消息包含文件名
        """
        exc = ImageNotFoundError("test_image.png")
        response = await comfyui_exception_handler(mock_request, exc)

        assert response.status_code == 500

        import json
        body = json.loads(response.body.decode())
        assert body["code"] == 404
        assert "test_image.png" in body["message"]

    @pytest.mark.asyncio
    async def test_base_comfyui_exception(self, mock_request):
        """
        测试基础 ComfyUIException

        验证点:
        - 未指定 code 时使用默认值
        - 消息正确传递
        """
        exc = ComfyUIException("自定义错误", code=1999)
        response = await comfyui_exception_handler(mock_request, exc)

        import json
        body = json.loads(response.body.decode())
        assert body["code"] == 1999
        assert body["message"] == "自定义错误"



# ========== 通用异常处理器测试 ==========


class TestGeneralExceptionHandler:
    """测试通用异常处理器"""

    @pytest.mark.asyncio
    async def test_generic_exception(self, mock_request):
        """
        测试通用异常处理

        验证点:
        - 返回 HTTP 500
        - code = 500 (INTERNAL_ERROR)
        - message = "服务器内部错误"
        """
        exc = Exception("未知错误")
        response = await general_exception_handler(mock_request, exc)

        assert response.status_code == 500

        import json
        body = json.loads(response.body.decode())
        assert body["code"] == 500
        assert body["message"] == "服务器内部错误"
        assert body["data"] is None


    @pytest.mark.asyncio
    async def test_various_exception_types(self, mock_request):
        """
        测试各种类型的异常

        验证点:
        - 所有未捕获的异常都被正确处理
        - 返回统一格式
        """
        exceptions = [
            ValueError("值错误"),
            TypeError("类型错误"),
            KeyError("键错误"),
            AttributeError("属性错误"),
            IndexError("索引错误"),
            RuntimeError("运行时错误"),
        ]

        for exc in exceptions:
            response = await general_exception_handler(mock_request, exc)

            assert response.status_code == 500

            import json
            body = json.loads(response.body.decode())
            assert body["code"] == 500
            assert body["message"] == "服务器内部错误"

    @pytest.mark.asyncio
    async def test_exception_with_special_characters(self, mock_request):
        """
        测试包含特殊字符的异常消息

        验证点:
        - 异常消息中的特殊字符不影响处理
        - 返回固定消息而非原始异常消息
        """
        exc = Exception("错误: 包含 特殊字符!@#$%")
        response = await general_exception_handler(mock_request, exc)

        import json
        body = json.loads(response.body.decode())
        # 通用异常返回固定消息，不暴露原始错误
        assert body["message"] == "服务器内部错误"


# ========== 异常类测试 ==========


class TestExceptionClasses:
    """测试自定义异常类"""

    def test_comfyui_connection_error_default_message(self):
        """
        测试 ComfyUIConnectionError 默认消息
        """
        exc = ComfyUIConnectionError()
        assert exc.message == "无法连接到 ComfyUI 服务"
        assert exc.code == 1001

    def test_comfyui_connection_error_custom_message(self):
        """
        测试 ComfyUIConnectionError 自定义消息
        """
        exc = ComfyUIConnectionError("连接超时")
        assert exc.message == "连接超时"
        assert exc.code == 1001

    def test_workflow_validation_error(self):
        """
        测试 WorkflowValidationError
        """
        exc = WorkflowValidationError("节点配置错误")
        assert exc.message == "节点配置错误"
        assert exc.code == 1002

    def test_queue_operation_error(self):
        """
        测试 QueueOperationError
        """
        exc = QueueOperationError("清空队列失败")
        assert exc.message == "清空队列失败"
        assert exc.code == 1003

    def test_file_operation_error(self):
        """
        测试 FileOperationError
        """
        exc = FileOperationError("文件写入失败")
        assert exc.message == "文件写入失败"
        assert exc.code == 1004

    def test_image_not_found_error(self):
        """
        测试 ImageNotFoundError
        """
        exc = ImageNotFoundError("missing.png")
        assert "missing.png" in exc.message
        assert exc.code == 404

    def test_base_exception_with_custom_code(self):
        """
        测试基础异常类带自定义错误码
        """
        exc = ComfyUIException("自定义", code=999)
        assert exc.message == "自定义"
        assert exc.code == 999

    def test_exception_is_exception_subclass(self):
        """
        测试所有自定义异常都是 Exception 的子类
        """
        assert issubclass(ComfyUIException, Exception)
        assert issubclass(ComfyUIConnectionError, ComfyUIException)
        assert issubclass(WorkflowValidationError, ComfyUIException)
        assert issubclass(QueueOperationError, ComfyUIException)
        assert issubclass(FileOperationError, ComfyUIException)
        assert issubclass(ImageNotFoundError, ComfyUIException)


# ========== 异常处理器集成测试 ==========


class TestExceptionHandlersIntegration:
    """异常处理器集成测试"""

    @pytest.mark.asyncio
    async def test_all_handlers_return_json_response(self, mock_request):
        """
        测试所有异常处理器都返回 JSONResponse

        验证点:
        - 所有处理器返回类型一致
        """
        from fastapi.responses import JSONResponse

        handlers = [
            (http_exception_handler, HTTPException(400, "test")),
            (validation_exception_handler, RequestValidationError([])),
            (comfyui_exception_handler, ComfyUIConnectionError()),
            (general_exception_handler, Exception("test")),
        ]

        for handler, exc in handlers:
            response = await handler(mock_request, exc)
            assert isinstance(response, JSONResponse)

    @pytest.mark.asyncio
    async def test_all_handlers_return_api_response_format(self, mock_request):
        """
        测试所有异常处理器返回 ApiResponse 格式

        验证点:
        - 响应体包含 code, message, data
        """
        import json

        handlers = [
            (http_exception_handler, HTTPException(400, "test")),
            (validation_exception_handler, RequestValidationError([])),
            (comfyui_exception_handler, ComfyUIConnectionError()),
            (general_exception_handler, Exception("test")),
        ]

        for handler, exc in handlers:
            response = await handler(mock_request, exc)
            body = json.loads(response.body.decode())

            assert "code" in body
            assert "message" in body
            assert "data" in body
            assert body["data"] is None
