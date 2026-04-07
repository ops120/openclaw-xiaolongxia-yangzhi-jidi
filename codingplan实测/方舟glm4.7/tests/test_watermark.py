"""
水印功能测试
"""

import unittest
import tempfile
from pathlib import Path

from src.core.watermark import DocxWatermarkTool, DEFAULT_PASSWORD
from src.core.crypto import CryptoManager


class TestCryptoManager(unittest.TestCase):
    """加密管理器测试"""

    def test_derive_key(self):
        """测试密钥派生"""
        password = "test_password"
        salt = b"test_salt"
        key = CryptoManager.derive_key(password, salt)

        self.assertIsNotNone(key)
        self.assertEqual(len(key), 44)  # 32字节 base64编码后为44字符

    def test_get_cipher(self):
        """测试获取加密器"""
        key = b'oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ='
        cipher = CryptoManager.get_cipher(key)

        self.assertIsNotNone(cipher)

    def test_generate_key(self):
        """测试生成随机密钥"""
        key1 = CryptoManager.generate_key()
        key2 = CryptoManager.generate_key()

        self.assertNotEqual(key1, key2)
        self.assertEqual(len(key1), 44)


class TestDocxWatermarkTool(unittest.TestCase):
    """水印工具测试"""

    def setUp(self):
        """测试前准备"""
        self.tool = DocxWatermarkTool(master_password=DEFAULT_PASSWORD)
        self.test_docx = None  # 需要实际的测试文档

    def test_tool_initialization(self):
        """测试工具初始化"""
        self.assertIsNotNone(self.tool)
        self.assertIsNotNone(self.tool.master_key)
        self.assertIsNotNone(self.tool.cipher)

    def test_calculate_crc(self):
        """测试CRC计算"""
        data = "test_data"
        crc1 = self.tool._calculate_crc(data)
        crc2 = self.tool._calculate_crc(data)

        self.assertEqual(crc1, crc2)
        self.assertEqual(len(crc1), 4)

    def test_build_watermark_data(self):
        """测试构建水印数据"""
        user_info = "张三-123"
        department = "销售部"
        project = "ProjectA"

        data = self.tool._build_watermark_data(user_info, department, project)

        self.assertIn('version', data)
        self.assertIn('uid', data)
        self.assertIn('department', data)
        self.assertIn('project', data)
        self.assertIn('timestamp', data)
        self.assertIn('crc', data)

        self.assertEqual(data['uid'], user_info)
        self.assertEqual(data['department'], department)
        self.assertEqual(data['project'], project)

    def test_text_to_zw_string(self):
        """测试文本到零宽字符转换"""
        text = "test_message"
        zw_string = self.tool._text_to_zw_string(text)

        self.assertNotIn('\u200d', zw_string)  # 不包含其他零宽字符
        self.assertTrue(all(c in '\u200b\u200c' for c in zw_string))

    def test_zw_string_to_text(self):
        """测试零宽字符到文本转换"""
        text = "test_message"
        zw_string = self.tool._text_to_zw_string(text)
        recovered_text = self.tool._zw_string_to_text(zw_string)

        self.assertEqual(text, recovered_text)

    def test_crc_verification(self):
        """测试CRC校验"""
        data = {"key": "value"}

        # 计算CRC
        crc1 = self.tool._calculate_crc('{"key": "value"}')

        # 修改数据
        data["crc"] = crc1
        json_str = '{"key": "value", "crc": "' + crc1 + '""}'

        # 验证
        json_obj = eval(json_str)
        stored_crc = json_obj.pop("crc")
        calculated_crc = self.tool._calculate_crc(str(json_obj))

        self.assertEqual(stored_crc, calculated_crc)


class TestWatermarkEmbedding(unittest.TestCase):
    """水印嵌入测试（需要实际文档）"""

    def setUp(self):
        """测试前准备"""
        self.tool = DocxWatermarkTool(master_password=DEFAULT_PASSWORD)

    def test_embed_without_document(self):
        """测试无文档时的错误处理"""
        result = self.tool.embed_watermark(
            "nonexistent.docx",
            "output.docx",
            "test_user"
        )

        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])


if __name__ == '__main__':
    unittest.main()
