"""
日志工具
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


class Logger:
    """日志管理器"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = 'logs', log_level: int = logging.INFO):
        """
        初始化日志管理器

        Args:
            log_dir: 日志目录
            log_level: 日志级别
        """
        if self._initialized:
            return

        self._initialized = True
        self.logger = logging.getLogger('WatermarkSystem')
        self.logger.setLevel(log_level)

        # 清除现有处理器
        self.logger.handlers.clear()

        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 文件处理器
        log_file = log_path / f'watermark_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        """记录 DEBUG 级别日志"""
        self.logger.debug(message)

    def info(self, message: str):
        """记录 INFO 级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录 WARNING 级别日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录 ERROR 级别日志"""
        self.logger.error(message)

    def critical(self, message: str):
        """记录 CRITICAL 级别日志"""
        self.logger.critical(message)

    def exception(self, message: str):
        """记录异常日志"""
        self.logger.exception(message)


# 全局日志实例
logger = Logger()