"""
应用配置模块

全局应用配置，从环境变量和配置文件中读取设置
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    应用配置类

    使用 Pydantic 进行配置验证和管理
    """

    # ========== 应用基本信息 ==========
    APP_NAME: str = "FastAPI ComfyUI Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    # ========== 服务器配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # ========== CORS 配置 ==========
    ALLOW_ORIGINS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]

    # ========== ComfyUI 配置 ==========
    COMFYUI_HOST: str = "127.0.0.1"
    COMFYUI_PORT: int = 8188
    COMFYUI_TIMEOUT: int = 300

    @property
    def COMFYUI_BASE_URL(self) -> str:
        """获取 ComfyUI 基础 URL"""
        return f"http://{self.COMFYUI_HOST}:{self.COMFYUI_PORT}"

    # ========== 文件存储配置 ==========
    # 项目根目录
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # 输入图片目录
    INPUT_DIR: Path = BASE_DIR / "input"

    # 输出图片目录
    OUTPUT_DIR: Path = BASE_DIR / "output"

    # ========== WebSocket 配置 ==========
    WS_PING_INTERVAL: int = 20
    WS_PING_TIMEOUT: int = 20
    WS_MAX_SIZE: int = 104857600  # 100MB

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def ensure_directories():
    """确保必要的目录存在"""
    settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
