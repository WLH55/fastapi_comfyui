"""
队列领域工具函数

定义队列模块的非业务逻辑函数
"""

from typing import Dict, Any, List


def format_queue_status(queue_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化队列状态数据

    Args:
        queue_data: 原始队列数据

    Returns:
        格式化后的队列数据
    """
    running = queue_data.get("queue_running", [])
    pending = queue_data.get("queue_pending", [])

    return {
        "queue_running": [parse_queue_item(item) for item in running],
        "queue_pending": [parse_queue_item(item) for item in pending],
        "running_count": len(running),
        "pending_count": len(pending)
    }


def parse_queue_item(raw_item: list) -> Dict[str, Any]:
    """
    解析队列项

    Args:
        raw_item: 原始队列项 [prompt_id, number, timestamp]

    Returns:
        解析后的队列项字典
    """
    if len(raw_item) >= 3:
        return {
            "prompt_id": raw_item[0],
            "number": raw_item[1],
            "timestamp": raw_item[2]
        }
    return {}


def find_task_in_queue(queue_data: Dict[str, Any], prompt_id: str) -> bool:
    """
    在队列中查找任务

    Args:
        queue_data: 队列数据
        prompt_id: 任务 ID

    Returns:
        是否找到
    """
    running = queue_data.get("queue_running", [])
    pending = queue_data.get("queue_pending", [])

    for item in running + pending:
        if len(item) >= 3 and item[0] == prompt_id:
            return True

    return False


def calculate_queue_position(queue_data: Dict[str, Any], prompt_id: str) -> int:
    """
    计算任务在队列中的位置

    Args:
        queue_data: 队列数据
        prompt_id: 任务 ID

    Returns:
        队列位置（0 表示正在执行，>0 表示等待位置）
    """
    running = queue_data.get("queue_running", [])
    pending = queue_data.get("queue_pending", [])

    # 检查是否在运行中
    for i, item in enumerate(running):
        if len(item) >= 3 and item[0] == prompt_id:
            return 0

    # 检查是否在等待中
    for i, item in enumerate(pending):
        if len(item) >= 3 and item[0] == prompt_id:
            return i + 1

    return -1
