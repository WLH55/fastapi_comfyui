"""
工作流处理器模块

为特定的工作流模板文件提供专用的加载和处理逻辑
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_cpu_quickly_workflow() -> Dict[str, Any]:
    """
    加载 cpu_quickly_api.json 工作流

    Returns:
        ComfyUI API 格式的 workflow 字典
    """
    templates_dir = Path(__file__).parent.parent / "templates"
    api_file = templates_dir / "cpu_quickly_api.json"

    with open(api_file, "r", encoding="utf-8") as f:
        return json.load(f)
