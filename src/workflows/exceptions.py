"""
工作流领域异常

定义工作流模块的特定异常
"""

from src.exceptions import ComfyUIException


class WorkflowNotFoundError(ComfyUIException):
    """工作流未找到错误"""

    def __init__(self, prompt_id: str):
        super().__init__(
            f"工作流未找到: {prompt_id}",
            detail={"prompt_id": prompt_id},
            code="WORKFLOW_NOT_FOUND"
        )


class WorkflowSubmitError(ComfyUIException):
    """工作流提交错误"""

    def __init__(self, message: str, detail=None):
        super().__init__(
            message,
            detail=detail,
            code="WORKFLOW_SUBMIT_ERROR"
        )
