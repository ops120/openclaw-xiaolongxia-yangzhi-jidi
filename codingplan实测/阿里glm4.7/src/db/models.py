"""
数据库模块 - 密钥管理和分发记录
"""
import sqlite3
import json
import base64
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet


class Database:
    """数据库管理类"""

    _master_key = b'oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ='  # 固定密钥（32字节 url-safe base64）
    _cipher = Fernet(_master_key)
    _db_path = 'watermark.db'

    @classmethod
    def get_db_path(cls) -> Path:
        """获取数据库文件路径"""
        return Path(cls._db_path)

    @classmethod
    def initialize(cls):
        """初始化数据库"""
        with sqlite3.connect(cls._db_path) as conn:
            cursor = conn.cursor()

            # 创建密钥表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keys (
                    id INTEGER PRIMARY KEY,
                    key_name TEXT UNIQUE NOT NULL,
                    key_password BLOB NOT NULL,
                    salt BLOB NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建分发记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trace_logs (
                    id INTEGER PRIMARY KEY,
                    uid TEXT NOT NULL,
                    user_info TEXT NOT NULL,
                    department TEXT,
                    project TEXT,
                    key_name TEXT,
                    original_filename TEXT,
                    watermark_hash TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    @classmethod
    def _encrypt_password(cls, password: str) -> bytes:
        """加密密码"""
        return cls._cipher.encrypt(password.encode('utf-8'))

    @classmethod
    def _decrypt_password(cls, encrypted_password: bytes) -> str:
        """解密密码"""
        return cls._cipher.decrypt(encrypted_password).decode('utf-8')

    @classmethod
    def add_key(cls, key_name: str, key_password: str, salt: bytes = None) -> bool:
        """
        添加密钥

        Args:
            key_name: 密钥名称
            key_password: 密钥密码
            salt: 盐值

        Returns:
            是否成功
        """
        if salt is None:
            salt = b'docx_watermark_salt_v1'

        encrypted_password = cls._encrypt_password(key_password)

        try:
            with sqlite3.connect(cls._db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO keys (key_name, key_password, salt)
                    VALUES (?, ?, ?)
                ''', (key_name, encrypted_password, salt))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    @classmethod
    def get_key(cls, key_name: str) -> dict:
        """
        获取密钥信息

        Args:
            key_name: 密钥名称

        Returns:
            密钥信息字典，未找到返回 None
        """
        with sqlite3.connect(cls._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, key_name, key_password, salt, created_at
                FROM keys WHERE key_name = ?
            ''', (key_name,))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'key_name': row['key_name'],
                    'password': cls._decrypt_password(row['key_password']),
                    'salt': row['salt'],
                    'created_at': row['created_at']
                }
            return None

    @classmethod
    def list_keys(cls) -> list:
        """
        列出所有密钥

        Returns:
            密钥列表
        """
        with sqlite3.connect(cls._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, key_name, created_at
                FROM keys ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()

            return [
                {
                    'id': row['id'],
                    'key_name': row['key_name'],
                    'created_at': row['created_at']
                }
                for row in rows
            ]

    @classmethod
    def delete_key(cls, key_name: str) -> bool:
        """
        删除密钥

        Args:
            key_name: 密钥名称

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(cls._db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM keys WHERE key_name = ?', (key_name,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    @classmethod
    def export_key(cls, key_name: str, export_path: str) -> bool:
        """
        导出密钥到文件

        Args:
            key_name: 密钥名称
            export_path: 导出文件路径

        Returns:
            是否成功
        """
        key_data = cls.get_key(key_name)
        if not key_data:
            return False

        try:
            export_data = {
                'key_name': key_data['key_name'],
                'password': key_data['password'],
                'salt': base64.b64encode(key_data['salt']).decode('utf-8'),
                'created_at': key_data['created_at']
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    @classmethod
    def import_key(cls, import_path: str) -> bool:
        """
        从文件导入密钥

        Args:
            import_path: 导入文件路径

        Returns:
            是否成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            salt = base64.b64decode(import_data['salt'].encode('utf-8'))
            return cls.add_key(
                import_data['key_name'],
                import_data['password'],
                salt
            )
        except Exception:
            return False

    @classmethod
    def add_trace_log(cls, uid: str, user_info: str, department: str = '',
                      project: str = '', key_name: str = '',
                      original_filename: str = '') -> int:
        """
        添加分发记录

        Args:
            uid: 唯一标识
            user_info: 用户信息
            department: 部门
            project: 项目
            key_name: 密钥名称
            original_filename: 原始文件名

        Returns:
            记录 ID，失败返回 -1
        """
        try:
            with sqlite3.connect(cls._db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trace_logs (uid, user_info, department, project, key_name, original_filename)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (uid, user_info, department, project, key_name, original_filename))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            return -1

    @classmethod
    def list_trace_logs(cls, limit: int = 100) -> list:
        """
        列出分发记录

        Args:
            limit: 返回记录数量限制

        Returns:
            记录列表
        """
        with sqlite3.connect(cls._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, uid, user_info, department, project, key_name, original_filename, created_at
                FROM trace_logs ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()

            return [
                {
                    'id': row['id'],
                    'uid': row['uid'],
                    'user_info': row['user_info'],
                    'department': row['department'],
                    'project': row['project'],
                    'key_name': row['key_name'],
                    'original_filename': row['original_filename'],
                    'created_at': row['created_at']
                }
                for row in rows
            ]

    @classmethod
    def get_trace_log_by_uid(cls, uid: str) -> dict:
        """
        根据 UID 获取分发记录

        Args:
            uid: 唯一标识

        Returns:
            记录字典，未找到返回 None
        """
        with sqlite3.connect(cls._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, uid, user_info, department, project, key_name, original_filename, created_at
                FROM trace_logs WHERE uid = ?
            ''', (uid,))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'uid': row['uid'],
                    'user_info': row['user_info'],
                    'department': row['department'],
                    'project': row['project'],
                    'key_name': row['key_name'],
                    'original_filename': row['original_filename'],
                    'created_at': row['created_at']
                }
            return None


class KeyManager:
    """密钥管理器（高级封装）"""

    @staticmethod
    def create_new_key(key_name: str, password: str = None) -> bool:
        """
        创建新密钥

        Args:
            key_name: 密钥名称
            password: 密钥密码，默认自动生成

        Returns:
            是否成功
        """
        if password is None:
            import secrets
            password = secrets.token_urlsafe(16)

        return Database.add_key(key_name, password)

    @staticmethod
    def validate_key(key_name: str, password: str) -> bool:
        """
        验证密钥密码

        Args:
            key_name: 密钥名称
            password: 密钥密码

        Returns:
            是否有效
        """
        key_data = Database.get_key(key_name)
        return key_data and key_data['password'] == password

    @staticmethod
    def export_all_keys(export_dir: str) -> list:
        """
        导出所有密钥到指定目录

        Args:
            export_dir: 导出目录

        Returns:
            导出成功文件列表
        """
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        keys = Database.list_keys()
        exported_files = []

        for key in keys:
            filename = f"key_{key['key_name']}.json"
            file_path = export_path / filename
            if Database.export_key(key['key_name'], str(file_path)):
                exported_files.append(str(file_path))

        return exported_files