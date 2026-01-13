# FastAPI ComfyUI 测试套件

本项目使用 pytest 框架进行测试，覆盖所有 HTTP 接口和 WebSocket 连接。

## 测试文件结构

```
tests/
├── __init__.py           # 测试模块初始化
├── conftest.py           # pytest 配置和共享 fixtures
├── test_main.py          # 主应用测试（根路由、健康检查等）
├── test_workflows.py     # 工作流路由测试
├── test_queue.py         # 队列路由测试
├── test_images.py        # 图片路由测试
├── test_scenarios.py     # 场景路由测试
└── test_websocket.py     # WebSocket 路由测试
```

## 安装依赖

```bash
pip install pytest pytest-asyncio pytest-cov
```

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定测试文件
```bash
pytest tests/test_workflows.py
```

### 运行特定测试类
```bash
pytest tests/test_workflows.py::TestWorkflowsSubmit
```

### 运行特定测试方法
```bash
pytest tests/test_workflows.py::TestWorkflowsSubmit::test_submit_workflow_success
```

### 显示详细输出
```bash
pytest -v
```

### 显示打印输出
```bash
pytest -s
```

## 测试覆盖率

### 生成覆盖率报告
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

覆盖率报告将生成在 `htmlcov/index.html`

### 仅查看终端覆盖率
```bash
pytest --cov=app --cov-report=term
```

## 测试覆盖范围

| 测试文件 | 覆盖路由 | 测试数量 |
|---------|---------|---------|
| `test_main.py` | `/`, `/health` | ~20 |
| `test_workflows.py` | `/api/v1/workflows/*` | ~15 |
| `test_queue.py` | `/api/v1/queue/*` | ~12 |
| `test_images.py` | `/api/v1/images/*` | ~15 |
| `test_scenarios.py` | `/api/v1/scenarios/*` | ~12 |
| `test_websocket.py` | `/api/v1/ws/*` | ~20 |

## Fixtures 说明

主要 fixtures 定义在 `conftest.py` 中：

- `app` - FastAPI 应用实例（跳过 lifespan 初始化）
- `client` - TestClient 实例
- `mock_comfyui_client` - Mock 的 ComfyUI 客户端
- `mock_image_content` - 测试用图片二进制数据
- `valid_workflow_submit_request` - 有效的工作流提交请求
- 等更多...

## WebSocket 测试

WebSocket 测试使用 TestClient 的 `websocket_connect` 方法：

```python
with client.websocket_connect(f"/api/v1/ws/{client_id}") as websocket:
    data = websocket.receive_json()
    assert data["type"] == "connected"
```

## Mock 策略

所有 ComfyUI 客户端调用都被 mock，因此测试不需要真实的 ComfyUI 服务：

```python
with patch("app.internal.comfyui.comfyui_client", mock_comfyui_client):
    response = client.post("/api/v1/workflows/submit", json=request_data)
```

## 参数化测试

使用 `@pytest.mark.parametrize` 进行多场景测试：

```python
@pytest.mark.parametrize("prompt_id,expected_code", [
    ("valid-id", 200),
    ("not-found", 404),
])
def test_get_history_parametrized(client, prompt_id, expected_code):
    response = client.get(f"/api/v1/workflows/{prompt_id}/history")
    assert response.status_code == expected_code
```

## 注意事项

1. **异步测试** - 使用 AsyncMock 处理异步函数
2. **文件上传** - 使用 BytesIO 模拟文件上传
3. **WebSocket** - 测试后连接会自动关闭
4. **依赖注入** - 使用 patch 替换 comfyui_client

## 持续集成

在 CI/CD 中运行测试：

```bash
# 运行测试并生成覆盖率
pytest --cov=app --cov-fail-under=80
```
