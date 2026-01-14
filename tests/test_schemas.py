"""
响应模型测试

测试 ApiResponse 和 ResponseCode 的正确性
"""

import pytest
from pydantic import ValidationError

from app.schemas import ApiResponse, ResponseCode


class TestResponseCode:
    """测试 ResponseCode 响应码常量"""

    def test_success_codes(self):
        """
        测试成功类响应码

        验证点:
        - SUCCESS = 200
        - CREATED = 201
        """
        assert ResponseCode.SUCCESS == 200
        assert ResponseCode.CREATED == 201

    def test_client_error_codes(self):
        """
        测试客户端错误响应码

        验证点:
        - BAD_REQUEST = 400
        - UNAUTHORIZED = 401
        - FORBIDDEN = 403
        - NOT_FOUND = 404
        - CONFLICT = 409
        - VALIDATION_ERROR = 400
        """
        assert ResponseCode.BAD_REQUEST == 400
        assert ResponseCode.UNAUTHORIZED == 401
        assert ResponseCode.FORBIDDEN == 403
        assert ResponseCode.NOT_FOUND == 404
        assert ResponseCode.CONFLICT == 409
        assert ResponseCode.VALIDATION_ERROR == 400

    def test_server_error_codes(self):
        """
        测试服务器错误响应码

        验证点:
        - INTERNAL_ERROR = 500
        - SERVICE_UNAVAILABLE = 503
        """
        assert ResponseCode.INTERNAL_ERROR == 500
        assert ResponseCode.SERVICE_UNAVAILABLE == 503

    def test_business_error_codes(self):
        """
        测试业务错误响应码

        验证点:
        - ERROR_COMFYUI_CONNECTION = 1001
        - ERROR_WORKFLOW_VALIDATION = 1002
        - ERROR_QUEUE_OPERATION = 1003
        - ERROR_FILE_OPERATION = 1004
        - ERROR_IMAGE_NOT_FOUND = 404
        - ERROR_WEBSOCKET = 1006
        - ERROR_TEMPLATE_NOT_FOUND = 1007
        """
        assert ResponseCode.ERROR_COMFYUI_CONNECTION == 1001
        assert ResponseCode.ERROR_WORKFLOW_VALIDATION == 1002
        assert ResponseCode.ERROR_QUEUE_OPERATION == 1003
        assert ResponseCode.ERROR_FILE_OPERATION == 1004
        assert ResponseCode.ERROR_IMAGE_NOT_FOUND == 404
        assert ResponseCode.ERROR_WEBSOCKET == 1006
        assert ResponseCode.ERROR_TEMPLATE_NOT_FOUND == 1007


