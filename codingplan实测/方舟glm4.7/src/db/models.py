"""
数据库模型
管理密钥和操作记录
"""

import sqlite3
import json
import base64
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
from typing import Dict, List, Optional


class Database:
    """数据库管理类"""

    # 固定的加密密钥（32字节 url-safe base64）
    _master_key = b'oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ='
    _cipher = Fernet(_master_key)

    def __init__(self, db_path: str = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认为当前目录的 watermark.db
        """
        if db_path is None:
            self.db_path = Path(__file__).parent.parent.parent / 'watermark.db'
        else:
            self.db_path = Path(db_path)

        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建密钥表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT UNIQUE NOT NULL,
                key_password TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建操作记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                user_info TEXT NOT NULL,
                key_name TEXT,
                original_filename TEXT,
                watermark_hash TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def add_key(self, key_name: str, password: str, salt: bytes = b'docx_watermark_salt_v1') -> int:
        """
        添加新密钥

        Args:
            key_name: 密钥名称
            password: 密钥密码
            salt: 盐值

        Returns:
            新密钥的ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 加密密码
            encrypted_password = self._encrypt_text(password)
            encrypted_salt = self._encrypt_bytes(salt)

            cursor.execute(
                'INSERT INTO keys (key_name, key_password, salt) VALUES (?, ?, ?)',
                (key_name, encrypted_password, encrypted_salt)
            )
            key_id = cursor.lastrowid
            conn.commit()
            return key_id
        except sqlite3.IntegrityError:
            raise ValueError(f'密钥名称 "{key_name}" 已存在')
        finally:
            conn.close()

    def get_all_keys(self) -> List[Dict]:
        """
        获取所有密钥信息

        Returns:
            密钥信息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, key_name, created_at FROM keys ORDER BY key_name')
        rows = cursor.fetchall()

        conn.close()

        return [
            {
                'id': row[0],
                'key_name': row[1],
                'created_at': row[2]
            }
            for row in rows
        ]

    def get_key_password(self, key_name: str) -> Optional[str]:
        """
        获取密钥密码

        Args:
            key_name: 密钥名称

        Returns:
            解密后的密码，如果密钥不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT key_password FROM keys WHERE key_name = ?', (key_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._decrypt_text(row[0])
        return None

    def get_key_salt(self, key_name: str) -> Optional[bytes]:
        """
        获取密钥盐值

        Args:
            key_name: 密钥名称

        Returns:
            解密后的盐值，如果密钥不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT salt FROM keys WHERE key_name = ?', (key_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._decrypt_bytes(row[0])
        return None

    def delete_key(self, key_name: str) -> bool:
        """
        删除密钥

        Args:
            key_name: 密钥名称

        Returns:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM keys WHERE key_name = ?', (key_name,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def add_trace_log(self, uid: str, user_info: str, key_name: str = None,
                      original_filename: str = None, watermark_hash: str = None) -> int:
        """
        添加操作记录

        Args:
            uid: 用户唯一标识
            user_info: 用户信息
            key_name: 使用的密钥名称
            original_filename: 原始文件名
            watermark_hash: 水印哈希

        Returns:
            新记录的ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO trace_logs (uid, user_info, key_name, original_filename, watermark_hash) VALUES (?, ?, ?, ?, ?)',
            (uid, user_info, key_name, original_filename, watermark_hash)
        )
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return log_id

    def get_trace_logs(self, limit: int = 100) -> List[Dict]:
        """
        获取操作记录

        Args:
            limit: 返回记录的最大数量

        Returns:
            操作记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id, uid, user_info, key_name, original_filename, created_at FROM trace_logs ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
        rows = cursor.fetchall()

        conn.close()

        return [
            {
                'id': row[0],
                'uid': row[1],
                'user_info': row[2],
                'key_name': row[3],
                'original_filename': row[4],
                'created_at': row[5]
            }
            for row in rows
        ]

    def _encrypt_text(self, text: str) -> str:
        """加密文本"""
        return self._cipher.encrypt(text.encode('utf-8')).decode('utf-8')

    def _decrypt_text(self, encrypted_text: str) -> str:
        """解密文本"""
        return self._cipher.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')

    def _encrypt_bytes(self, data: bytes) -> str:
        """加密字节数据"""
        return self._cipher.encrypt(data).decode('utf-8')

    def _decrypt_bytes(self, encrypted_data: str) -> bytes:
        """解密字节数据"""
        return self._cipher.decrypt(encrypted_data.encode('utf-8'))


class KeyManager:
    """密钥管理类"""

    def __init__(self, db: Database = None):
        """
        初始化密钥管理器

        Args:
            db: 数据库实例，如果为None则创建新实例
        """
        self.db = db or Database()

    def create_key(self, key_name: str, password: str, salt: bytes = b'docx_watermark_salt_v1') -> bool:
        """
        创建新密钥

        Args:
            key_name: 密钥名称
            password: 密钥密码
            salt: 盐值

        Returns:
            是否创建成功
        """
        try:
            self.db.add_key(key_name, password, salt)
            return True
        except Exception as e:
            print(f"创建密钥失败: {e}")
            return False

    def list_keys(self) -> List[Dict]:
        """
        列出所有密钥

        Returns:
            密钥信息列表
        """
        return self.db.get_all_keys()

    def get_key(self, key_name: str) -> Optional[Dict]:
        """
        获取指定密钥

        Args:
            key_name: 密钥名称

        Returns:
            密钥信息，包含password和salt字段
        """
        password = self.db.get_key_password(key_name)
        salt = self.db.get_key_salt(key_name)

        if password and salt:
            return {
                'key_name': key_name,
                'password': password,
                'salt': salt
            }
        return None

    def delete_key(self, key_name: str) -> bool:
        """
        删除密钥

        Args:
            key_name: 密钥名称

        Returns:
            是否删除成功
        """
        return self.db.delete_key(key_name)

    def export_keys(self, output_path: str) -> bool:
        """
        导出所有密钥到JSON文件

        Args:
            output_path: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            keys = []
            for key_info in self.list_keys():
                key_data = self.get_key(key_info['key_name'])
                if key_data:
                    keys.append({
                        'key_name': key_data['key_name'],
                        'password': key_data['password'],
                        'salt': base64.b64encode(key_data['salt']).decode('utf-8'),
                        'created_at': key_info['created_at']
                    })

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(keys, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"导出密钥失败: {e}")
            return False

    def import_keys(self, input_path: str) -> bool:
        """
        从JSON文件导入密钥

        Args:
            input_path: 输入文件路径

        Returns:
            是否导入成功
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                keys = json.load(f)

            for key in keys:
                salt = base64.b64decode(key['salt'].encode('utf-8'))
                self.create_key(key['key_name'], key['password'], salt)

            return True
        except Exception as e:
            print(f"导入密钥失败: {e}")
            return False
