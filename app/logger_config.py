import logging
from datetime import datetime
from pathlib import Path

from app.config import settings


# ========== 日志配置 ==========
def setup_logging():
    """
    配置日志系统

    - 按日期轮转日志文件
    - 自动压缩旧日志
    - 自动清理过期日志
    """
    # 创建日志格式
    log_format = "[%(asctime)s] %(levelname)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 创建 formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.LOG_LEVEL)

    # 文件处理器（按日期轮转）
    from logging.handlers import TimedRotatingFileHandler

    # 当天日志文件
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = settings.ACCESS_LOG_DIR / f"{today}.log"

    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",  # 每天午夜轮转
        interval=1,  # 每天一个文件
        backupCount=settings.LOG_BACKUP_COUNT,  # 保留文件数量
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(settings.LOG_LEVEL)

    # 轮转时压缩旧日志
    def namer(default_name):
        """重命名轮转的日志文件，添加 .gz 压缩后缀"""
        return default_name + ".gz"

    file_handler.namer = namer
    file_handler.rotator = __rotator

    # 配置根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 配置 uvicorn 日志也写入文件
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(settings.LOG_LEVEL)
    uvicorn_logger.addHandler(file_handler)

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(settings.LOG_LEVEL)
    uvicorn_access_logger.addHandler(file_handler)


def __rotator(source, dest):
    """
    日志轮转时的压缩函数

    将旧日志文件压缩为 .gz 格式
    """
    import gzip
    import shutil

    # 读取源文件
    with open(source, "rb") as f_in:
        # 写入压缩文件
        with gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # 删除源文件
    Path(source).unlink()

    # 清理过期日志
    __cleanup_old_logs()


def __cleanup_old_logs():
    """清理超过保留天数的日志文件"""
    import time

    current_time = time.time()
    cutoff_time = current_time - (settings.LOG_RETENTION_DAYS * 86400)

    for log_file in settings.ACCESS_LOG_DIR.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                logging.info(f"删除过期日志: {log_file.name}")
            except Exception as e:
                logging.warning(f"删除日志失败 {log_file.name}: {e}")
