"""
场景化封装领域模块

提供预定义场景和 workflow 模板管理功能
"""

from src.scenarios.router import router
from src.scenarios.schemas import (
    ScenarioTemplateRequest,
    ScenarioTemplateResponse,
    ScenarioExecuteRequest,
    ScenarioExecuteResponse,
    TemplateParamRequest,
)
from src.scenarios.service import (
    save_workflow_template,
    get_workflow_template,
    list_workflow_templates,
    delete_workflow_template,
    execute_scenario_template,
    execute_text2img_scenario,
    execute_img2img_scenario,
)

__all__ = [
    "router",
    "ScenarioTemplateRequest",
    "ScenarioTemplateResponse",
    "ScenarioExecuteRequest",
    "ScenarioExecuteResponse",
    "TemplateParamRequest",
    "save_workflow_template",
    "get_workflow_template",
    "list_workflow_templates",
    "delete_workflow_template",
    "execute_scenario_template",
    "execute_text2img_scenario",
    "execute_img2img_scenario",
]
