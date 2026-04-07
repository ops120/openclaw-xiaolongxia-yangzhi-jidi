# -*- coding: utf-8 -*-
"""
数据模型 - 密钥管理和分发记录
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from cryptography.fernet import Fernet

from ..core.crypto import CryptoManager


class Database:
    """
    数据库管理类

    使用 SQLite 存储密钥和分发记录
    """

    # 固定的数据库加密密钥（用于加密存储的密钥密码）
    _master_key = b'oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ='
    _cipher = Fernet(_master_key)

    def __init__(self, db_path: str = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认为程序目录下的 watermark.db
        """
        if db_path is None:
            # 默认路径
            db_path = Path(__file__).parent.parent.parent / 'watermark.db'

        self.db_path = str(db_path)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建密钥表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT UNIQUE NOT NULL,
                key_password_encrypted BLOB NOT NULL,
                salt BLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建分发记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE NOT NULL,
                user_info TEXT NOT NULL,
                department TEXT,
                project TEXT,
                key_id INTEGER,
                original_filename TEXT,
                output_filename TEXT,
                watermark_hash TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (key_id) REFERENCES keys(id)
            )
        ''')

        # 创建审计日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                user_info TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def _encrypt_password(self, password: str) -> bytes:
        """加密密码存储"""
        return self._cipher.encrypt(password.encode('utf-8'))

    def _decrypt_password(self, encrypted: bytes) -> str:
        """解密密码"""
        return self._cipher.decrypt(encrypted).decode('utf-8')


class KeyManager:
    """密钥管理器"""

    def __init__(self, db: Database):
        """
        初始化密钥管理器

        Args:
            db: 数据库实例
        """
        self.db = db

    def create_key(self, key_name: str, password: str) -> Dict[str, Any]:
        """
        创建新密钥

        Args:
            key_name: 密钥名称
            password: 密钥密码

        Returns:
            创建结果

        Raises:
            ValueError: 密钥名称已存在
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # 检查是否已存在
            cursor.execute('SELECT id FROM keys WHERE key_name = ?', (key_name,))
            if cursor.fetchone():
                raise ValueError(f'密钥名称 "{key_name}" 已存在')

            # 加密密码
            encrypted_password = self.db._encrypt_password(password)

            # 插入数据库
            cursor.execute('''
                INSERT INTO keys (key_name, key_password_encrypted)
                VALUES (?, ?)
            ''', (key_name, encrypted_password))

            key_id = cursor.lastrowid
            conn.commit()

            return {
                'id': key_id,
                'key_name': key_name,
                'created_at': datetime.now().isoformat()
            }
        finally:
            conn.close()

    def get_key(self, key_name: str) -> Optional[Dict[str, Any]]:
        """
        获取密钥信息

        Args:
            key_name: 密钥名称

        Returns:
            密钥信息字典，不存在返回 None
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, key_name, key_password_encrypted, created_at
                FROM keys WHERE key_name = ?
            ''', (key_name,))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'key_name': row['key_name'],
                    'password': self.db._decrypt_password(row['key_password_encrypted']),
                    'created_at': row['created_at']
                }
            return None
        finally:
            conn.close()

    def get_all_keys(self) -> List[Dict[str, Any]]:
        """
        获取所有密钥列表

        Returns:
            密钥列表
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, key_name, created_at, updated_at
                FROM keys ORDER BY created_at DESC
            ''')

            keys = []
            for row in cursor.fetchall():
                keys.append({
                    'id': row['id'],
                    'key_name': row['key_name'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            return keys
        finally:
            conn.close()

    def delete_key(self, key_name: str) -> bool:
        """
        删除密钥

        Args:
            key_name: 密钥名称

        Returns:
            是否删除成功
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM keys WHERE key_name = ?', (key_name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def export_key(self, key_name: str) -> Optional[str]:
        """
        导出密钥为 JSON 字符串

        Args:
            key_name: 密钥名称

        Returns:
            JSON 字符串，不存在返回 None
        """
        key = self.get_key(key_name)
        if key:
            export_data = {
                'key_name': key['key_name'],
                'password': key['password'],
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        return None

    def import_key(self, json_data: str) -> Dict[str, Any]:
        """
        从 JSON 字符串导入密钥

        Args:
            json_data: JSON 格式的密钥数据

        Returns:
            导入结果

        Raises:
            ValueError: 数据格式错误或密钥已存在
        """
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            raise ValueError('无效的 JSON 格式')

        required_fields = ['key_name', 'password']
        for field in required_fields:
            if field not in data:
                raise ValueError(f'缺少必需字段: {field}')

        return self.create_key(data['key_name'], data['password'])

    def key_exists(self, key_name: str) -> bool:
        """检查密钥是否存在"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id FROM keys WHERE key_name = ?', (key_name,))
            return cursor.fetchone() is not None
        finally:
            conn.close()


class TraceLogManager:
    """分发记录管理器"""

    def __init__(self, db: Database):
        """
        初始化分发记录管理器

        Args:
            db: 数据库实例
        """
        self.db = db

    def add_log(self, uid: str, user_info: str, department: str = '',
                project: str = '', key_id: int = None,
                original_filename: str = '', output_filename: str = '',
                watermark_hash: str = '') -> Dict[str, Any]:
        """
        添加分发记录

        Args:
            uid: 唯一标识
            user_info: 用户信息
            department: 部门
            project: 项目
            key_id: 使用的密钥ID
            original_filename: 原始文件名
            output_filename: 输出文件名
            watermark_hash: 水印哈希

        Returns:
            创建的记录
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO trace_logs
                (uid, user_info, department, project, key_id,
                 original_filename, output_filename, watermark_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uid, user_info, department, project, key_id,
                  original_filename, output_filename, watermark_hash))

            log_id = cursor.lastrowid
            conn.commit()

            return {
                'id': log_id,
                'uid': uid,
                'user_info': user_info,
                'created_at': datetime.now().isoformat()
            }
        finally:
            conn.close()

    def get_log_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        根据 UID 获取记录

        Args:
            uid: 唯一标识

        Returns:
            记录字典，不存在返回 None
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM trace_logs WHERE uid = ?
            ''', (uid,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def search_logs(self, user_info: str = '', department: str = '',
                    project: str = '') -> List[Dict[str, Any]]:
        """
        搜索分发记录

        Args:
            user_info: 用户信息（模糊匹配）
            department: 部门
            project: 项目

        Returns:
            匹配的记录列表
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            query = 'SELECT * FROM trace_logs WHERE 1=1'
            params = []

            if user_info:
                query += ' AND user_info LIKE ?'
                params.append(f'%{user_info}%')

            if department:
                query += ' AND department = ?'
                params.append(department)

            if project:
                query += ' AND project = ?'
                params.append(project)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取所有分发记录

        Args:
            limit: 返回数量限制

        Returns:
            记录列表
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM trace_logs
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_log(self, log_id: int) -> bool:
        """
        删除分发记录

        Args:
            log_id: 记录ID

        Returns:
            是否删除成功
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM trace_logs WHERE id = ?', (log_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
