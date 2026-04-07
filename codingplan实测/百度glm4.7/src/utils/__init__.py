# -*- coding: utf-8 -*-
"""
Word 智能水印溯源系统 - 工具模块
"""

from .logger import get_logger, setup_logger
from .config import Config

__all__ = ['get_logger', 'setup_logger', 'Config']
