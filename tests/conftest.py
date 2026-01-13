"""
Pytest 配置和共享 Fixtures

提供测试所需的共享 fixtures 和 mock 对象
"""

import asyncio
import pytest
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import create_app
from app.internal.comfyui import ComfyUIClient


# ============ 应用 Fixtures ============


@pytest.fixture
def app():
    """
    创建 FastAPI 测试应用实例

    跳过 lifespan 事件
    """
    # 创建空 lifespan 来跳过初始化
    @asynccontextmanager
    async def empty_lifespan(app):
        yield

    # 创建应用并替换 lifespan
    app_instance = create_app()
    app_instance.router.lifespan_context = empty_lifespan

    yield app_instance


@pytest.fixture
def client(app) -> TestClient:
    """
    创建测试客户端

    提供用于 HTTP 请求测试的 TestClient 实例
    """
    with TestClient(app) as test_client:
        yield test_client


# ============ ComfyUI Client Mock Fixtures ============


@pytest.fixture
def mock_comfyui_client():
    """
    Mock ComfyUI 客户端

    提供所有 ComfyUI 方法的 mock 实现
    """
    mock_client = AsyncMock(spec=ComfyUIClient)

    # submit_prompt 方法默认返回值
    mock_client.submit_prompt.return_value = "test-prompt-id-123"

    # get_queue_status 方法默认返回值
    mock_client.get_queue_status.return_value = {
        "queue_running": [],
        "queue_pending": []
    }

    # clear_queue 方法默认返回值
    mock_client.clear_queue.return_value = {"detail": "Queue cleared"}

    # get_history 方法默认返回值
    mock_client.get_history.return_value = None

    # interrupt 方法默认返回值
    mock_client.interrupt.return_value = {"detail": "Interrupted"}

    # upload_image 方法默认返回值
    mock_client.upload_image.return_value = {"name": "test_image.png"}

    yield mock_client


@pytest.fixture
def mock_queue_status_data():
    """
    提供测试用的队列状态数据
    """
    return {
        "queue_running": [
            [1, "running-prompt-1", 1234567890],
            [2, "running-prompt-2", 1234567891],
        ],
        "queue_pending": [
            [3, "pending-prompt-1", 1234567892],
            [4, "pending-prompt-2", 1234567893],
        ]
    }


@pytest.fixture
def mock_history_data():
    """
    提供测试用的历史记录数据
    """
    return {
        "test-prompt-id": {
            "prompt": [1, "test workflow"],
            "outputs": {"1": "test output"}
        }
    }


@pytest.fixture
def mock_workflow_data():
    """
    提供测试用的工作流数据
    """
    return {
        "1": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 123456789,
                "steps": 20,
                "cfg": 7,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1
            }
        }
    }


# ============ 图片测试 Fixtures ============


@pytest.fixture
def mock_image_content():
    """
    提供测试用的图片二进制数据
    """
    # 返回一个最小 PNG 图片的二进制数据
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"


@pytest.fixture
def mock_upload_file(mock_image_content):
    """
    创建 mock UploadFile 对象
    """
    from fastapi import UploadFile
    from io import BytesIO

    file = MagicMock(spec=UploadFile)
    file.filename = "test_image.png"
    file.content_type = "image/png"
    file.read = AsyncMock(return_value=mock_image_content)
    return file



# ============ 测试数据 Fixtures ============


@pytest.fixture
def valid_workflow_submit_request():
    """
    有效的工作流提交请求
    """
    return {
        "workflow": {
            "1": {
                "class_type": "KSampler",
                "inputs": {"seed": 123456789}
            }
        },
        "client_id": "test-client-1"
    }


@pytest.fixture
def valid_cpu_quickly_request():
    """
    有效的 CPU Quickly 场景请求
    """
    return {
        "prompt": "a beautiful landscape",
        "negative_prompt": "ugly, blurry",
        "input_image": "test_input.png"
    }


@pytest.fixture
def valid_clear_queue_request():
    """
    有效的清空队列请求
    """
    return {"clear": True}


@pytest.fixture
def valid_interrupt_request():
    """
    有效的中断工作流请求
    """
    return {"prompt_id": "test-prompt-id-123"}


# ============ 依赖覆盖 Helper ============


@pytest.fixture
def comfyui_client_override(app, mock_comfyui_client):
    """
    提供依赖覆盖的上下文管理器

    用法:
        with comfyui_client_override:
            # 测试代码
            response = client.get("/api/v1/queue/status")
    """
    from app.internal import comfyui as comfyui_module

    original_client = comfyui_module.comfyui_client

    class _OverrideContext:
        def __enter__(self):
            comfyui_module.comfyui_client = mock_comfyui_client
            return mock_comfyui_client

        def __exit__(self, *args):
            comfyui_module.comfyui_client = original_client

    return _OverrideContext()


# ============ 异步事件循环 Fixture ============


@pytest.fixture
def event_loop():
    """
    创建事件循环用于异步测试
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============ 参数化测试数据 ============


@pytest.fixture(params=[
    ("test-id-1", 200),
    ("test-id-2", 200),
    ("non-existent", 404),
])
def history_test_cases(request):
    """
    历史记录测试用例参数化
    """
    return request.param
