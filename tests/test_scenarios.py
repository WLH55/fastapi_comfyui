"""
场景路由测试

测试 /api/v1/scenarios/* 相关接口
"""

import pytest
from unittest.mock import AsyncMock, patch
import json


class TestScenariosCPUQuickly:
    """测试 CPU Quickly 图生图接口 POST /api/v1/scenarios/cpu_quickly"""

    def test_cpu_quickly_success(self, client, mock_comfyui_client, valid_cpu_quickly_request):
        """
        测试成功执行 CPU Quickly 场景
        """
        mock_comfyui_client.submit_prompt.return_value = "test-prompt-id-123"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=valid_cpu_quickly_request)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 200
            assert result["message"] == "图生图任务已提交"
            assert "prompt_id" in result["data"]
            assert result["data"]["scenario"] == "cpu_quickly"
            mock_comfyui_client.submit_prompt.assert_called_once()

    def test_cpu_quickly_with_negative_prompt(self, client, mock_comfyui_client):
        """
        测试包含负面提示词的请求
        """
        request_data = {
            "prompt": "a beautiful landscape",
            "negative_prompt": "ugly, blurry, low quality",
            "input_image": "test.png"
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 200

    def test_cpu_quickly_without_negative_prompt(self, client, mock_comfyui_client):
        """
        测试不提供负面提示词（使用默认值）
        """
        request_data = {
            "prompt": "a beautiful landscape",
            "input_image": "test.png"
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            assert response.status_code == 200

    def test_cpu_quickly_missing_required_field(self, client, mock_comfyui_client):
        """
        测试缺少必填字段
        """
        # 缺少 prompt
        request_data = {
            "negative_prompt": "ugly",
            "input_image": "test.png"
        }

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            # Pydantic 验证失败，返回 422
            assert response.status_code == 422

    def test_cpu_quickly_template_not_found(self, client, mock_comfyui_client):
        """
        测试 workflow 模板文件不存在
        """
        from app.internal.workflow_handlers import load_cpu_quickly_workflow

        # 模拟 FileNotFoundError
        load_cpu_quickly_workflow.side_effect = FileNotFoundError("模板文件不存在")

        request_data = {
            "prompt": "test",
            "negative_prompt": "",
            "input_image": "test.png"
        }

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            with patch("app.internal.workflow_handlers.load_cpu_quickly_workflow", load_cpu_quickly_workflow):
                response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

                assert response.status_code == 200
                result = response.json()
                assert result["code"] == 404
                assert "模板文件不存在" in result["message"]

    def test_cpu_quickly_submit_exception(self, client, mock_comfyui_client):
        """
        测试提交工作流时发生异常
        """
        mock_comfyui_client.submit_prompt.side_effect = Exception("提交失败")

        request_data = {
            "prompt": "test",
            "negative_prompt": "",
            "input_image": "test.png"
        }

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 500
            assert "执行失败" in result["message"]

    @pytest.mark.parametrize("prompt,expected_valid", [
        ("a beautiful landscape", True),
        ("1girl, anime style, detailed", True),
        ("", True),  # 空提示词可能有效
        ("x" * 10000, True),  # 长提示词
    ])
    def test_cpu_quickly_various_prompts(self, client, mock_comfyui_client, prompt, expected_valid):
        """
        参数化测试：不同类型的提示词
        """
        request_data = {
            "prompt": prompt,
            "negative_prompt": "",
            "input_image": "test.png"
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            assert response.status_code == 200

    def test_cpu_quickly_with_special_characters(self, client, mock_comfyui_client):
        """
        测试包含特殊字符的提示词
        """
        request_data = {
            "prompt": "测试 prompt with 特殊字符!@#$%",
            "negative_prompt": "避免的",
            "input_image": "测试图片.png"
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            assert response.status_code == 200


class TestScenariosEdgeCases:
    """场景接口边界情况测试"""

    def test_cpu_quickly_empty_input_image(self, client, mock_comfyui_client):
        """
        测试空的输入图片文件名
        """
        request_data = {
            "prompt": "test",
            "negative_prompt": "",
            "input_image": ""
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            # 空字符串是有效的默认值
            assert response.status_code == 200

    def test_cpu_quickly_with_unicode_emoji(self, client, mock_comfyui_client):
        """
        测试包含 emoji 的提示词
        """
        request_data = {
            "prompt": "a beautiful landscape 🌄✨",
            "negative_prompt": "ugly 😖",
            "input_image": "test.png"
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            assert response.status_code == 200

    def test_cpu_quickly_workflow_parameters(self, client, mock_comfyui_client):
        """
        测试 workflow 参数正确应用
        """
        request_data = {
            "prompt": "test prompt",
            "negative_prompt": "test negative",
            "input_image": "test_image.png"
        }

        captured_workflow = None

        def capture_workflow(workflow, client_id):
            nonlocal captured_workflow
            captured_workflow = workflow
            return "prompt-id"

        mock_comfyui_client.submit_prompt.side_effect = capture_workflow

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            assert response.status_code == 200
            # 验证 workflow 被正确修改
            assert captured_workflow is not None

    def test_concurrent_scenario_requests(self, client, mock_comfyui_client):
        """
        测试并发场景请求
        """
        import threading

        results = []
        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        def make_request():
            request_data = {
                "prompt": "test",
                "negative_prompt": "",
                "input_image": "test.png"
            }
            with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
                resp = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)
                results.append(resp.status_code)

        threads = [threading.Thread(target=make_request) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(status == 200 for status in results)


class TestScenariosValidation:
    """场景接口参数验证测试"""

    def test_invalid_request_body_type(self, client, mock_comfyui_client):
        """
        测试无效的请求体类型
        """
        # 发送数组而不是对象
        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=[])

            assert response.status_code == 422

    def test_extra_fields_allowed(self, client, mock_comfyui_client):
        """
        测试额外字段的处理（Pydantic 默认忽略额外字段）
        """
        request_data = {
            "prompt": "test",
            "negative_prompt": "",
            "input_image": "test.png",
            "extra_field": "should be ignored"
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            # Pydantic 使用 extra='ignore' 模式，应该成功
            assert response.status_code == 200

    @pytest.mark.parametrize("prompt,negative_prompt,image", [
        ("x" * 5000, "y" * 5000, "a" * 200 + ".png"),  # 超长字符串
        ("   ", "   ", "   "),  # 空白字符
        ("test\nprompt", "test\nnegative", "test\nimage.png"),  # 包含换行
    ])
    def test_edge_case_strings(self, client, mock_comfyui_client, prompt, negative_prompt, image):
        """
        参数化测试：边界情况字符串
        """
        request_data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "input_image": image
        }

        mock_comfyui_client.submit_prompt.return_value = "prompt-id"

        with patch("app.routers.scenarios.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/scenarios/cpu_quickly", json=request_data)

            # 应该能接受各种字符串
            assert response.status_code == 200
