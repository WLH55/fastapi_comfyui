"""
队列路由
"""
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from app.internal.comfyui import comfyui_client
from app.exceptions import ComfyUIConnectionError
from app.schemas import ApiResponse, ResponseCode


router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/status", summary="获取队列状态", response_model=ApiResponse)
async def get_queue_status() -> ApiResponse:
    """
    获取当前队列状态

    返回正在运行和等待中的任务列表
    """
    try:
        queue = await comfyui_client.get_queue_status()

        running = [
            {"prompt_id": item[1], "number": item[0], "timestamp": item[2]}
            for item in queue.get("queue_running", []) if len(item) >= 3
        ]
        pending = [
            {"prompt_id": item[1], "number": item[0], "timestamp": item[2]}
            for item in queue.get("queue_pending", []) if len(item) >= 3
        ]

        return ApiResponse.success(
            data={
                "queue_running": running,
                "queue_pending": pending,
                "running_count": len(running),
                "pending_count": len(pending)
            },
            message="获取队列状态成功"
        )

    except ComfyUIConnectionError as e:
        return ApiResponse.error(
            code=e.code,
            message=e.message
        )


@router.post("/clear", summary="清空队列", response_model=ApiResponse)
async def clear_queue(request: Dict[str, Any]) -> ApiResponse:
    """
    清空队列

    请求体:
    ```json
    {
        "clear": true
    }
    ```
    """
    try:
        if request.get("clear"):
            result = await comfyui_client.clear_queue()
            return ApiResponse.success(
                data={"detail": result},
                message="队列已清空"
            )
        return ApiResponse.error(
            code=ResponseCode.BAD_REQUEST,
            message="未执行清空"
        )
    except Exception as e:
        return ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"清空队列失败: {str(e)}"
        )
