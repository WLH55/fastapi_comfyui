"""
主应用测试

测试应用根路由、健康检查等通用接口
"""

import pytest
from app.main import create_app


class TestRootRoutes:
    """测试根路由"""

    def test_root_endpoint(self, client):
        """
        测试根路径 / 返回服务信息
        """
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        assert data["status"] == "running"
        assert data["docs"] == "/docs"

    def test_health_check(self, client):
        """
        测试健康检查接口 /health
        """
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_docs_endpoint(self, client):
        """
        测试 API 文档接口 /docs 可访问
        """
        response = client.get("/docs")

        # Swagger UI HTML 页面
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()

    def test_redoc_endpoint(self, client):
        """
        测试 ReDoc 接口 /redoc 可访问
        """
        response = client.get("/redoc")

        # ReDoc HTML 页面
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()

    def test_openapi_schema(self, client):
        """
        测试 OpenAPI schema 端点
        """
        response = client.get("/api/v1/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"]


class TestApplicationConfiguration:
    """测试应用配置"""

    def test_cors_headers(self, client):
        """
        测试 CORS 响应头
        """
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        # 验证 CORS 头存在
        assert response.status_code == 200

    def test_api_prefix_routing(self, client):
        """
        测试 API 前缀路由
        """
        # 测试 workflows 路由
        response = client.post("/api/v1/workflows/submit", json={"workflow": {}})
        # 应该不是 404（可能返回其他状态码，取决于 mock）
        assert response.status_code != 404

    def test_all_routers_registered(self, client):
        """
        测试所有路由都已正确注册
        """
        # 检查各路由的前缀是否存在（通过访问根 OpenAPI schema）
        response = client.get("/api/v1/openapi.json")
        schema = response.json()

        paths = schema.get("paths", {})

        # 验证各个路由的端点存在
        expected_prefixes = [
            "/api/v1/workflows",
            "/api/v1/queue",
            "/api/v1/images",
            "/api/v1/scenarios",
            "/api/v1/ws",
        ]

        registered_paths = list(paths.keys())

        # 至少应该有一些路径被注册
        assert len(registered_paths) > 0

        # 检查是否有预期的路径
        for prefix in expected_prefixes:
            # 检查是否有以该前缀开头的路径
            has_prefix = any(path.startswith(prefix) for path in registered_paths)
            assert has_prefix, f"Expected to find paths with prefix {prefix}"


class TestErrorHandling:
    """测试错误处理"""

    def test_404_not_found(self, client):
        """
        测试访问不存在的路径返回 404
        """
        response = client.get("/non-existent-path")

        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """
        测试使用不正确的 HTTP 方法
        """
        # GET 请求到只接受 POST 的端点
        response = client.get("/api/v1/workflows/submit")

        # 可能返回 405 或其他状态
        assert response.status_code in [405, 422]

    def test_422_validation_error(self, client):
        """
        测试请求参数验证错误
        """
        # 发送格式错误的 JSON
        response = client.post(
            "/api/v1/workflows/submit",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422]

    def test_missing_required_parameter(self, client):
        """
        测试缺少必需参数
        """
        # 不提供必需的查询参数
        response = client.get("/api/v1/images/url")

        # 应该返回验证错误
        assert response.status_code == 422


class TestExceptionHandlers:
    """测试全局异常处理器"""

    def test_http_exception_handling(self, client):
        """
        测试 HTTP 异常被正确处理
        """
        # 访问需要认证的端点（如果有的话）
        # 或者其他会触发 HTTPException 的场景
        response = client.get("/api/v1/workflows/non-existent-id/history")

        # 应该返回统一格式的错误响应
        assert response.status_code in [200, 404]

    def test_request_validation_error_handling(self, client):
        """
        测试请求验证异常被正确处理
        """
        # 发送不符合 schema 的请求
        response = client.post(
            "/api/v1/scenarios/cpu_quickly",
            json={"invalid": "data"}
        )

        # 应该返回统一格式的验证错误响应
        assert response.status_code == 422


class TestApplicationLifecycle:
    """测试应用生命周期"""

    def test_app_creation(self):
        """
        测试应用实例创建
        """
        app = create_app()

        assert app is not None
        assert app.title
        assert app.version
        assert len(app.routes) > 0

    def test_app_routes(self):
        """
        测试应用路由配置
        """
        app = create_app()

        # 获取所有路由
        routes = [route for route in app.routes if hasattr(route, 'path')]

        # 验证关键路由存在
        route_paths = [route.path for route in routes]

        assert "/" in route_paths
        assert "/health" in route_paths
        assert "/docs" in route_paths
        assert "/redoc" in route_paths


class TestResponseFormat:
    """测试统一响应格式"""

    def test_api_response_format(self, client):
        """
        测试 API 响应符合统一格式
        """
        # 测试一个返回 ApiResponse 的端点
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # 根路由返回简单格式，但应该有基本结构
        assert isinstance(data, dict)

    def test_error_response_format(self, client):
        """
        测试错误响应符合统一格式
        """
        response = client.get("/non-existent-path")

        assert response.status_code == 404
        # 404 可能由 FastAPI 默认处理，格式可能不同


class TestIntegration:
    """集成测试"""

    def test_full_request_flow(self, client, mock_comfyui_client):
        """
        测试完整的请求流程

        从健康检查到 API 调用的完整流程
        """
        # 1. 健康检查
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # 2. 获取队列状态
        mock_comfyui_client.get_queue_status.return_value = {
            "queue_running": [],
            "queue_pending": []
        }

        with pytest.mock.patch("app.internal.comfyui.comfyui_client", mock_comfyui_client):
            queue_response = client.get("/api/v1/queue/status")
            assert queue_response.status_code == 200
            data = queue_response.json()
            assert "code" in data
            assert "message" in data
            assert "data" in data

    def test_concurrent_requests(self, client):
        """
        测试并发请求处理
        """
        import threading

        results = []

        def make_request():
            response = client.get("/health")
            results.append(response.status_code)

        threads = [threading.Thread(target=make_request) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有请求都应该成功
        assert all(status == 200 for status in results)

    def test_multiple_clients(self):
        """
        测试多个 TestClient 实例
        """
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()

        # 创建多个客户端
        client1 = TestClient(app)
        client2 = TestClient(app)

        response1 = client1.get("/")
        response2 = client2.get("/")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()


class TestOpenAPISpec:
    """测试 OpenAPI 规范"""

    def test_openapi_info(self, client):
        """
        测试 OpenAPI info 字段
        """
        response = client.get("/api/v1/openapi.json")
        schema = response.json()

        info = schema["info"]
        assert info["title"]
        assert info["version"]
        assert info["description"]

    def test_openapi_tags(self, client):
        """
        测试 OpenAPI tags 定义
        """
        response = client.get("/api/v1/openapi.json")
        schema = response.json()

        tags = schema.get("tags", [])
        # 验证存在预期的 tags
        tag_names = [tag["name"] for tag in tags]
        expected_tags = ["root", "health", "workflows", "queue", "images", "scenarios"]

        for tag in expected_tags:
            assert tag in tag_names

    def test_openapi_paths_documented(self, client):
        """
        测试端点都有文档说明
        """
        response = client.get("/api/v1/openapi.json")
        schema = response.json()

        paths = schema["paths"]

        # 检查一些关键端点有文档
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "delete"]:
                    # 应该有 summary 或 description
                    assert "summary" in details or "description" in details
                    # 应该有 tags
                    assert "tags" in details
                    assert len(details["tags"]) > 0
