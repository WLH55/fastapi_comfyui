"""
路由模块

包含所有 API 路由
"""

from app.routers.workflows import router as workflows_router
from app.routers.queue import router as queue_router
from app.routers.images import router as images_router
from app.routers.websocket import router as websocket_router
from app.routers.scenarios import router as scenarios_router

__all__ = [
    "workflows_router",
    "queue_router",
    "images_router",
    "websocket_router",
    "scenarios_router",
]
