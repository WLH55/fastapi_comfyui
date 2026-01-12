"""
队列领域服务

队列业务逻辑层
"""

from typing import Dict, Any, List

from src.config import settings
from src.exceptions import ComfyUIConnectionError
from src.services import get_json, post_json
from src.queue.constants import ComfyUIAPIPath


async def get_queue_status() -> Dict[str, Any]:
    """
    获取队列状态

    Returns:
        队列状态字典，包含 queue_running 和 queue_pending

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.QUEUE}"
    return await get_json(url)


async def get_running_tasks() -> List[Dict[str, Any]]:
    """
    获取正在运行的任务列表

    Returns:
        正在运行的任务列表
    """
    queue = await get_queue_status()
    running = queue.get("queue_running", [])

    # 转换为统一格式
    result = []
    for item in running:
        # item 格式: [prompt_id, number, timestamp]
        if len(item) >= 3:
            result.append({
                "prompt_id": item[0],
                "number": item[1],
                "timestamp": item[2]
            })

    return result


async def get_pending_tasks() -> List[Dict[str, Any]]:
    """
    获取等待中的任务列表

    Returns:
        等待中的任务列表
    """
    queue = await get_queue_status()
    pending = queue.get("queue_pending", [])

    # 转换为统一格式
    result = []
    for item in pending:
        # item 格式: [prompt_id, number, timestamp]
        if len(item) >= 3:
            result.append({
                "prompt_id": item[0],
                "number": item[1],
                "timestamp": item[2]
            })

    return result


async def is_task_in_queue(prompt_id: str) -> bool:
    """
    检查任务是否在队列中

    Args:
        prompt_id: 任务 ID

    Returns:
        是否在队列中
    """
    running = await get_running_tasks()
    pending = await get_pending_tasks()

    running_ids = [task["prompt_id"] for task in running]
    pending_ids = [task["prompt_id"] for task in pending]

    return prompt_id in running_ids or prompt_id in pending_ids


async def get_queue_count() -> Dict[str, int]:
    """
    获取队列任务数量

    Returns:
        包含 running_count 和 pending_count 的字典
    """
    running = await get_running_tasks()
    pending = await get_pending_tasks()

    return {
        "running_count": len(running),
        "pending_count": len(pending)
    }


async def clear_queue() -> Dict[str, Any]:
    """
    清空队列

    Returns:
        清空结果

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.QUEUE}"
    return await post_json(url, {"clear": True})


async def delete_from_queue(prompt_id: str) -> Dict[str, Any]:
    """
    从队列中删除指定任务

    Args:
        prompt_id: 任务 ID

    Returns:
        删除结果

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.QUEUE}"
    return await post_json(url, {"delete": [prompt_id]})
