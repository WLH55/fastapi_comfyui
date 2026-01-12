"""
场景领域配置
"""

import os
from pathlib import Path
from src.config import settings


class ScenarioConfig:
    """场景模块配置类"""

    # 模板存储目录
    TEMPLATES_DIR: Path = Path(__file__).parent.parent / "scenarios" / "templates"

    # 是否启用模板缓存
    ENABLE_TEMPLATE_CACHE: bool = True

    # 模板缓存过期时间（秒）
    TEMPLATE_CACHE_TTL: int = 3600

    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".webp"]

    # 默认图片尺寸
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 1024

    # 默认采样参数
    DEFAULT_STEPS = 20
    DEFAULT_CFG = 7.0
    DEFAULT_SAMPLER = "euler"
    DEFAULT_SCHEDULER = "normal"


# 创建配置实例
scenario_config = ScenarioConfig()

# 确保模板目录存在
scenario_config.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
