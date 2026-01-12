"""
队列领域配置

定义队列模块的特定配置
"""

from src.config import settings


class QueueConfig:
    """队列模块配置类"""

    # 队列查询超时时间（秒）
    QUERY_TIMEOUT: int = settings.COMFYUI_TIMEOUT

    # 默认队列清空确认
    REQUIRE_CLEAR_CONFIRMATION: bool = True


# 创建配置实例
queue_config = QueueConfig()
