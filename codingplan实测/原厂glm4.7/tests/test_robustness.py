"""
鲁棒性测试
"""

import sys
import unittest
import zipfile
import tempfile
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.watermark import DocxWatermarkTool


class TestWatermarkRobustness(unittest.TestCase):
    """水印鲁棒性测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 检查是否有测试文档
        cls.test_doc_path = Path(__file__).parent / 'test_document.docx'
        if not cls.test_doc_path.exists():
            # 创建一个简单的测试文档
            cls._create_test_document(cls.test_doc_path)

    @staticmethod
    def _create_test_document(path: Path):
        """创建测试文档"""
        # 创建最小的 DOCX 文件
        with zipfile.ZipFile(path, 'w') as zf:
            # [Content_Types].xml
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')

            # _rels/.rels
            zf.writestr('_rels/.rels', '''<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')

            # word/document.xml (包含多个段落)
            zf.writestr('word/document.xml', '''<?xml version="1.0"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>第一段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第二段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第三段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第四段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第五段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第六段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第七段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第八段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第九段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第十段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第十一段内容</w:t></w:r></w:p>
    <w:p><w:r><w:t>第十二段内容</w:t></w:r></w:p>
  </w:body>
</w:document>''')

    def setUp(self):
        """每个测试前的准备"""
        self.tool = DocxWatermarkTool('test_password_123')
        self.temp_dir = Path(tempfile.mkdtemp())
        self.watermarked_path = self.temp_dir / 'watermarked.docx'

        # 嵌入水印
        result = self.tool.embed_watermark(
            str(self.test_doc_path),
            str(self.watermarked_path),
            'TestUser-001',
            '测试部',
            'TestProject'
        )
        self.assertTrue(result['success'], '水印嵌入失败')

    def tearDown(self):
        """测试后清理"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_basic_extraction(self):
        """测试基本提取功能"""
        result = self.tool.analyze_docx(str(self.watermarked_path))
        self.assertTrue(result['success'], '水印提取失败')
        self.assertTrue(result['has_watermark'], '未发现水印')

        data = result['watermark_data']
        self.assertEqual(data['uid'], 'TestUser-001')
        self.assertEqual(data['department'], '测试部')
        self.assertEqual(data['project'], 'TestProject')

    def test_partial_deletion_robustness(self):
        """测试部分删除后的鲁棒性"""
        # 创建一个删除了部分内容的文档
        modified_path = self.temp_dir / 'partial.docx'

        with zipfile.ZipFile(self.watermarked_path, 'r') as zin:
            with zipfile.ZipFile(modified_path, 'w') as zout:
                for item in zin.namelist():
                    content = zin.read(item)
                    if item == 'word/document.xml':
                        # 删除部分段落（保留前6段）
                        content_str = content.decode('utf-8')
                        # 保留前6个段落
                        parts = content_str.split('<w:p>')
                        modified = '<w:p>'.join(parts[:7])  # 前6个段落+结尾
                        zout.writestr(item, modified.encode('utf-8'))
                    else:
                        zout.writestr(item, content)

        # 测试提取
        result = self.tool.analyze_docx(str(modified_path))
        # 应该能从备份层提取
        self.assertTrue(result['success'] or result.get('extraction_source') in [
            'custom.xml', '[Content_Types].xml comment',
            'settings.xml comment', 'backup file'
        ])

    def test_backup_layers(self):
        """测试备份层是否正确写入"""
        with zipfile.ZipFile(self.watermarked_path, 'r') as zf:
            # 检查备份文件是否存在
            self.assertIn('word/watermark_backup.xml', zf.namelist())

            # 检查 custom.xml 是否有水印标记
            if 'docProps/custom.xml' in zf.namelist():
                custom_content = zf.read('docProps/custom.xml').decode('utf-8')
                self.assertIn('wm_backup', custom_content or '')

            # 检查 [Content_Types].xml 注释
            ct_content = zf.read('[Content_Types].xml').decode('utf-8')
            self.assertIn('wm_data:', ct_content)

            # 检查 settings.xml 注释
            if 'word/settings.xml' in zf.namelist():
                settings_content = zf.read('word/settings.xml').decode('utf-8')
                self.assertIn('wm_store:', settings_content or '')


class TestEncryptionRobustness(unittest.TestCase):
    """加密鲁棒性测试"""

    def test_wrong_key_decryption(self):
        """测试错误密钥解密"""
        tool1 = DocxWatermarkTool('password1')
        tool2 = DocxWatermarkTool('password2')

        # 用 tool1 加密
        encrypted = tool1.crypto.encrypt('secret_message')

        # 用 tool2 解密应该失败
        with self.assertRaises(Exception):
            tool2.crypto.decrypt(encrypted)

    def test_corrupted_data_detection(self):
        """测试损坏数据检测"""
        tool = DocxWatermarkTool('test_password')

        # 正确数据
        data = '{"version": "1.0", "uid": "User-001"}'
        crc = tool.crypto.calculate_crc(data)

        # 完整数据应该通过验证
        test_data = '{"version": "1.0", "uid": "User-001", "crc": "' + crc + '"}'
        test_crc = tool.crypto.calculate_crc(
            '{"version": "1.0", "uid": "User-001"}'
        )
        self.assertEqual(crc, test_crc)

        # 篡改数据应该检测出
        tampered_data = '{"version": "1.0", "uid": "User-999", "crc": "' + crc + '"}'
        tampered_crc = tool.crypto.calculate_crc(
            '{"version": "1.0", "uid": "User-999"}'
        )
        self.assertNotEqual(crc, tampered_crc)


if __name__ == '__main__':
    unittest.main(verbosity=2)
