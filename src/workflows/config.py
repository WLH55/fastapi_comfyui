"""
工作流领域配置

定义工作流模块的特定配置
"""

from src.config import settings


class WorkflowConfig:
    """工作流模块配置类"""

    # 工作流提交超时时间（秒）
    SUBMIT_TIMEOUT: int = settings.COMFYUI_TIMEOUT

    # 工作流执行历史查询限制
    HISTORY_MAX_ITEMS: int = 100

    # 工作流验证严格模式
    STRICT_VALIDATION: bool = True


# 创建配置实例
workflow_config = WorkflowConfig()
