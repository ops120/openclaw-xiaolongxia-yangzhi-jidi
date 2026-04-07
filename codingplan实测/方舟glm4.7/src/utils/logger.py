"""
日志工具
提供统一的日志记录接口
"""

import logging
from pathlib import Path
from datetime import datetime


class Logger:
    """日志记录器"""

    def __init__(self, name: str = 'watermark', log_dir: str = None):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
            log_dir: 日志目录，默认为程序目录下的logs文件夹
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if not self.logger.handlers:
            # 确定日志目录
            if log_dir is None:
                log_dir = Path(__file__).parent.parent.parent / 'logs'
            else:
                log_dir = Path(log_dir)

            log_dir.mkdir(exist_ok=True)

            # 创建日志文件名
            log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

            # 添加文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)

            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, message: str):
        """记录INFO级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录WARNING级别日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录ERROR级别日志"""
        self.logger.error(message)

    def debug(self, message: str):
        """记录DEBUG级别日志"""
        self.logger.debug(message)


# 默认日志记录器
default_logger = Logger()
