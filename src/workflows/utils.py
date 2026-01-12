"""
工作流领域工具函数

定义工作流模块的非业务逻辑函数
"""

from typing import Dict, Any, List


def extract_prompt_id_from_response(response: Dict[str, Any]) -> str:
    """
    从 ComfyUI 响应中提取 prompt_id

    Args:
        response: ComfyUI 响应数据

    Returns:
        prompt_id
    """
    return response.get("prompt_id", "")


def format_workflow_error(error: Dict[str, Any]) -> str:
    """
    格式化工作流错误信息

    Args:
        error: 错误字典

    Returns:
        格式化后的错误信息
    """
    node_errors = error.get("node_errors", {})
    if not node_errors:
        return "未知错误"

    errors = []
    for node_id, node_error in node_errors.items():
        errors.append(f"节点 {node_id}: {node_error}")

    return "; ".join(errors)


def sanitize_workflow_for_logging(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理工作流数据用于日志记录

    Args:
        workflow: 原始工作流数据

    Returns:
        清理后的工作流数据
    """
    sanitized = {}
    for node_id, node_data in workflow.items():
        sanitized[node_id] = {
            "class_type": node_data.get("class_type", ""),
            "inputs": "<inputs>" if "inputs" in node_data else {}
        }

    return sanitized


def count_workflow_nodes(workflow: Dict[str, Any]) -> int:
    """
    统计工作流节点数量

    Args:
        workflow: 工作流数据

    Returns:
        节点数量
    """
    return len(workflow)


def get_workflow_node_types(workflow: Dict[str, Any]) -> List[str]:
    """
    获取工作流中的节点类型列表

    Args:
        workflow: 工作流数据

    Returns:
        节点类型列表
    """
    return [
        node_data.get("class_type", "Unknown")
        for node_data in workflow.values()
    ]