class TestApiResponse:
    """测试 ApiResponse 响应模型"""

    def test_default_values(self):
        """
        测试默认值

        验证点:
        - 默认 code = 200
        - 默认 message = "success"
        - 默认 data = None
        """
        response = ApiResponse()
        assert response.code == 200
        assert response.message == "success"
        assert response.data is None

    def test_success_method(self):
        """
        测试 success 类方法

        验证点:
        - 返回正确的 ApiResponse 实例
        - code = 200
        - message 可自定义
        - data 可设置任意值
        """
        # 默认消息
        response = ApiResponse.success()
        assert response.code == 200
        assert response.message == "success"
        assert response.data is None

        # 自定义消息
        response = ApiResponse.success(message="操作成功")
        assert response.code == 200
        assert response.message == "操作成功"

        # 带数据
        data = {"key": "value", "count": 100}
        response = ApiResponse.success(data=data, message="获取数据成功")
        assert response.code == 200
        assert response.message == "获取数据成功"
        assert response.data == data

    def test_success_method_with_complex_data(self):
        """
        测试 success 方法处理复杂数据

        验证点:
        - 支持字典数据
        - 支持列表数据
        - 支持嵌套结构
        """
        # 字典数据
        dict_data = {"user": {"id": 1, "name": "test"}, "token": "abc123"}
        response = ApiResponse.success(data=dict_data)
        assert response.data == dict_data

        # 列表数据
        list_data = [1, 2, 3, 4, 5]
        response = ApiResponse.success(data=list_data)
        assert response.data == list_data

        # 嵌套结构
        nested_data = {
            "users": [
                {"id": 1, "name": "user1"},
                {"id": 2, "name": "user2"}
            ],
            "total": 2,
            "page": 1
        }
        response = ApiResponse.success(data=nested_data)
        assert response.data == nested_data

    def test_error_method(self):
        """
        测试 error 类方法

        验证点:
        - 返回正确的 ApiResponse 实例
        - code 可自定义
        - message 可自定义
        - data 可设置任意值
        """
        # 基本错误
        response = ApiResponse.error(code=400, message="请求参数错误")
        assert response.code == 400
        assert response.message == "请求参数错误"
        assert response.data is None

        # 带数据的错误
        error_data = {"field": "email", "error": "格式不正确"}
        response = ApiResponse.error(code=422, message="验证失败", data=error_data)
        assert response.code == 422
        assert response.message == "验证失败"
        assert response.data == error_data

    def test_error_method_with_response_codes(self):
        """
        测试 error 方法使用 ResponseCode 常量

        验证点:
        - 支持使用 ResponseCode 中的常量
        """
        response = ApiResponse.error(
            code=ResponseCode.ERROR_COMFYUI_CONNECTION,
            message="无法连接到 ComfyUI"
        )
        assert response.code == 1001
        assert response.message == "无法连接到 ComfyUI"

    def test_model_serialization(self):
        """
        测试模型序列化为字典

        验证点:
        - model_dump() 返回正确的字典结构
        - 包含 code, message, data 字段
        """
        response = ApiResponse.success(
            data={"id": 123},
            message="操作成功"
        )
        serialized = response.model_dump()

        assert serialized == {
            "code": 200,
            "message": "操作成功",
            "data": {"id": 123}
        }

    def test_model_serialization_with_none_data(self):
        """
        测试 data 为 None 时的序列化

        验证点:
        - data 字段正确序列化为 None
        """
        response = ApiResponse.error(code=404, message="未找到", data=None)
        serialized = response.model_dump()

        assert serialized == {
            "code": 404,
            "message": "未找到",
            "data": None
        }

    def test_model_json_compatibility(self):
        """
        测试 JSON 兼容性

        验证点:
        - model_dump_json() 返回有效 JSON 字符串
        - 可被 json.loads() 解析
        """
        import json

        response = ApiResponse.success(data={"test": "value"})
        json_str = response.model_dump_json()

        parsed = json.loads(json_str)
        assert parsed["code"] == 200
        assert parsed["data"]["test"] == "value"

    def test_generic_type_support(self):
        """
        测试泛型类型支持

        验证点:
        - 支持 ApiResponse[Dict]
        - 支持 ApiResponse[List]
        - 类型提示正确
        """
        from typing import Dict, List

        # Dict 类型
        dict_response: ApiResponse[Dict[str, int]] = ApiResponse.success(data={"a": 1, "b": 2})
        assert isinstance(dict_response.data, dict)

        # List 类型
        list_response: ApiResponse[List[str]] = ApiResponse.success(data=["a", "b", "c"])
        assert isinstance(list_response.data, list)

    def test_special_characters_in_message(self):
        """
        测试消息中的特殊字符

        验证点:
        - 支持中文
        - 支持特殊符号
        - 支持换行符
        """
        # 中文
        response = ApiResponse.success(message="操作成功完成")
        assert response.message == "操作成功完成"

        # 特殊符号
        response = ApiResponse.error(code=500, message="错误: 文件未找到!")
        assert "错误:" in response.message

        # 换行符
        message = "第一行\n第二行"
        response = ApiResponse.error(code=500, message=message)
        assert response.message == message

    def test_empty_and_whitespace_values(self):
        """
        测试空值和空白字符

        验证点:
        - 支持空字符串
        - 支持空列表
        - 支持空字典
        """
        # 空字符串
        response = ApiResponse.success(data="", message="")
        assert response.data == ""
        assert response.message == ""

        # 空列表
        response = ApiResponse.success(data=[])
        assert response.data == []

        # 空字典
        response = ApiResponse.success(data={})
        assert response.data == {}

    def test_data_field_optional(self):
        """
        测试 data 字段可选性

        验证点:
        - 不传 data 时默认为 None
        - 显式传入 None
        """
        # 不传 data
        response1 = ApiResponse.success(message="test")
        assert response1.data is None

        # 显式传 None
        response2 = ApiResponse.success(data=None, message="test")
        assert response2.data is None


class TestApiResponseEdgeCases:
    """ApiResponse 边界情况测试"""

    def test_large_data(self):
        """
        测试大数据量

        验证点:
        - 支持大量数据的序列化
        """
        large_list = list(range(10000))
        response = ApiResponse.success(data=large_list)
        assert len(response.data) == 10000

    def test_nested_deep_structure(self):
        """
        测试深层嵌套结构

        验证点:
        - 支持多层嵌套
        """
        deep_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep"
                        }
                    }
                }
            }
        }
        response = ApiResponse.success(data=deep_data)
        assert response.data["level1"]["level2"]["level3"]["level4"]["value"] == "deep"

    def test_unicode_in_data(self):
        """
        测试数据中的 Unicode 字符

        验证点:
        - 支持 emoji
        - 支持各种语言字符
        """
        data = {
            "emoji": "😀🎨",
            "chinese": "中文测试",
            "japanese": "日本語",
            "arabic": "العربية"
        }
        response = ApiResponse.success(data=data)
        assert response.data["emoji"] == "😀🎨"
        assert response.data["chinese"] == "中文测试"

    def test_boolean_and_numeric_codes(self):
        """
        测试布尔和数值类型的响应码

        验证点:
        - 支持 0 作为响应码
        - 支持大数值响应码
        """
        # 零值
        response = ApiResponse.error(code=0, message="test")
        assert response.code == 0

        # 大数值
        response = ApiResponse.error(code=9999, message="test")
        assert response.code == 9999
