"""
WebSocket 领域工具函数

定义 WebSocket 模块的非业务逻辑函数
"""

from typing import Dict, Any
from enum import Enum


def format_websocket_message(message_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化 WebSocket 消息

    Args:
        message_type: 消息类型
        data: 消息数据

    Returns:
        格式化后的消息
    """
    return {
        "type": message_type,
        "data": data
    }


def extract_progress_data(message: Dict[str, Any]) -> tuple:
    """
    从进度消息中提取数据

    Args:
        message: 进度消息

    Returns:
        (value, max) 元组
    """
    data = message.get("data", {})
    return data.get("value", 0), data.get("max", 0)


def extract_executing_node(message: Dict[str, Any]) -> str:
    """
    从执行消息中提取节点 ID

    Args:
        message: 执行消息

    Returns:
        节点 ID
    """
    data = message.get("data", {})
    return data.get("node", "")


def is_completion_message(message: Dict[str, Any]) -> bool:
    """
    判断是否为完成消息

    Args:
        message: 消息数据

    Returns:
        是否为完成消息
    """
    msg_type = message.get("type", "")
    data = message.get("data", {})

    return (
        msg_type == "executing" and
        data.get("node") is None
    )


def is_error_message(message: Dict[str, Any]) -> bool:
    """
    判断是否为错误消息

    Args:
        message: 消息数据

    Returns:
        是否为错误消息
    """
    return message.get("type") == "execution_error"


def sanitize_workflow_for_websocket(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理工作流数据用于 WebSocket 传输

    Args:
        workflow: 原始工作流数据

    Returns:
        清理后的工作流数据
    """
    # 限制工作流大小，避免传输过大数据
    if len(workflow) > 100:
        return {
            "node_count": len(workflow),
            "truncated": True
        }

    return workflow
