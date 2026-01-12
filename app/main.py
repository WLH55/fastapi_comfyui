"""
FastAPI 应用主入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings, ensure_directories
from app.routers import (
    workflows_router,
    queue_router,
    images_router,
    websocket_router,
    scenarios_router,
)
from app.schemas import ApiResponse, ResponseCode
from app.exceptions import ComfyUIException


# ========== 全局异常处理器 ==========

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理 HTTP 异常

    返回格式: {code, message, data: null}
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(
            code=exc.status_code,
            message=exc.detail,
            data=None
        ).dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理请求验证异常

    返回格式: {code, message, data: null}
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ApiResponse.error(
            code=ResponseCode.VALIDATION_ERROR,
            message="请求参数验证失败",
            data=None
        ).dict()
    )


async def comfyui_exception_handler(request: Request, exc: ComfyUIException):
    """
    处理 ComfyUI 业务异常

    返回格式: {code, message, data: null}
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.error(
            code=getattr(exc, "code", ResponseCode.INTERNAL_ERROR),
            message=exc.message,
            data=None
        ).dict()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常

    返回格式: {code, message, data: null}
    """
    import traceback

    # 打印异常堆栈
    traceback.print_exc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message="服务器内部错误",
            data=None
        ).dict()
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    ensure_directories()
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[COMFYUI] {settings.COMFYUI_BASE_URL}")
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

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ComfyUIException, comfyui_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

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
    app.include_router(websocket_router, prefix=settings.API_PREFIX)

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
