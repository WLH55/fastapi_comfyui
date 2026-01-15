"""
FastAPI 应用主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.config import settings, ensure_directories
from app.logger_config import setup_logging
from app.routers import (
    workflows_router,
    queue_router,
    images_router,
    scenarios_router,
)
from app.exceptions import register_exception_handlers



@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    ensure_directories()
    setup_logging()  # 初始化日志系统
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[COMFYUI] {settings.COMFYUI_BASE_URL}")
    print(f"[LOGS] 访问日志目录: {settings.ACCESS_LOG_DIR}")
    yield
    print(f"[STOP] {settings.APP_NAME} shutdown")



def create_app() -> FastAPI:
    """创建应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        FastAPI ComfyUI 服务 - ComfyUI 接口封装

        ## 统一响应格式

        所有接口返回格式:
        ```json
        {
            "code": 200,
            "message": "success",
            "data": {...}
        }
        ```

        ## 场景化 API

        * **CPU Quickly**: `POST /api/v1/scenarios/cpu_quickly`

        ## 高级 API

        * **工作流**: 直接提交 ComfyUI workflow
        * **队列**: 查询和管理队列
        * **图片**: 上传和下载图片

        ## API 文档

        * Swagger UI: `/docs`
        * ReDoc: `/redoc`
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # ========== 注册全局异常处理器 ==========
    register_exception_handlers(app)

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    # 根路由
    @app.get("/", tags=["root"])
    async def root():
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "healthy"}

    # 注册路由
    app.include_router(scenarios_router, prefix=settings.API_PREFIX)
    app.include_router(workflows_router, prefix=settings.API_PREFIX)
    app.include_router(queue_router, prefix=settings.API_PREFIX)
    app.include_router(images_router, prefix=settings.API_PREFIX)


    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
