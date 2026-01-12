"""
工具函数模块
"""

import json
from pathlib import Path
from typing import Dict, Any
from copy import deepcopy


def save_file(content: bytes, filename: str, directory: Path) -> str:
    """保存文件到目录"""
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    with open(file_path, "wb") as f:
        f.write(content)
    return str(file_path)


def read_file(file_path: Path) -> bytes:
    """读取文件"""
    with open(file_path, "rb") as f:
        return f.read()


def load_workflow_json(file_path: str) -> Dict[str, Any]:
    """
    加载 ComfyUI workflow JSON 文件

    Args:
        file_path: JSON 文件路径（相对于 app/templates/）

    Returns:
        workflow 字典（API 格式）

    Note:
        模板文件必须是 API 格式，不进行自动转换
    """
    templates_dir = Path(__file__).parent.parent.parent / "app" / "templates"
    full_path = templates_dir / file_path

    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_params_to_workflow(
    workflow: Dict[str, Any],
    params: Dict[str, Any],
    param_mappings: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    将参数应用到 workflow

    Args:
        workflow: 原始 workflow（API 格式）
        params: 用户提供的参数
        param_mappings: 参数映射配置 {参数名: {node_id, field}}

    Returns:
        应用参数后的 workflow
    """
    result = deepcopy(workflow)

    for param_name, param_value in params.items():
        if param_name not in param_mappings:
            continue

        mapping = param_mappings[param_name]
        node_id = mapping["node_id"]
        field = mapping["field"]

        if node_id not in result:
            continue

        # 处理嵌套字段（如 inputs.text）
        keys = field.split(".")
        current = result[node_id]
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = param_value

    return result
