"""
核心模块 - 水印嵌入和提取
"""

from .watermark import DocxWatermarkTool
from .crypto import CryptoManager

__all__ = ['DocxWatermarkTool', 'CryptoManager']
