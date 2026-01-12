"""
工作流领域服务

工作流业务逻辑层
"""

from typing import Dict, Any, Optional

from src.config import settings
from src.exceptions import ComfyUIConnectionError, WorkflowValidationError
from src.services import post_json, get_json, validate_workflow_structure
from src.workflows.constants import ComfyUIAPIPath


async def submit_workflow_to_comfyui(
    workflow: Dict[str, Any],
    client_id: Optional[str] = None
) -> str:
    """
    提交工作流到 ComfyUI

    Args:
        workflow: 工作流 JSON（API 格式）
        client_id: 客户端标识

    Returns:
        prompt_id: 任务 ID

    Raises:
        ComfyUIConnectionError: 连接失败时
        WorkflowValidationError: 工作流验证失败时
    """
    # 验证工作流结构
    validate_workflow_structure(workflow)

    # 构建请求 payload
    payload = {
        "prompt": workflow,
    }

    if client_id:
        payload["client_id"] = client_id

    # 提交到 ComfyUI
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.PROMPT}"
    response = await post_json(url, payload)

    # 检查是否有错误
    if "node_errors" in response and response["node_errors"]:
        raise ComfyUIConnectionError(
            f"工作流验证失败: {response['node_errors']}"
        )

    return response["prompt_id"]


async def interrupt_workflow(prompt_id: Optional[str] = None) -> Dict[str, Any]:
    """
    中断工作流执行

    Args:
        prompt_id: 任务 ID（可选，不传则中断所有）

    Returns:
        中断结果

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.INTERRUPT}"

    payload = {}
    if prompt_id:
        payload["prompt_id"] = prompt_id

    return await post_json(url, payload)


async def get_workflow_history(prompt_id: str) -> Dict[str, Any]:
    """
    获取工作流执行历史

    Args:
        prompt_id: 任务 ID

    Returns:
        历史记录数据

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    url = f"{settings.COMFYUI_BASE_URL}{ComfyUIAPIPath.HISTORY}/{prompt_id}"
    response = await get_json(url)

    if prompt_id in response:
        return response[prompt_id]

    return {}


async def check_workflow_completion(prompt_id: str) -> bool:
    """
    检查工作流是否完成

    Args:
        prompt_id: 任务 ID

    Returns:
        是否完成
    """
    try:
        history = await get_workflow_history(prompt_id)
        return bool(history)

    except Exception:
        return False


async def get_workflow_outputs(prompt_id: str) -> Dict[str, Any]:
    """
    获取工作流输出结果

    Args:
        prompt_id: 任务 ID

    Returns:
        输出结果字典

    Raises:
        ComfyUIConnectionError: 连接失败时
    """
    history = await get_workflow_history(prompt_id)
    return history.get("outputs", {})


async def get_generated_images(prompt_id: str) -> list:
    """
    获取工作流生成的图片列表

    Args:
        prompt_id: 任务 ID

    Returns:
        图片信息列表
    """
    outputs = await get_workflow_outputs(prompt_id)
    images = []

    for node_output in outputs.values():
        if "images" in node_output:
            for img in node_output["images"]:
                images.append({
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output")
                })

    return images
