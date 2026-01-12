"""
WebSocket 领域配置

定义 WebSocket 模块的特定配置
"""

from src.config import settings


class WebSocketConfig:
    """WebSocket 模块配置类"""

    # 连接超时时间（秒）
    CONNECTION_TIMEOUT: int = settings.COMFYUI_TIMEOUT

    # Ping 间隔（秒）
    PING_INTERVAL: int = settings.WS_PING_INTERVAL

    # Ping 超时（秒）
    PING_TIMEOUT: int = settings.WS_PING_TIMEOUT

    # 最大消息大小（字节）
    MAX_MESSAGE_SIZE: int = settings.WS_MAX_SIZE

    # 心跳检测间隔（秒）
    HEARTBEAT_INTERVAL: int = 30


# 创建配置实例
websocket_config = WebSocketConfig()
