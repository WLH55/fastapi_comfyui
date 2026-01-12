"""
工作流领域模块

提供工作流提交、查询、中断等功能
"""

from src.workflows.router import router
from src.workflows.schemas import (
    WorkflowSubmitRequest,
    WorkflowSubmitResponse,
    WorkflowInterruptRequest,
    NodeOutput,
    WorkflowHistoryResponse,
)
from src.workflows.service import (
    submit_workflow_to_comfyui,
    interrupt_workflow,
    get_workflow_history,
    check_workflow_completion,
    get_workflow_outputs,
    get_generated_images,
)

__all__ = [
    "router",
    "WorkflowSubmitRequest",
    "WorkflowSubmitResponse",
    "WorkflowInterruptRequest",
    "NodeOutput",
    "WorkflowHistoryResponse",
    "submit_workflow_to_comfyui",
    "interrupt_workflow",
    "get_workflow_history",
    "check_workflow_completion",
    "get_workflow_outputs",
    "get_generated_images",
]
