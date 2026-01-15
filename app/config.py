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
    COMFYUI_WS_PORT: int = 8188  # ComfyUI WebSocket 端口
    COMFYUI_TIMEOUT: int = 999999

    @property
    def COMFYUI_BASE_URL(self) -> str:
        """获取 ComfyUI 基础 URL"""
        return f"http://{self.COMFYUI_HOST}:{self.COMFYUI_PORT}"

    @property
    def COMFYUI_WS_URL(self) -> str:
        """获取 ComfyUI WebSocket URL"""
        return f"ws://{self.COMFYUI_HOST}:{self.COMFYUI_WS_PORT}"

    # ========== 文件存储配置 ==========
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    INPUT_DIR: Path = BASE_DIR / "input"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    STORAGE_DIR: Path = BASE_DIR / "storage"
    LOGS_DIR: Path = STORAGE_DIR / "logs"
    ACCESS_LOG_DIR: Path = LOGS_DIR / "access"



    # ========== 签名验签配置 ==========
    SIGNATURE_ENABLED: bool = False  # 签名验证总开关
    APP_SECRET: str = ""  # 签名密钥（HMAC-SHA256）
    SIGNATURE_TIMESTAMP_TOLERANCE: int = 300  # 时间戳容忍度（秒），默认 5 分钟

    # ========== 日志配置 ==========
    LOG_LEVEL: str = "INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_RETENTION_DAYS: int = 7  # 日志保留天数
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 单个日志文件最大大小（10MB）
    LOG_BACKUP_COUNT: int = 30  # 保留的日志文件数量

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def ensure_directories():
    """确保必要的目录存在"""
    settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.ACCESS_LOG_DIR.mkdir(parents=True, exist_ok=True)
