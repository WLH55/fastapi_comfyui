"""
工作流路由测试

测试 /api/v1/workflows/* 相关接口
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestWorkflowsSubmit:
    """测试提交工作流接口 POST /api/v1/workflows/submit"""

    def test_submit_workflow_success(self, client, mock_comfyui_client, valid_workflow_submit_request):
        """
        测试成功提交工作流

        验证点:
        - 状态码为 200
        - 返回 prompt_id
        - 返回正确的响应格式
        """
        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/submit", json=valid_workflow_submit_request)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "工作流已提交"
            assert "data" in data
            assert "prompt_id" in data["data"]
            mock_comfyui_client.submit_prompt.assert_called_once()

    def test_submit_workflow_with_client_id(self, client, mock_comfyui_client):
        """
        测试提交工作流并指定 client_id
        """
        request_data = {
            "workflow": {"1": {"class_type": "KSampler"}},
            "client_id": "test-client-123"
        }

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/submit", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["client_id"] == "test-client-123"

    def test_submit_workflow_empty_workflow(self, client, mock_comfyui_client):
        """
        测试提交空工作流

        验证系统能处理空 workflow 的情况
        """
        request_data = {"workflow": {}, "client_id": "test"}

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/submit", json=request_data)

            assert response.status_code == 200
            mock_comfyui_client.submit_prompt.assert_called_once_with({}, "test")

    def test_submit_workflow_connection_error(self, client, mock_comfyui_client):
        """
        测试 ComfyUI 连接错误

        模拟 ComfyUIConnectionError 异常
        """
        from app.exceptions import ComfyUIConnectionError
        from app.schemas import ResponseCode

        mock_comfyui_client.submit_prompt.side_effect = ComfyUIConnectionError("无法连接到 ComfyUI")

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/submit", json={"workflow": {}})

            assert response.status_code == 200  # 业务异常仍然返回 200
            data = response.json()
            assert data["code"] == ResponseCode.ERROR_COMFYUI_CONNECTION
            assert "无法连接" in data["message"]


class TestWorkflowsHistory:
    """测试获取工作流历史接口 GET /api/v1/workflows/{prompt_id}/history"""

    def test_get_history_success(self, client, mock_comfyui_client, mock_history_data):
        """
        测试成功获取工作流历史
        """
        prompt_id = "test-prompt-id"
        mock_comfyui_client.get_history.return_value = mock_history_data

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.get(f"/api/v1/workflows/{prompt_id}/history")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "获取历史记录成功"
            assert data["data"]["prompt_id"] == prompt_id
            mock_comfyui_client.get_history.assert_called_once_with(prompt_id)

    def test_get_history_not_found(self, client, mock_comfyui_client):
        """
        测试获取不存在的工作流历史

        验证返回 404 错误码
        """
        mock_comfyui_client.get_history.return_value = None

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/workflows/non-existent/history")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 404
            assert "不存在" in data["message"] or "尚未完成" in data["message"]

    def test_get_history_with_empty_history(self, client, mock_comfyui_client):
        """
        测试获取历史时返回空数据
        """
        mock_comfyui_client.get_history.return_value = {}

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/workflows/empty-id/history")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 404

    @pytest.mark.parametrize("prompt_id,expected_code", [
        ("valid-id-123", 200),
        ("another-id-456", 200),
        ("not-found", 404),
    ])
    def test_get_history_parametrized(self, client, mock_comfyui_client, prompt_id, expected_code):
        """
        参数化测试：多种场景获取历史
        """
        if expected_code == 200:
            mock_comfyui_client.get_history.return_value = {"prompt": [1, "test"]}
        else:
            mock_comfyui_client.get_history.return_value = None

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.get(f"/api/v1/workflows/{prompt_id}/history")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == expected_code


class TestWorkflowsInterrupt:
    """测试中断工作流接口 POST /api/v1/workflows/interrupt"""

    def test_interrupt_workflow_success(self, client, mock_comfyui_client):
        """
        测试成功中断工作流
        """
        request_data = {"prompt_id": "test-prompt-123"}
        mock_comfyui_client.interrupt.return_value = {"detail": "Interrupted"}

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/interrupt", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "工作流已中断"
            assert "detail" in data["data"]
            mock_comfyui_client.interrupt.assert_called_once_with("test-prompt-123")

    def test_interrupt_workflow_without_prompt_id(self, client, mock_comfyui_client):
        """
        测试不提供 prompt_id 的中断请求
        """
        request_data = {}

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/interrupt", json=request_data)

            # 应该返回成功，但 prompt_id 为 None
            assert response.status_code == 200
            mock_comfyui_client.interrupt.assert_called_once_with(None)

    def test_interrupt_workflow_exception(self, client, mock_comfyui_client):
        """
        测试中断工作流时发生异常
        """
        mock_comfyui_client.interrupt.side_effect = Exception("中断失败")

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/interrupt", json={"prompt_id": "test"})

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 500
            assert "中断工作流失败" in data["message"]


class TestWorkflowsEdgeCases:
    """工作流接口边界情况测试"""

    def test_submit_malformed_workflow(self, client, mock_comfyui_client):
        """
        测试提交格式错误的工作流
        """
        # 提交非字典类型的 workflow
        request_data = {"workflow": "not-a-dict"}

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/submit", json=request_data)

            # 验证系统处理了这种情况
            assert response.status_code == 200

    def test_submit_complex_workflow(self, client, mock_comfyui_client):
        """
        测试提交包含多个节点的复杂工作流
        """
        complex_workflow = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "positive prompt"}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "negative prompt"}},
            "4": {"class_type": "KSampler", "inputs": {"seed": 12345, "steps": 20}},
            "5": {"class_type": "VAEDecode", "inputs": {"samples": ["4", 0], "vae": ["1", 0]}},
            "6": {"class_type": "SaveImage", "inputs": {"images": ["5", 0]}},
        }

        request_data = {"workflow": complex_workflow, "client_id": "test"}

        with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/workflows/submit", json=request_data)

            assert response.status_code == 200
            mock_comfyui_client.submit_prompt.assert_called_once()

    def test_concurrent_submit_requests(self, client, mock_comfyui_client):
        """
        测试并发提交多个工作流请求
        """
        import threading

        results = []
        request_data = {"workflow": {}, "client_id": "test"}

        def make_request():
            with patch("app.routers.workflows.comfyui_client", mock_comfyui_client):
                resp = client.post("/api/v1/workflows/submit", json=request_data)
                results.append(resp.status_code)

        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有请求都应该成功
        assert all(status == 200 for status in results)
