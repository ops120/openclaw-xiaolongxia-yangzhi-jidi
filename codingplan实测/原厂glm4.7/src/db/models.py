"""
数据库模块 - 密钥和记录管理
"""

import sqlite3
import json
import base64
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet


class Database:
    """数据库连接管理"""

    # 固定的数据库加密密钥（32字节 url-safe base64）
    _master_key = b'oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ='
    _cipher = Fernet(_master_key)

    def __init__(self, db_path: str = 'watermark.db'):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.connect()
        self._init_tables()

    def connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()

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

        # 创建分发记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                user_info TEXT NOT NULL,
                key_id INTEGER,
                original_filename TEXT,
                watermark_hash TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (key_id) REFERENCES keys(id)
            )
        ''')

        self.conn.commit()

    def _encrypt_password(self, password: str) -> str:
        """加密密钥密码"""
        encrypted = self._cipher.encrypt(password.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('ascii')

    def _decrypt_password(self, encrypted_password: str) -> str:
        """解密密钥密码"""
        encrypted = base64.urlsafe_b64decode(encrypted_password.encode('ascii'))
        decrypted = self._cipher.decrypt(encrypted)
        return decrypted.decode('utf-8')


class KeyManager:
    """密钥管理器"""

    def __init__(self, database: Database):
        """
        初始化密钥管理器

        Args:
            database: 数据库实例
        """
        self.db = database

    def create_key(self, key_name: str, password: str, salt: str = 'default_salt') -> int:
        """
        创建新密钥

        Args:
            key_name: 密钥名称
            password: 密钥密码
            salt: 盐值

        Returns:
            新创建密钥的 ID
        """
        cursor = self.db.conn.cursor()
        encrypted_password = self.db._encrypt_password(password)

        try:
            cursor.execute('''
                INSERT INTO keys (key_name, key_password, salt)
                VALUES (?, ?, ?)
            ''', (key_name, encrypted_password, salt))
            self.db.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"密钥名称 '{key_name}' 已存在")

    def get_all_keys(self) -> list:
        """获取所有密钥"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id, key_name, created_at FROM keys ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

    def get_key_by_name(self, key_name: str) -> dict:
        """根据名称获取密钥"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, key_name, key_password, salt, created_at
            FROM keys WHERE key_name = ?
        ''', (key_name,))
        row = cursor.fetchone()

        if row:
            key_data = dict(row)
            key_data['key_password'] = self.db._decrypt_password(key_data['key_password'])
            return key_data
        return None

    def get_key_by_id(self, key_id: int) -> dict:
        """根据 ID 获取密钥"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, key_name, key_password, salt, created_at
            FROM keys WHERE id = ?
        ''', (key_id,))
        row = cursor.fetchone()

        if row:
            key_data = dict(row)
            key_data['key_password'] = self.db._decrypt_password(key_data['key_password'])
            return key_data
        return None

    def delete_key(self, key_name: str) -> bool:
        """删除密钥"""
        cursor = self.db.conn.cursor()
        cursor.execute('DELETE FROM keys WHERE key_name = ?', (key_name,))
        self.db.conn.commit()
        return cursor.rowcount > 0

    def export_keys(self, output_path: str) -> dict:
        """
        导出密钥到文件

        Args:
            output_path: 输出文件路径

        Returns:
            导出结果
        """
        keys = self.get_all_keys()
        export_data = []

        for key in keys:
            key_detail = self.get_key_by_name(key['key_name'])
            export_data.append({
                'key_name': key_detail['key_name'],
                'password': key_detail['key_password'],
                'salt': key_detail['salt'],
                'created_at': key['created_at']
            })

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return {'success': True, 'count': len(export_data)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_keys(self, input_path: str) -> dict:
        """
        从文件导入密钥

        Args:
            input_path: 输入文件路径

        Returns:
            导入结果
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            imported_count = 0
            skipped_count = 0

            for key_data in import_data:
                try:
                    self.create_key(
                        key_data['key_name'],
                        key_data['password'],
                        key_data.get('salt', 'default_salt')
                    )
                    imported_count += 1
                except ValueError:
                    skipped_count += 1

            return {
                'success': True,
                'imported': imported_count,
                'skipped': skipped_count
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


class TraceLogManager:
    """分发记录管理器"""

    def __init__(self, database: Database):
        """
        初始化记录管理器

        Args:
            database: 数据库实例
        """
        self.db = database

    def add_log(self, uid: str, user_info: str, key_id: int,
                original_filename: str, watermark_hash: str) -> int:
        """
        添加分发记录

        Args:
            uid: 用户ID
            user_info: 用户信息
            key_id: 密钥ID
            original_filename: 原始文件名
            watermark_hash: 水印哈希

        Returns:
            新记录的 ID
        """
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO trace_logs (uid, user_info, key_id, original_filename, watermark_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (uid, user_info, key_id, original_filename, watermark_hash))
        self.db.conn.commit()
        return cursor.lastrowid

    def get_all_logs(self) -> list:
        """获取所有记录"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT l.id, l.uid, l.user_info, l.original_filename,
                   l.watermark_hash, l.created_at, k.key_name
            FROM trace_logs l
            LEFT JOIN keys k ON l.key_id = k.id
            ORDER BY l.created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_log_by_uid(self, uid: str) -> dict:
        """根据 UID 获取记录"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT l.id, l.uid, l.user_info, l.original_filename,
                   l.watermark_hash, l.created_at, k.key_name
            FROM trace_logs l
            LEFT JOIN keys k ON l.key_id = k.id
            WHERE l.uid = ?
        ''', (uid,))
        row = cursor.fetchone()

        return dict(row) if row else None
