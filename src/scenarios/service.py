"""
场景领域服务

场景化封装业务逻辑层
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from src.config import settings
from src.scenarios.config import scenario_config
from src.scenarios.constants import DEFAULT_PARAM_MAPPINGS
from src.scenarios.exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateExecutionError,
    ParamMappingError,
    ScenarioNotFoundError,
)
from src.workflows.service import submit_workflow_to_comfyui


# ========== 模板存储管理 ==========

_template_cache: Dict[str, Dict[str, Any]] = {}


def _get_template_path(template_id: str) -> Path:
    """
    获取模板文件路径

    Args:
        template_id: 模板 ID

    Returns:
        模板文件路径
    """
    return scenario_config.TEMPLATES_DIR / f"{template_id}.json"


def _load_template_from_file(template_id: str) -> Dict[str, Any]:
    """
    从文件加载模板

    Args:
        template_id: 模板 ID

    Returns:
        模板数据

    Raises:
        TemplateNotFoundError: 模板不存在时
    """
    template_path = _get_template_path(template_id)

    if not template_path.exists():
        raise TemplateNotFoundError(template_id)

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        raise TemplateValidationError(f"模板 JSON 格式错误: {str(e)}")


def _save_template_to_file(template_id: str, template_data: Dict[str, Any]) -> None:
    """
    保存模板到文件

    Args:
        template_id: 模板 ID
        template_data: 模板数据
    """
    template_path = _get_template_path(template_id)

    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)


def _generate_template_id() -> str:
    """生成唯一的模板 ID"""
    return f"tpl_{uuid.uuid4().hex[:12]}"


# ========== 模板 CRUD 操作 ==========

async def save_workflow_template(
    name: str,
    workflow: Dict[str, Any],
    param_mappings: Dict[str, Dict[str, str]],
    description: str = ""
) -> Dict[str, Any]:
    """
    保存 workflow 模板

    Args:
        name: 模板名称
        workflow: workflow JSON
        param_mappings: 参数映射配置
        description: 模板描述

    Returns:
        模板信息
    """
    template_id = _generate_template_id()

    template_data = {
        "id": template_id,
        "name": name,
        "description": description,
        "workflow": workflow,
        "param_mappings": param_mappings,
        "created_at": datetime.now().isoformat(),
    }

    _save_template_to_file(template_id, template_data)

    # 缓存模板
    if scenario_config.ENABLE_TEMPLATE_CACHE:
        _template_cache[template_id] = template_data

    return {
        "id": template_id,
        "name": name,
        "description": description,
        "created_at": template_data["created_at"],
    }


async def get_workflow_template(template_id: str) -> Dict[str, Any]:
    """
    获取 workflow 模板

    Args:
        template_id: 模板 ID

    Returns:
        模板数据

    Raises:
        TemplateNotFoundError: 模板不存在时
    """
    # 先从缓存获取
    if scenario_config.ENABLE_TEMPLATE_CACHE and template_id in _template_cache:
        return _template_cache[template_id]

    template_data = _load_template_from_file(template_id)

    # 缓存模板
    if scenario_config.ENABLE_TEMPLATE_CACHE:
        _template_cache[template_id] = template_data

    return template_data


async def list_workflow_templates() -> List[Dict[str, Any]]:
    """
    列出所有 workflow 模板

    Returns:
        模板列表
    """
    templates_dir = scenario_config.TEMPLATES_DIR

    templates = []
    for template_file in templates_dir.glob("*.json"):
        try:
            template_id = template_file.stem
            template_data = _load_template_from_file(template_id)

            templates.append({
                "id": template_data["id"],
                "name": template_data["name"],
                "description": template_data.get("description", ""),
                "created_at": template_data.get("created_at", ""),
            })

        except Exception:
            continue

    return templates


async def delete_workflow_template(template_id: str) -> bool:
    """
    删除 workflow 模板

    Args:
        template_id: 模板 ID

    Returns:
        是否删除成功
    """
    template_path = _get_template_path(template_id)

    if not template_path.exists():
        raise TemplateNotFoundError(template_id)

    template_path.unlink()

    # 从缓存中移除
    if template_id in _template_cache:
        del _template_cache[template_id]

    return True


# ========== 参数替换逻辑 ==========

def _set_nested_value(obj: Dict[str, Any], path: str, value: Any) -> None:
    """
    设置嵌套字典的值

    Args:
        obj: 目标字典
        path: 字段路径（支持点号分隔）
        value: 要设置的值
    """
    keys = path.split(".")
    current = obj

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def _find_nodes_by_type(workflow: Dict[str, Any], node_type: str) -> List[str]:
    """
    根据节点类型查找节点 ID

    Args:
        workflow: workflow 数据
        node_type: 节点类型

    Returns:
        节点 ID 列表
    """
    matching_nodes = []

    for node_id, node_data in workflow.items():
        if node_data.get("class_type") == node_type:
            matching_nodes.append(node_id)

    return matching_nodes


def _apply_param_to_workflow(
    workflow: Dict[str, Any],
    param_name: str,
    param_value: Any,
    node_id: str,
    field: str
) -> None:
    """
    将参数应用到 workflow 节点

    Args:
        workflow: workflow 数据
        param_name: 参数名称
        param_value: 参数值
        node_id: 目标节点 ID
        field: 目标字段

    Raises:
        ParamMappingError: 参数映射失败时
    """
    if node_id not in workflow:
        raise ParamMappingError(param_name, f"节点 {node_id} 不存在")

    node_data = workflow[node_id]

    # 设置参数值
    try:
        if "inputs" not in node_data:
            node_data["inputs"] = {}

        _set_nested_value(node_data["inputs"], field, param_value)

    except Exception as e:
        raise ParamMappingError(param_name, f"设置字段失败: {str(e)}")


def _apply_params_to_workflow(
    workflow: Dict[str, Any],
    params: Dict[str, Any],
    param_mappings: Dict[str, Dict[str, str]]
) -> Dict[str, Any]:
    """
    将参数应用到 workflow

    Args:
        workflow: 原始 workflow
        params: 参数值字典
        param_mappings: 参数映射配置

    Returns:
        替换后的 workflow

    Raises:
        ParamMappingError: 参数映射失败时
    """
    import copy

    # 深拷贝 workflow，避免修改原始数据
    workflow_copy = copy.deepcopy(workflow)

    for param_name, param_value in params.items():
        if param_name not in param_mappings:
            raise ParamMappingError(param_name, "未定义的参数映射")

        mapping = param_mappings[param_name]
        node_id = mapping.get("node_id")
        field = mapping.get("field")

        if not node_id or not field:
            raise ParamMappingError(param_name, "映射配置不完整")

        _apply_param_to_workflow(workflow_copy, param_name, param_value, node_id, field)

    return workflow_copy


# ========== 场景执行 ==========

async def execute_scenario_template(
    template_id: str,
    params: Dict[str, Any],
    client_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    执行场景模板

    Args:
        template_id: 模板 ID
        params: 参数值字典
        client_id: 客户端 ID

    Returns:
        执行结果
    """
    # 加载模板
    template_data = await get_workflow_template(template_id)

    workflow = template_data["workflow"]
    param_mappings = template_data.get("param_mappings", {})

    # 应用参数替换
    try:
        final_workflow = _apply_params_to_workflow(workflow, params, param_mappings)

    except ParamMappingError as e:
        raise TemplateExecutionError(
            f"参数替换失败: {e.message}",
            template_id=template_id
        )

    # 提交 workflow
    prompt_id = await submit_workflow_to_comfyui(final_workflow, client_id)

    return {
        "prompt_id": prompt_id,
        "template_id": template_id,
        "client_id": client_id,
    }


