"""
配置管理模块
提供配置文件的读写功能
"""

import json
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为程序目录下的config.json
        """
        if config_path is None:
            self.config_path = Path(__file__).parent.parent.parent / 'config.json'
        else:
            self.config_path = Path(config_path)

        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # 返回默认配置
        return {
            'version': '1.0',
            'last_used_key': None,
            'default_output_dir': 'watermarked',
            'log_level': 'INFO',
            'ui_theme': 'default'
        }

    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
        self._save_config()

    def get_all(self) -> Dict:
        """获取所有配置"""
        return self.config.copy()

    def update(self, config: Dict):
        """
        更新配置

        Args:
            config: 要更新的配置字典
        """
        self.config.update(config)
        self._save_config()


# 默认配置管理器
default_config = ConfigManager()
