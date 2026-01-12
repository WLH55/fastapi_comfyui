"""
FastAPI 应用主入口

项目根文件，负责应用初始化、路由注册、全局异常捕获与日志路由
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings, ensure_directories

# 导入领域路由
from src.workflows.router import router as workflows_router
from src.queue.router import router as queue_router
from src.images.router import router as images_router
from src.websocket.router import router as websocket_router
from src.scenarios.router import router as scenarios_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    负责应用启动和关闭时的初始化和清理工作
    """
    # 启动时执行
    ensure_directories()
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[INPUT]  {settings.INPUT_DIR}")
    print(f"[OUTPUT] {settings.OUTPUT_DIR}")
    print(f"[COMFYUI] {settings.COMFYUI_BASE_URL}")

    yield

    # 关闭时执行
    print(f"[STOP] {settings.APP_NAME} shutdown")


def create_app() -> FastAPI:
    """
    应用工厂函数

    创建并配置 FastAPI 应用实例

    Returns:
        FastAPI: 配置好的应用实例
    """

    # 创建应用实例
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        FastAPI ComfyUI 服务

        提供 ComfyUI 工作流的 HTTP API 和 WebSocket 接口。

        ## 主要功能

        * **场景化封装**: 简化的场景 API（text2img, img2img）
        * **模板管理**: 上传和管理 workflow 模板
        * **工作流管理**: 提交、查询、中断工作流
        * **队列管理**: 查询队列状态、清空队列
        * **图片处理**: 上传输入图片、下载生成图片
        * **实时通信**: WebSocket 实时推送执行进度

        ## 快速开始

        ### 文生图场景
        ```bash
        POST /api/v1/scenarios/text2img
        {
          "prompt": "a beautiful landscape",
          "width": 1024,
          "height": 1024
        }
        ```

        ### 上传自定义模板
        ```bash
        POST /api/v1/scenarios/templates/upload
        ```

        ## API 文档

        * Swagger UI: `/docs`
        * ReDoc: `/redoc`
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    # ========== 注册根路由 ==========

    @app.get("/", tags=["root"])
    async def root() -> dict:
        """根路径，返回服务基本信息"""
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
            "comfyui": settings.COMFYUI_BASE_URL,
        }

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
        }

    # ========== 注册领域路由 ==========

    # 场景化封装路由
    app.include_router(
        scenarios_router,
        prefix=settings.API_PREFIX,
    )

    # 工作流路由
    app.include_router(
        workflows_router,
        prefix=settings.API_PREFIX,
    )

    # 队列路由
    app.include_router(
        queue_router,
        prefix=settings.API_PREFIX,
    )

    # 图片路由
    app.include_router(
        images_router,
        prefix=settings.API_PREFIX,
    )

    # WebSocket 路由（不使用 API 前缀）
    app.include_router(
        websocket_router,
        prefix=settings.API_PREFIX,
    )

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # 开发环境运行服务器
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
