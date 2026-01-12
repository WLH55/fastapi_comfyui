"""
队列领域路由

队列 API 路由定义
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from src.queue.schemas import QueueStatusResponse, QueueClearRequest
from src.queue.service import (
    get_queue_status,
    get_running_tasks,
    get_pending_tasks,
    clear_queue,
)
from src.exceptions import ComfyUIConnectionError, QueueOperationError


# 创建路由器
router = APIRouter(prefix="/queue", tags=["queue"])


@router.get(
    "/status",
    response_model=QueueStatusResponse,
    summary="获取队列状态",
    description="获取当前队列的运行中和等待中的任务",
)
async def get_queue_status_endpoint() -> QueueStatusResponse:
    """
    获取队列状态
    """
    try:
        # 获取队列状态
        queue = await get_queue_status()

        # 转换为标准格式
        running_tasks = []
        for item in queue.get("queue_running", []):
            if len(item) >= 3:
                running_tasks.append({
                    "prompt_id": item[0],
                    "number": item[1],
                    "timestamp": item[2]
                })

        pending_tasks = []
        for item in queue.get("queue_pending", []):
            if len(item) >= 3:
                pending_tasks.append({
                    "prompt_id": item[0],
                    "number": item[1],
                    "timestamp": item[2]
                })

        return QueueStatusResponse(
            queue_running=running_tasks,
            queue_pending=pending_tasks,
            running_count=len(running_tasks),
            pending_count=len(pending_tasks)
        )

    except ComfyUIConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": e.code,
                "message": e.message
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"获取队列状态失败: {str(e)}"
            }
        )


@router.post(
    "/clear",
    summary="清空队列",
    description="清空当前队列中的所有任务",
)
async def clear_queue_endpoint(request: QueueClearRequest) -> Dict[str, Any]:
    """
    清空队列
    """
    try:
        if request.clear:
            result = await clear_queue()
            return {
                "success": True,
                "message": "队列已清空",
                "detail": result
            }
        else:
            return {
                "success": False,
                "message": "未执行清空操作"
            }

    except ComfyUIConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": e.code,
                "message": e.message
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"清空队列失败: {str(e)}"
            }
        )
