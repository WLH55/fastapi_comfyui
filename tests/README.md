# 测试文档

## 项目概述

本项目采用 Pytest 进行测试，使用 FastAPI TestClient 进行接口测试，通过 Mock 模拟 ComfyUI 客户端。

---

## 测试架构

```
tests/
├── conftest.py              # Pytest 配置和共享 fixtures
├── test_exceptions.py       # 异常处理器测试
├── test_schemas.py          # 响应模型测试
├── test_workflows.py        # 工作流路由测试
├── test_queue.py            # 队列路由测试
├── test_images.py           # 图片路由测试
├── test_scenarios.py        # 场景路由测试
└── test_main.py             # 应用主入口测试
```

---

## 测试分层

### 1. 单元测试层

#### test_exceptions.py
测试全局异常处理器的正确性：

| 测试类 | 测试内容 |
|--------|----------|
| `TestHTTPExceptionHandler` | HTTPException 处理，验证返回统一响应格式 |
| `TestValidationExceptionHandler` | RequestValidationError 处理（422错误） |
| `TestComfyUIExceptionHandler` | 5种自定义业务异常处理（1001-1007错误码） |
| `TestGeneralExceptionHandler` | 未捕获异常的处理（500错误） |

#### test_schemas.py
测试响应模型的正确性：

| 测试类 | 测试内容 |
|--------|----------|
| `TestApiResponse` | success() / error() 方法，模型序列化 |
| `TestResponseCode` | 响应码常量定义完整性 |

---

### 2. 集成测试层

#### test_workflows.py
测试 `/api/v1/workflows/*` 接口：

| 接口 | 测试场景 |
|------|----------|
| `POST /submit` | 成功提交、带client_id、空workflow、连接错误、复杂workflow、并发请求 |
| `GET /{prompt_id}/history` | 成功获取、不存在（404）、空历史、参数化测试 |
| `POST /interrupt` | 成功中断、无prompt_id、中断失败异常 |

#### test_queue.py
测试 `/api/v1/queue/*` 接口：

| 接口 | 测试场景 |
|------|----------|
| `GET /status` | 成功获取、空队列、格式错误数据过滤、连接错误、大队列、特殊字符、时间戳 |
| `POST /clear` | 成功清空、clear=false验证、无clear字段、清空异常、参数化测试 |
| `POST /delete` | 成功删除、多个prompt_id、空列表、连接错误、删除不存在的项 |

#### test_images.py
测试 `/api/v1/images/*` 接口：

| 接口 | 测试场景 |
|------|----------|
| `POST /upload` | 成功上传、overwrite参数、非图片文件拒绝、无content_type、连接错误、通用异常、不同图片类型、大文件、特殊字符文件名、并发上传、空文件 |
| `GET /download` | 成功下载、带subfolder、input类型、参数化测试、特殊字符文件名、不存在的文件、不同扩展名推断content-type |

#### test_scenarios.py
测试 `/api/v1/scenarios/*` 接口：

| 接口 | 测试场景 |
|------|----------|
| `POST /cpu_quickly` | 成功执行、带负面提示词、无负面提示词、缺少必填字段、模板不存在、提交异常、各种提示词、特殊字符、emoji、参数验证、workflow参数应用、并发请求 |

---

### 3. 专项测试

所有测试文件中均包含以下专项测试：

| 专项类型 | 覆盖内容 |
|----------|----------|
| 并发测试 | 使用 threading 模拟多线程并发请求 |
| 特殊字符 | 中文、Unicode、空格、换行符 |
| Emoji | 表情符号处理 |
| 超长数据 | 长字符串、大文件 |
| 边界条件 | 空值、None、空列表、空字典 |

---

## 测试覆盖清单

### 响应格式验证
- [ ] 所有接口返回统一 `ApiResponse` 格式（code/message/data）
- [ ] 成功响应 code=200
- [ ] 业务异常返回对应业务错误码
- [ ] HTTP异常返回对应HTTP状态码

