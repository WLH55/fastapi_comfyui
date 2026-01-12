"""
时间处理服务

负责时间相关的转换和格式化操作
"""

import time
from datetime import datetime
from typing import Optional


def get_current_timestamp() -> int:
    """
    获取当前时间戳（秒）

    Returns:
        当前时间戳
    """
    return int(time.time())


def get_current_datetime() -> datetime:
    """
    获取当前日期时间

    Returns:
        当前日期时间对象
    """
    return datetime.now()


def format_datetime(dt: datetime, format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    格式化日期时间

    Args:
        dt: 日期时间对象
        format_str: 格式字符串

    Returns:
        格式化后的字符串
    """
    return dt.strftime(format_str)


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    时间戳转日期时间

    Args:
        timestamp: 时间戳（秒）

    Returns:
        日期时间对象
    """
    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    日期时间转时间戳

    Args:
        dt: 日期时间对象

    Returns:
        时间戳（秒）
    """
    return int(dt.timestamp())


def calculate_elapsed_seconds(start_timestamp: int) -> int:
    """
    计算经过的秒数

    Args:
        start_timestamp: 开始时间戳

    Returns:
        经过的秒数
    """
    return get_current_timestamp() - start_timestamp


def is_timeout(start_timestamp: int, timeout_seconds: int) -> bool:
    """
    判断是否超时

    Args:
        start_timestamp: 开始时间戳
        timeout_seconds: 超时秒数

    Returns:
        是否超时
    """
    return calculate_elapsed_seconds(start_timestamp) > timeout_seconds
