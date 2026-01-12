"""
场景领域工具函数
"""

import json
import random
from typing import Dict, Any, List
from pathlib import Path


def parse_workflow_api_file(file_path: str) -> Dict[str, Any]:
    """
    解析 ComfyUI API 格式的 workflow 文件

    Args:
        file_path: workflow 文件路径

    Returns:
        workflow JSON 数据

    Raises:
        ValueError: 文件解析失败时
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        raise ValueError(f"Workflow 文件 JSON 格式错误: {str(e)}")

    except FileNotFoundError:
        raise ValueError(f"Workflow 文件不存在: {file_path}")


def generate_random_seed() -> int:
    """
    生成随机种子

    Returns:
        随机种子值
    """
    return random.randint(0, 2**32 - 1)


def validate_workflow_structure(workflow: Dict[str, Any]) -> List[str]:
    """
    验证 workflow 结构并返回问题列表

    Args:
        workflow: workflow 数据

    Returns:
        问题列表（空列表表示没有问题）
    """
    issues = []

    if not workflow:
        issues.append("Workflow 为空")
        return issues

    if not isinstance(workflow, dict):
        issues.append("Workflow 必须是字典类型")
        return issues

    # 检查是否有节点
    if len(workflow) == 0:
        issues.append("Workflow 至少需要一个节点")

    # 验证每个节点
    for node_id, node_data in workflow.items():
        if "class_type" not in node_data:
            issues.append(f"节点 {node_id} 缺少 class_type 字段")

        if "inputs" not in node_data:
            issues.append(f"节点 {node_id} 缺少 inputs 字段")

    return issues


def infer_param_mappings_from_workflow(
    workflow: Dict[str, Any],
    known_mappings: Dict[str, Dict[str, str]] = None
) -> Dict[str, Dict[str, str]]:
    """
    从 workflow 自动推断参数映射

    Args:
        workflow: workflow 数据
        known_mappings: 已知的映射配置

    Returns:
        推断的参数映射字典
    """
    mappings = {}
    if known_mappings:
        mappings = known_mappings.copy()

    # 常见节点类型到参数的映射规则
    inference_rules = {
        "CLIPTextEncode": [
            {"param": "prompt", "field": "text"},
            {"param": "negative_prompt", "field": "text"},
        ],
        "EmptyLatentImage": [
            {"param": "width", "field": "width"},
            {"param": "height", "field": "height"},
            {"param": "batch_size", "field": "batch_size"},
        ],
        "KSampler": [
            {"param": "seed", "field": "seed"},
            {"param": "steps", "field": "steps"},
            {"param": "cfg", "field": "cfg"},
            {"param": "sampler_name", "field": "sampler_name"},
            {"param": "scheduler", "field": "scheduler"},
            {"param": "denoise", "field": "denoise"},
        ],
        "LoadImage": [
            {"param": "input_image", "field": "image"},
        ],
    }

    # 遍历节点，推断映射
    for node_id, node_data in workflow.items():
        class_type = node_data.get("class_type", "")

        if class_type in inference_rules:
            for rule in inference_rules[class_type]:
                param_name = rule["param"]
                field = rule["field"]

                # 如果参数还没有映射，添加映射
                if param_name not in mappings:
                    mappings[param_name] = {"node_id": node_id, "field": field}

    return mappings


def extract_workflow_metadata(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    从 workflow 提取元数据

    Args:
        workflow: workflow 数据

    Returns:
        元数据字典
    """
    metadata = {
        "node_count": len(workflow),
        "node_types": [],
        "has_image_input": False,
        "has_image_output": False,
    }

    for node_data in workflow.values():
        class_type = node_data.get("class_type", "")
        metadata["node_types"].append(class_type)

        if class_type == "LoadImage":
            metadata["has_image_input"] = True

        if class_type == "SaveImage":
            metadata["has_image_output"] = True

    # 去重
    metadata["node_types"] = list(set(metadata["node_types"]))

    return metadata


def create_workflow_preview(workflow: Dict[str, Any]) -> str:
    """
    创建 workflow 的预览文本

    Args:
        workflow: workflow 数据

    Returns:
        预览文本
    """
    metadata = extract_workflow_metadata(workflow)

    lines = [
        f"节点数量: {metadata['node_count']}",
        f"节点类型: {', '.join(metadata['node_types'][:5])}",
    ]

    if metadata['has_image_input']:
        lines.append("- 需要输入图片")

    if metadata['has_image_output']:
        lines.append("- 生成图片输出")

    return "\n".join(lines)


def sanitize_param_value(value: Any, param_type: str = "string") -> Any:
    """
    清理和验证参数值

    Args:
        value: 原始值
        param_type: 参数类型

    Returns:
        清理后的值
    """
    if value is None:
        return None

    if param_type == "integer":
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    if param_type == "float":
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    if param_type == "boolean":
        return bool(value)

    if param_type == "string":
        return str(value)

    return value


def merge_params_with_defaults(
    params: Dict[str, Any],
    defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """
    合并用户参数和默认值

    Args:
        params: 用户提供的参数
        defaults: 默认参数值

    Returns:
        合并后的参数字典
    """
    result = defaults.copy()
    result.update(params)
    return result
