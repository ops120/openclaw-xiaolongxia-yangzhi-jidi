"""
配置管理工具
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """配置管理类"""

    _instance = None
    _initialized = False

    DEFAULT_CONFIG = {
        'app_name': 'Word智能水印溯源系统',
        'version': '1.1.0',
        'default_key_name': 'default',
        'output_dir': 'watermarked',
        'log_dir': 'logs',
        'db_file': 'watermark.db',
        'backup_dir': 'backups',
        'ui': {
            'theme': 'default',
            'language': 'zh_CN',
            'window_width': 1000,
            'window_height': 700
        },
        'watermark': {
            'max_embed_positions': 10,
            'min_embed_positions': 3,
            'default_salt': b'docx_watermark_salt_v1'
        }
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_file: str = 'config.json'):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        if self._initialized:
            return

        self._initialized = True
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()

        # 加载配置文件
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置
                    self._merge_config(self.config, user_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """
        递归合并配置

        Args:
            base: 基础配置
            override: 覆盖配置
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def save_config(self) -> bool:
        """
        保存配置到文件

        Returns:
            是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置项

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值

        Returns:
            是否成功
        """
        keys = key.split('.')
        config = self.config

        # 导航到父级
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value
        return self.save_config()

    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()

    @property
    def app_name(self) -> str:
        """应用名称"""
        return self.get('app_name')

    @property
    def version(self) -> str:
        """版本号"""
        return self.get('version')

    @property
    def output_dir(self) -> Path:
        """输出目录"""
        return Path(self.get('output_dir', 'watermarked'))

    @property
    def log_dir(self) -> Path:
        """日志目录"""
        return Path(self.get('log_dir', 'logs'))

    @property
    def backup_dir(self) -> Path:
        """备份目录"""
        return Path(self.get('backup_dir', 'backups'))

    @property
    def db_file(self) -> str:
        """数据库文件名"""
        return self.get('db_file', 'watermark.db')

    @property
    def default_key_name(self) -> str:
        """默认密钥名称"""
        return self.get('default_key_name', 'default')


# 全局配置实例
config = Config()