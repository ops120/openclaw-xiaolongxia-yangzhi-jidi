# -*- coding: utf-8 -*-
"""
Word 智能水印溯源系统 - 核心模块
"""

from .watermark import DocxWatermarkTool
from .crypto import CryptoManager

__all__ = ['DocxWatermarkTool', 'CryptoManager']
