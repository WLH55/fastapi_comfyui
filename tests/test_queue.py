"""
队列路由测试

测试 /api/v1/queue/* 相关接口
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestQueueStatus:
    """测试获取队列状态接口 GET /api/v1/queue/status"""

    def test_get_queue_status_success(self, client, mock_comfyui_client, mock_queue_status_data):
        """
        测试成功获取队列状态

        验证点:
        - 状态码为 200
        - 返回正确的队列信息
        - 数据格式正确（包含 queue_running 和 queue_pending）
        """
        mock_comfyui_client.get_queue_status.return_value = mock_queue_status_data

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "获取队列状态成功"
            assert "data" in data

            # 验证返回数据结构
            queue_data = data["data"]
            assert "queue_running" in queue_data
            assert "queue_pending" in queue_data
            assert "running_count" in queue_data
            assert "pending_count" in queue_data
            assert queue_data["running_count"] == 2
            assert queue_data["pending_count"] == 2

    def test_get_queue_status_empty(self, client, mock_comfyui_client):
        """
        测试获取空队列状态
        """
        mock_comfyui_client.get_queue_status.return_value = {
            "queue_running": [],
            "queue_pending": []
        }

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["running_count"] == 0
            assert data["data"]["pending_count"] == 0

    def test_get_queue_status_malformed_data(self, client, mock_comfyui_client):
        """
        测试处理格式错误的队列数据

        当队列数据项长度小于3时，应该被过滤掉
        """
        malformed_data = {
            "queue_running": [
                [1, "prompt-1", 1234567890],  # 正常
                [2, "prompt-2"],  # 格式错误（缺少时间戳）
            ],
            "queue_pending": [
                [3],  # 格式错误（只有编号）
            ]
        }
        mock_comfyui_client.get_queue_status.return_value = malformed_data

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            # 只应该返回格式正确的数据
            assert data["data"]["running_count"] == 1
            assert data["data"]["pending_count"] == 0

    def test_get_queue_status_connection_error(self, client, mock_comfyui_client):
        """
        测试获取队列状态时连接错误
        """
        from app.exceptions import ComfyUIConnectionError
        from app.schemas import ResponseCode

        mock_comfyui_client.get_queue_status.side_effect = ComfyUIConnectionError("ComfyUI 服务不可用")

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == ResponseCode.ERROR_COMFYUI_CONNECTION
            assert "不可用" in data["message"]

    def test_get_queue_status_large_queue(self, client, mock_comfyui_client):
        """
        测试获取大量队列项的状态
        """
        large_queue = {
            "queue_running": [[i, f"running-{i}", 1234567890 + i] for i in range(50)],
            "queue_pending": [[i, f"pending-{i}", 1234567890 + i] for i in range(50, 100)]
        }
        mock_comfyui_client.get_queue_status.return_value = large_queue

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["running_count"] == 50
            assert data["data"]["pending_count"] == 50


class TestQueueClear:
    """测试清空队列接口 POST /api/v1/queue/clear"""

    def test_clear_queue_success(self, client, mock_comfyui_client):
        """
        测试成功清空队列
        """
        mock_comfyui_client.clear_queue.return_value = {"detail": "Queue cleared"}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "队列已清空"
            assert "detail" in data["data"]
            mock_comfyui_client.clear_queue.assert_called_once_with({"clear": True})



class TestQueueDelete:
    """测试删除队列项接口 POST /api/v1/queue/delete"""

    def test_delete_single_item(self, client, mock_comfyui_client):
        """
        测试删除单个队列项

        验证点:
        - 状态码为 200
        - 返回成功消息
        - 正确调用 clear_queue 方法
        """
        mock_comfyui_client.clear_queue.return_value = {"detail": "Deleted"}

        request_data = {"delete": ["prompt-id-1"]}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "['prompt-id-1']删除成功"
            mock_comfyui_client.clear_queue.assert_called_once_with({"delete": ["prompt-id-1"]})

    def test_delete_multiple_items(self, client, mock_comfyui_client):
        """
        测试删除多个队列项

        验证点:
        - 支持批量删除
        - 消息包含所有删除的 prompt_id
        """
        mock_comfyui_client.clear_queue.return_value = {"detail": "Deleted"}

        request_data = {
            "delete": ["prompt-1", "prompt-2", "prompt-3"]
        }

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "prompt-1" in data["message"]
            assert "prompt-2" in data["message"]
            assert "prompt-3" in data["message"]
            mock_comfyui_client.clear_queue.assert_called_once_with({"delete": ["prompt-1", "prompt-2", "prompt-3"]})

    def test_delete_empty_list(self, client, mock_comfyui_client):
        """
        测试删除空列表

        验证点:
        - 空列表是有效输入
        - 仍然调用 clear_queue
        """
        mock_comfyui_client.clear_queue.return_value = {"detail": "Nothing to delete"}

        request_data = {"delete": []}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 200
            mock_comfyui_client.clear_queue.assert_called_once_with({"delete": []})

    def test_delete_missing_delete_field(self, client, mock_comfyui_client):
        """
        测试缺少 delete 字段

        验证点:
        - Pydantic 验证失败
        - 返回 422 错误
        """
        request_data = {}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 400
            mock_comfyui_client.clear_queue.assert_not_called()

    def test_delete_invalid_delete_type(self, client, mock_comfyui_client):
        """
        测试 delete 字段类型错误

        验证点:
        - delete 不是列表时验证失败
        - 返回 422 错误
        """
        request_data = {"delete": "not-a-list"}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 400

    def test_delete_connection_error(self, client, mock_comfyui_client):
        """
        测试删除时连接错误
        """
        from app.exceptions import ComfyUIConnectionError
        from app.schemas import ResponseCode

        mock_comfyui_client.clear_queue.side_effect = ComfyUIConnectionError("无法连接")

        request_data = {"delete": ["prompt-1"]}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == ResponseCode.ERROR_COMFYUI_CONNECTION

    def test_delete_queue_operation_error(self, client, mock_comfyui_client):
        """
        测试删除时队列操作错误
        """
        from app.exceptions import QueueOperationError
        from app.schemas import ResponseCode

        mock_comfyui_client.clear_queue.side_effect = QueueOperationError("删除失败")

        request_data = {"delete": ["prompt-1"]}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == ResponseCode.ERROR_QUEUE_OPERATION

    @pytest.mark.parametrize("prompt_ids,expected_count", [
        (["p1"], 1),
        (["p1", "p2", "p3"], 3),
        ([], 0),
        (["p" + str(i) for i in range(10)], 10),
    ])
    def test_delete_parametrized(self, client, mock_comfyui_client, prompt_ids, expected_count):
        """
        参数化测试：不同数量的删除项
        """
        mock_comfyui_client.clear_queue.return_value = {"detail": "Deleted"}

        request_data = {"delete": prompt_ids}

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 200
            mock_comfyui_client.clear_queue.assert_called_once_with({"delete": prompt_ids})


class TestQueueEdgeCases:
    """队列接口边界情况测试"""

    def test_concurrent_queue_status_requests(self, client, mock_comfyui_client):
        """
        测试并发获取队列状态
        """
        import threading

        results = []
        mock_comfyui_client.get_queue_status.return_value = {
            "queue_running": [],
            "queue_pending": []
        }

        def make_request():
            with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
                resp = client.get("/api/v1/queue/status")
                results.append(resp.status_code)

        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(status == 200 for status in results)

    def test_queue_data_with_special_characters(self, client, mock_comfyui_client):
        """
        测试队列数据中包含特殊字符
        """
        queue_data = {
            "queue_running": [
                [1, "prompt-with-特殊字符-中文", 1234567890],
            ],
            "queue_pending": []
        }
        mock_comfyui_client.get_queue_status.return_value = queue_data

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["queue_running"][0]["prompt_id"] == "prompt-with-特殊字符-中文"

    def test_queue_with_future_timestamps(self, client, mock_comfyui_client):
        """
        测试队列数据中包含未来时间戳
        """
        import time
        future_timestamp = int(time.time()) + 3600  # 1小时后

        queue_data = {
            "queue_running": [[1, "future-prompt", future_timestamp]],
            "queue_pending": []
        }
        mock_comfyui_client.get_queue_status.return_value = queue_data

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["queue_running"][0]["timestamp"] == future_timestamp

    def test_queue_with_zero_timestamp(self, client, mock_comfyui_client):
        """
        测试队列数据中包含零时间戳
        """
        queue_data = {
            "queue_running": [[1, "zero-timestamp", 0]],
            "queue_pending": []
        }
        mock_comfyui_client.get_queue_status.return_value = queue_data

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["queue_running"][0]["timestamp"] == 0

    def test_delete_with_special_prompt_ids(self, client, mock_comfyui_client):
        """
        测试删除包含特殊字符的 prompt_id
        """
        mock_comfyui_client.clear_queue.return_value = {"detail": "Deleted"}

        request_data = {
            "delete": ["prompt-with-特殊字符", "prompt/with/slashes", "prompt with spaces"]
        }

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/queue/delete", json=request_data)

            assert response.status_code == 200
            mock_comfyui_client.clear_queue.assert_called_once()

    def test_queue_response_data_structure(self, client, mock_comfyui_client):
        """
        测试队列响应数据结构

        验证点:
        - 返回的队列项包含所有必需字段
        - 字段类型正确
        """
        queue_data = {
            "queue_running": [[1, "running-1", 1234567890]],
            "queue_pending": [[2, "pending-1", 1234567891]]
        }
        mock_comfyui_client.get_queue_status.return_value = queue_data

        with patch("app.routers.queue.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()["data"]

            # 验证 queue_running 结构
            running_item = data["queue_running"][0]
            assert "prompt_id" in running_item
            assert "number" in running_item
            assert "timestamp" in running_item
            assert isinstance(running_item["number"], int)
            assert isinstance(running_item["timestamp"], int)
