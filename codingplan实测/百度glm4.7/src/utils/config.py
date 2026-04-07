# -*- coding: utf-8 -*-
"""
配置管理
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理类"""

    DEFAULT_CONFIG = {
        'version': '1.1.0',
        'log_level': 'INFO',
        'log_file': None,
        'default_output_dir': 'watermarked',
        'max_backup_count': 10,
        'ui': {
            'theme': 'default',
            'language': 'zh_CN',
            'window_size': [800, 600]
        },
        'watermark': {
            'default_project': '',
            'default_department': ''
        }
    }

    def __init__(self, config_path: str = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，默认为程序目录下的 config.json
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config.json'

        self.config_path = str(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置
                return self._merge_config(self.DEFAULT_CONFIG, config)
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def _merge_config(self, default: Dict, custom: Dict) -> Dict:
        """递归合并配置"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def save(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键 (如 'ui.theme')
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    @property
    def version(self) -> str:
        """获取版本号"""
        return self._config.get('version', '1.0.0')

    @property
    def log_level(self) -> str:
        """获取日志级别"""
        return self._config.get('log_level', 'INFO')

    @property
    def default_output_dir(self) -> str:
        """获取默认输出目录"""
        return self._config.get('default_output_dir', 'watermarked')

    @property
    def ui_theme(self) -> str:
        """获取 UI 主题"""
        return self.get('ui.theme', 'default')

    @property
    def window_size(self) -> tuple:
        """获取窗口大小"""
        size = self.get('ui.window_size', [800, 600])
        return tuple(size)
