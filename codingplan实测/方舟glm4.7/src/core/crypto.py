"""
加密模块
提供密钥派生和加密/解密功能
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class CryptoManager:
    """加密管理器"""

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        从密码派生加密密钥

        Args:
            password: 密码字符串
            salt: 盐值

        Returns:
            派生的密钥（32字节 url-safe base64）
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def get_cipher(key: bytes) -> Fernet:
        """
        获取Fernet加密器

        Args:
            key: 密钥（32字节 url-safe base64）

        Returns:
            Fernet加密器
        """
        return Fernet(key)

    @staticmethod
    def generate_key() -> bytes:
        """
        生成随机密钥

        Returns:
            随机密钥（32字节 url-safe base64）
        """
        return Fernet.generate_key()
