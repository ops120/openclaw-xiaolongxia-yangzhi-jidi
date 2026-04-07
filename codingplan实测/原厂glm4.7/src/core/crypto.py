"""
加密模块 - 密钥派生和加密解密
"""

import base64
import zlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class CryptoManager:
    """加密管理器 - 处理密钥派生和加密解密"""

    # 固定默认密码（用于测试和默认场景）
    DEFAULT_PASSWORD = 'docx_watermark_default_key_2024'
    DEFAULT_SALT = b'docx_watermark_salt_v1'

    def __init__(self, master_password: str = None, salt: bytes = None):
        """
        初始化加密管理器

        Args:
            master_password: 主密码，用于派生加密密钥
            salt: 盐值，增强安全性
        """
        self.salt = salt or self.DEFAULT_SALT
        password = master_password or self.DEFAULT_PASSWORD
        self.master_key = self._derive_key(password, self.salt)
        self.cipher = Fernet(self.master_key)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """从主密码派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def calculate_crc(self, data: str) -> str:
        """计算 CRC 校验码"""
        return format(zlib.crc32(data.encode()) & 0xFFFFFFFF, '04X')

    def encrypt(self, plaintext: str) -> bytes:
        """加密文本"""
        return self.cipher.encrypt(plaintext.encode('utf-8'))

    def decrypt(self, ciphertext: bytes) -> str:
        """解密数据"""
        return self.cipher.decrypt(ciphertext).decode('utf-8')

    def text_to_base64(self, text: str) -> str:
        """将文本转换为 base64 编码（用于备份数据）"""
        encrypted_data = self.encrypt(text)
        return base64.urlsafe_b64encode(encrypted_data).decode('ascii')

    def base64_to_text(self, b64_data: str) -> str:
        """将 base64 编码还原为文本"""
        encrypted_data = base64.urlsafe_b64decode(b64_data.encode('ascii'))
        return self.decrypt(encrypted_data)
