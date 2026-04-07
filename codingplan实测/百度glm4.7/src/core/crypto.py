# -*- coding: utf-8 -*-
"""
加密模块 - 密钥派生和数据加密
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class CryptoManager:
    """加密管理器 - 处理密钥派生和数据加密"""

    # 固定的默认盐值
    DEFAULT_SALT = b'docx_watermark_salt_v1_2024'

    # 固定的默认主密钥（用于无密码情况）
    DEFAULT_MASTER_KEY = b'oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ='

    def __init__(self, password: str = None, salt: bytes = None):
        """
        初始化加密管理器

        Args:
            password: 用户密码，用于派生加密密钥
            salt: 盐值，增强安全性
        """
        self.salt = salt or self.DEFAULT_SALT

        if password:
            self.key = self._derive_key(password, self.salt)
        else:
            # 使用固定默认密钥
            self.key = self.DEFAULT_MASTER_KEY

        self.cipher = Fernet(self.key)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        从密码派生加密密钥

        Args:
            password: 用户密码
            salt: 盐值

        Returns:
            Fernet 兼容的密钥 (32字节 url-safe base64)
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))

    def encrypt(self, data: str) -> bytes:
        """
        加密数据

        Args:
            data: 待加密的字符串

        Returns:
            加密后的字节串
        """
        return self.cipher.encrypt(data.encode('utf-8'))

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        解密数据

        Args:
            encrypted_data: 加密的字节串

        Returns:
            解密后的字符串

        Raises:
            cryptography.fernet.InvalidToken: 密钥不匹配或数据损坏
        """
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode('utf-8')

    def encrypt_to_base64(self, data: str) -> str:
        """
        加密数据并转换为 base64 字符串

        Args:
            data: 待加密的字符串

        Returns:
            base64 编码的加密字符串
        """
        encrypted = self.encrypt(data)
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt_from_base64(self, encrypted_base64: str) -> str:
        """
        从 base64 字符串解密数据

        Args:
            encrypted_base64: base64 编码的加密字符串

        Returns:
            解密后的字符串
        """
        encrypted = base64.b64decode(encrypted_base64.encode('utf-8'))
        return self.decrypt(encrypted)

    @staticmethod
    def generate_key() -> bytes:
        """
        生成新的 Fernet 密钥

        Returns:
            新生成的密钥
        """
        return Fernet.generate_key()

    @staticmethod
    def generate_password(length: int = 32) -> str:
        """
        生成随机密码

        Args:
            length: 密码长度

        Returns:
            随机密码字符串
        """
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(secrets.choice(alphabet) for _ in range(length))
