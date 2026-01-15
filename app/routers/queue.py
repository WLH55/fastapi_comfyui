"""
队列路由
"""
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.internal.comfyui import comfyui_client
from app.schemas import ApiResponse


router = APIRouter(prefix="/queue", tags=["queue"])


# ========== 请求模型 ==========


class DeleteQueueRequest(BaseModel):
    """删除队列项请求"""
    delete: List[str]


# ========== 队列接口 ==========


@router.get("/status", summary="获取队列状态", response_model=ApiResponse)
async def get_queue_status() -> ApiResponse:
    """
    获取当前队列状态

    返回正在运行和等待中的任务列表
    """
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


@router.get("/clear", summary="清空队列", response_model=ApiResponse)
async def clear_queue() -> ApiResponse:
    """
    清空整个队列
    """
    result = await comfyui_client.clear_queue({"clear": True})
    return ApiResponse.success(
        data=result,
        message="队列已清空"
    )


@router.post("/delete", summary="删除队列项", response_model=ApiResponse)
async def delete_queue_items(request: DeleteQueueRequest) -> ApiResponse:
    """
    删除指定的队列项

    请求体:
    ```json
    {
        "delete": ["prompt_id1", "prompt_id2"]
    }
    ```
    """
    result = await comfyui_client.clear_queue({"delete": request.delete})
    return ApiResponse.success(
        data=result,
        message=f"{request.delete}删除成功"
    )
