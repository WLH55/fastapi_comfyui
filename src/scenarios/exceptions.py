"""
场景领域异常
"""

from src.exceptions import ComfyUIException


class TemplateNotFoundError(ComfyUIException):
    """模板未找到错误"""

    def __init__(self, template_id: str):
        super().__init__(
            f"模板未找到: {template_id}",
            detail={"template_id": template_id},
            code="TEMPLATE_NOT_FOUND"
        )


class TemplateValidationError(ComfyUIException):
    """模板验证错误"""

    def __init__(self, message: str, detail=None):
        super().__init__(
            message,
            detail=detail,
            code="TEMPLATE_VALIDATION_ERROR"
        )


class TemplateExecutionError(ComfyUIException):
    """模板执行错误"""

    def __init__(self, message: str, template_id: str = None):
        super().__init__(
            message,
            detail={"template_id": template_id} if template_id else None,
            code="TEMPLATE_EXECUTION_ERROR"
        )


class ParamMappingError(ComfyUIException):
    """参数映射错误"""

    def __init__(self, param_name: str, reason: str):
        super().__init__(
            f"参数映射失败: {param_name} - {reason}",
            detail={"param_name": param_name, "reason": reason},
            code="PARAM_MAPPING_ERROR"
        )


class ScenarioNotFoundError(ComfyUIException):
    """场景未找到错误"""

    def __init__(self, scenario_type: str):
        super().__init__(
            f"场景未找到: {scenario_type}",
            detail={"scenario_type": scenario_type},
            code="SCENARIO_NOT_FOUND"
        )
