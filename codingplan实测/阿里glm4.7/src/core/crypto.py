"""
加密模块 - 用于密钥派生和水印数据加密
"""
import base64
import zlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class CryptoEngine:
    """加密引擎"""

    DEFAULT_PASSWORD = 'docx_watermark_default_key_2024'
    DEFAULT_SALT = b'docx_watermark_salt_v1'

    def __init__(self, password: str = None, salt: bytes = None):
        """
        初始化加密引擎

        Args:
            password: 主密码，用于派生加密密钥
            salt: 盐值，增强安全性
        """
        self.salt = salt or self.DEFAULT_SALT
        password = password or self.DEFAULT_PASSWORD
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

    def encrypt(self, data: str) -> bytes:
        """
        加密字符串数据

        Args:
            data: 要加密的字符串

        Returns:
            加密后的字节数据
        """
        return self.cipher.encrypt(data.encode('utf-8'))

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        解密字节数据

        Args:
            encrypted_data: 加密的字节数据

        Returns:
            解密后的字符串

        Raises:
            Exception: 解密失败时抛出异常
        """
        return self.cipher.decrypt(encrypted_data).decode('utf-8')

    def calculate_crc(self, data: str) -> str:
        """
        计算数据的 CRC 校验码

        Args:
            data: 要计算校验码的字符串

        Returns:
            4位十六进制校验码
        """
        return format(zlib.crc32(data.encode()) & 0xFFFFFFFF, '04X')

    @staticmethod
    def validate_crc(data_dict: dict) -> bool:
        """
        验证数据字典中的 CRC 校验码

        Args:
            data_dict: 包含 crc 字段的数据字典

        Returns:
            校验是否通过
        """
        crc_data = data_dict.copy()
        stored_crc = crc_data.pop('crc', None)
        if not stored_crc:
            return False

        import json
        calculated_crc = format(zlib.crc32(json.dumps(crc_data, sort_keys=True).encode()) & 0xFFFFFFFF, '04X')
        return stored_crc == calculated_crc