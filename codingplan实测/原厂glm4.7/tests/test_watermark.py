"""
水印功能测试
"""

import sys
import unittest
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.watermark import DocxWatermarkTool


class TestWatermark(unittest.TestCase):
    """水印功能测试"""

    def setUp(self):
        """测试前准备"""
        self.tool = DocxWatermarkTool('test_password_123')
        self.test_data = {
            'user_info': 'TestUser-001',
            'department': '测试部',
            'project': 'TestProject'
        }

    def test_encryption_decryption(self):
        """测试加密解密"""
        # 测试加密
        encrypted = self.tool.crypto.encrypt('test_message')
        self.assertIsNotNone(encrypted)

        # 测试解密
        decrypted = self.tool.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, 'test_message')

    def test_zero_width_conversion(self):
        """测试零宽字符转换"""
        # 文本转零宽字符
        test_text = 'Hello World'
        zw_string = self.tool._text_to_zw_string(test_text)
        self.assertIsNotNone(zw_string)
        # 零宽字符应该只包含零宽字符
        self.assertTrue(all(c in '\u200b\u200c' for c in zw_string))

        # 零宽字符转回文本
        recovered_text = self.tool._zw_string_to_text(zw_string)
        self.assertEqual(recovered_text, test_text)

    def test_watermark_data_structure(self):
        """测试水印数据结构"""
        data = self.tool._build_watermark_data(
            self.test_data['user_info'],
            self.test_data['department'],
            self.test_data['project']
        )

        self.assertIn('version', data)
        self.assertIn('uid', data)
        self.assertIn('department', data)
        self.assertIn('timestamp', data)
        self.assertIn('project', data)
        self.assertIn('crc', data)

        self.assertEqual(data['uid'], self.test_data['user_info'])
        self.assertEqual(data['department'], self.test_data['department'])
        self.assertEqual(data['project'], self.test_data['project'])

    def test_crc_calculation(self):
        """测试 CRC 计算"""
        data = '{"test": "data"}'
        crc1 = self.tool.crypto.calculate_crc(data)
        crc2 = self.tool.crypto.calculate_crc(data)
        self.assertEqual(crc1, crc2)

        # 不同数据应产生不同 CRC
        crc3 = self.tool.crypto.calculate_crc('{"test": "other"}')
        self.assertNotEqual(crc1, crc3)

    def test_base64_conversion(self):
        """测试 base64 转换（用于备份数据）"""
        test_data = '{"test": "backup_data"}'

        # 转为 base64
        b64_data = self.tool.crypto.text_to_base64(test_data)
        self.assertIsNotNone(b64_data)
        # base64 应该只包含安全字符
        self.assertTrue(all(c.isalnum() or c in '-_=' for c in b64_data))

        # 从 base64 还原
        recovered = self.tool.crypto.base64_to_text(b64_data)
        self.assertEqual(recovered, test_data)


class TestWatermarkExtraction(unittest.TestCase):
    """水印提取测试"""

    def setUp(self):
        """测试前准备"""
        self.tool = DocxWatermarkTool('test_password_123')

    def test_extract_from_zero_width_string(self):
        """测试从零宽字符字符串提取"""
        # 创建测试数据
        test_json = '{"version": "1.0", "uid": "TestUser-001", "crc": "ABCD"}'
        zw_string = self.tool._text_to_zw_string(test_json)

        # 提取并验证
        extracted = self.tool._zw_string_to_text(zw_string)
        self.assertEqual(extracted, test_json)

    def test_extract_from_base64_backup(self):
        """测试从 base64 备份提取"""
        # 创建测试数据
        test_json = '{"version": "1.0", "uid": "TestUser-001", "crc": "ABCD"}'
        b64_data = self.tool.crypto.text_to_base64(test_json)

        # 提取并验证
        extracted = self.tool.crypto.base64_to_text(b64_data)
        self.assertEqual(extracted, test_json)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
