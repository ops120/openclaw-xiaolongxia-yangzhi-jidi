# -*- coding: utf-8 -*-
"""
日志工具
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(log_level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """
    设置日志器

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径，None 表示不写入文件

    Returns:
        配置好的日志器
    """
    logger = logging.getLogger('watermark')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除已有的处理器
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = 'watermark') -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    return logging.getLogger(name)


# 默认日志器
_default_logger = None


def init_default_logger():
    """初始化默认日志器"""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger()
    return _default_logger
