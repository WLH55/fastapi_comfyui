"""
数据验证服务

负责验证请求数据的合法性和完整性
"""

from typing import Dict, Any, List

from src.exceptions import WorkflowValidationError


def validate_workflow_structure(workflow: Dict[str, Any]) -> bool:
    """
    验证工作流结构

    Args:
        workflow: 工作流字典

    Returns:
        是否有效

    Raises:
        WorkflowValidationError: 验证失败时
    """
    if not workflow:
        raise WorkflowValidationError("工作流不能为空")

    if not isinstance(workflow, dict):
        raise WorkflowValidationError("工作流必须是字典类型")

    # 检查是否有节点
    if len(workflow) == 0:
        raise WorkflowValidationError("工作流至少需要一个节点")

    # 验证每个节点的结构
    for node_id, node_data in workflow.items():
        if "class_type" not in node_data:
            raise WorkflowValidationError(
                f"节点 {node_id} 缺少 class_type 字段"
            )

        if "inputs" not in node_data:
            raise WorkflowValidationError(
                f"节点 {node_id} 缺少 inputs 字段"
            )

    return True


def validate_prompt_text(text: str, min_length: int = 1, max_length: int = 5000) -> bool:
    """
    验证提示词文本

    Args:
        text: 提示词文本
        min_length: 最小长度
        max_length: 最大长度

    Returns:
        是否有效

    Raises:
        WorkflowValidationError: 验证失败时
    """
    if not text or not text.strip():
        raise WorkflowValidationError("提示词不能为空")

    if len(text) < min_length:
        raise WorkflowValidationError(
            f"提示词长度不能少于 {min_length} 个字符"
        )

    if len(text) > max_length:
        raise WorkflowValidationError(
            f"提示词长度不能超过 {max_length} 个字符"
        )

    return True


def validate_image_filename(filename: str, allowed_extensions: List[str] = None) -> bool:
    """
    验证图片文件名

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表

    Returns:
        是否有效

    Raises:
        WorkflowValidationError: 验证失败时
    """
    if not filename:
        raise WorkflowValidationError("文件名不能为空")

    if allowed_extensions is None:
        allowed_extensions = [".png", ".jpg", ".jpeg", ".webp", ".gif"]

    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if f".{ext}" not in allowed_extensions:
        raise WorkflowValidationError(
            f"不支持的图片格式，允许的格式: {', '.join(allowed_extensions)}"
        )

    return True


def validate_client_id(client_id: str) -> bool:
    """
    验证客户端 ID

    Args:
        client_id: 客户端 ID

    Returns:
        是否有效

    Raises:
        WorkflowValidationError: 验证失败时
    """
    if not client_id:
        raise WorkflowValidationError("客户端 ID 不能为空")

    if len(client_id) > 100:
        raise WorkflowValidationError("客户端 ID 长度不能超过 100 个字符")

    return True