### 异常场景覆盖
- [ ] `ComfyUIConnectionError` (1001)
- [ ] `WorkflowValidationError` (1002)
- [ ] `QueueOperationError` (1003)
- [ ] `FileOperationError` (1004)
- [ ] `ImageNotFoundError` (404)

### 参数验证覆盖
- [ ] Pydantic 验证失败返回 422
- [ ] 必填字段缺失
- [ ] 类型错误
- [ ] 额外字段处理

---

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_workflows.py

# 运行特定测试类
pytest tests/test_workflows.py::TestWorkflowsSubmit

# 运行特定测试方法
pytest tests/test_workflows.py::TestWorkflowsSubmit::test_submit_workflow_success

# 显示详细输出
pytest -v

# 显示覆盖率
pytest --cov=app --cov-report=html
```

---

## 编写测试指南

### 测试命名规范

```python
class Test<模块名><功能名>:
    """测试描述"""

    def test_<场景>_<条件>_<期望结果>(self, ...):
        """
        测试描述

        验证点:
        - 验证点1
        - 验证点2
        """
```

### 测试结构模板

```python
class TestExample:
    """测试示例"""

    def test_success_case(self, client, mock_comfyui_client):
        """
        测试成功场景

        验证点:
        - 状态码正确
        - 响应格式正确
        - 数据内容正确
        """
        # Arrange
        mock_comfyui_client.method.return_value = expected_data

        # Act
        with patch("path.to.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/endpoint", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "期望消息"
        assert data["data"]["key"] == expected_value
        mock_comfyui_client.method.assert_called_once_with(args)

    def test_exception_case(self, client, mock_comfyui_client):
        """
        测试异常场景

        验证点:
        - 异常被正确处理
        - 返回正确的错误码和消息
        """
        from app.exceptions import SomeException

        mock_comfyui_client.method.side_effect = SomeException("错误消息")

        with patch("path.to.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/endpoint", json={})

        assert response.status_code == 200  # 业务异常仍返回200
        data = response.json()
        assert data["code"] == ExpectedErrorCode
        assert "错误" in data["message"]
```

### Mock 使用规范

```python
# 1. 使用 fixtures 中提供的 mock_comfyui_client
def test_example(self, client, mock_comfyui_client):
    mock_comfyui_client.method.return_value = expected_value

    # 2. 使用 patch 覆盖依赖
    with patch("app.routers.module.comfyui_client", mock_comfyui_client):
        response = client.post("/api/v1/endpoint")

    # 3. 验证调用
    mock_comfyui_client.method.assert_called_once_with(expected_args)
```

---

## 测试数据 Fixtures

conftest.py 提供以下共享 fixtures：

| Fixture | 说明 |
|---------|------|
| `app` | FastAPI 测试应用实例 |
| `client` | TestClient 实例 |
| `mock_comfyui_client` | Mock 的 ComfyUI 客户端 |
| `mock_queue_status_data` | 队列状态测试数据 |
| `mock_history_data` | 历史记录测试数据 |
| `mock_workflow_data` | 工作流测试数据 |
| `mock_image_content` | 图片二进制数据 |
| `valid_*_request` | 各接口有效请求数据 |

---

## 当前测试状态

| 文件 | 状态 | 待办事项 |
|------|------|----------|
| `conftest.py` | ✅ 可用 | - |
| `test_workflows.py` | ✅ 可用 | 增强异常覆盖 |
| `test_queue.py` | ⚠️ 有语法错误 | **修复 true/True**，**补充 /delete 测试** |
| `test_images.py` | ⚠️ 测试不存在接口 | **重写**，改为测试 /download |
| `test_scenarios.py` | ✅ 可用 | 增强 |
| `test_exceptions.py` | ❌ 不存在 | **新增** |
| `test_schemas.py` | ❌ 不存在 | **新增** |
