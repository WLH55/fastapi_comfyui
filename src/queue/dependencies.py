"""
队列领域依赖项

定义队列路由的依赖项
"""

from typing import Optional
from fastapi import Header, HTTPException


async def validate_clear_request(
    x_confirm: Optional[str] = Header(None)
) -> dict:
    """
    验证清空队列请求

    Args:
        x_confirm: 确认头

    Returns:
        验证上下文字典
    """
    return {
        "confirm": x_confirm == "true",
        "validated": True
    )


def parse_queue_item(raw_item: list) -> dict:
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
