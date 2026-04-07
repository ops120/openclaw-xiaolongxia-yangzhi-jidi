"""
配置管理模块
"""

import json
from pathlib import Path


class Config:
    """配置管理器"""

    DEFAULT_CONFIG = {
        'default_key_name': '默认密钥',
        'output_directory': 'watermarked',
        'log_level': 'INFO',
        'log_file': 'watermark.log',
        'window_width': 900,
        'window_height': 700
    }

    def __init__(self, config_path: str = 'config.json'):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # 合并默认配置和加载的配置
                return {**self.DEFAULT_CONFIG, **loaded}
            except:
                pass
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """设置配置项"""
        self.config[key] = value
        self.save_config()

    def get_all(self) -> dict:
        """获取所有配置"""
        return self.config.copy()
