"""
应用配置模块
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置类"""

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
    COMFYUI_PORT: int = 8189
    COMFYUI_TIMEOUT: int = 999999

    @property
    def COMFYUI_BASE_URL(self) -> str:
        """获取 ComfyUI 基础 URL"""
        return f"http://{self.COMFYUI_HOST}:{self.COMFYUI_PORT}"

    # ========== 文件存储配置 ==========
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    INPUT_DIR: Path = BASE_DIR / "input"
    OUTPUT_DIR: Path = BASE_DIR / "output"

    # ========== WebSocket 配置 ==========
    WS_PING_INTERVAL: int = 20
    WS_PING_TIMEOUT: int = 20
    WS_MAX_SIZE: int = 104857600  # 100MB

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def ensure_directories():
    """确保必要的目录存在"""
    settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
