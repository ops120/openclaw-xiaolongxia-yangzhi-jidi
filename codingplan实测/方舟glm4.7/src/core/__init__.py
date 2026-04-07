"""
核心模块
"""

from .watermark import DocxWatermarkTool, DEFAULT_PASSWORD
from .crypto import CryptoManager

__all__ = ['DocxWatermarkTool', 'CryptoManager', 'DEFAULT_PASSWORD']