# ========== 预定义场景 ==========

async def _get_predefined_workflow(scenario_type: str) -> Dict[str, Any]:
    """
    获取预定义场景的 workflow 模板

    Args:
        scenario_type: 场景类型

    Returns:
        (workflow, param_mappings) 元组

    Raises:
        ScenarioNotFoundError: 场景不存在时
    """
    # 尝试从文件加载
    template_path = scenario_config.TEMPLATES_DIR / f"builtin_{scenario_type}.json"

    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["workflow"], data.get("param_mappings", {})

    # 如果没有预定义文件，返回基础模板
    if scenario_type == "text2img":
        return _get_default_text2img_template()
    elif scenario_type == "img2img":
        return _get_default_img2img_template()
    else:
        raise ScenarioNotFoundError(scenario_type)


def _get_default_text2img_template() -> tuple:
    """获取默认的文生图模板"""
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.safetensors"}
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0]
            }
        }
    }

    param_mappings = DEFAULT_PARAM_MAPPINGS["text2img"]

    # 更新映射中的 node_id
    param_mappings = {
        "prompt": {"node_id": "2", "field": "text"},
        "negative_prompt": {"node_id": "3", "field": "text"},
        "width": {"node_id": "4", "field": "width"},
        "height": {"node_id": "4", "field": "height"},
        "seed": {"node_id": "5", "field": "seed"},
        "steps": {"node_id": "5", "field": "steps"},
        "cfg": {"node_id": "5", "field": "cfg"},
        "sampler_name": {"node_id": "5", "field": "sampler_name"},
        "scheduler": {"node_id": "5", "field": "scheduler"},
    }

    return workflow, param_mappings


def _get_default_img2img_template() -> tuple:
    """获取默认的图生图模板"""
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.safetensors"}
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": "input.png", "upload": "image"}
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["1", 1]
            }
        },
        "5": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["1", 2]
            }
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 0.75,
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0]
            }
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["1", 2]
            }
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["7", 0]
            }
        }
    }

    param_mappings = {
        "prompt": {"node_id": "3", "field": "text"},
        "negative_prompt": {"node_id": "4", "field": "text"},
        "input_image": {"node_id": "2", "field": "image"},
        "denoise": {"node_id": "6", "field": "denoise"},
        "seed": {"node_id": "6", "field": "seed"},
        "steps": {"node_id": "6", "field": "steps"},
        "cfg": {"node_id": "6", "field": "cfg"},
    }

    return workflow, param_mappings


async def execute_text2img_scenario(params: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
    """
    执行文生图场景

    Args:
        params: 场景参数
        client_id: 客户端 ID

    Returns:
        执行结果
    """
    workflow, param_mappings = await _get_predefined_workflow("text2img")

    final_workflow = _apply_params_to_workflow(workflow, params, param_mappings)

    prompt_id = await submit_workflow_to_comfyui(final_workflow, client_id)

    return {
        "prompt_id": prompt_id,
        "scenario_type": "text2img",
        "client_id": client_id,
    }


async def execute_img2img_scenario(params: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
    """
    执行图生图场景

    Args:
        params: 场景参数
        client_id: 客户端 ID

    Returns:
        执行结果
    """
    workflow, param_mappings = await _get_predefined_workflow("img2img")

    final_workflow = _apply_params_to_workflow(workflow, params, param_mappings)

    prompt_id = await submit_workflow_to_comfyui(final_workflow, client_id)

    return {
        "prompt_id": prompt_id,
        "scenario_type": "img2img",
        "client_id": client_id,
    }
