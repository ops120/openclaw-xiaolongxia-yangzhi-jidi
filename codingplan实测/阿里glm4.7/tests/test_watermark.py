"""
水印功能测试
"""
import unittest
import tempfile
import shutil
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.watermark import WatermarkEngine
from src.core.crypto import CryptoEngine


class TestCryptoEngine(unittest.TestCase):
    """加密引擎测试"""

    def setUp(self):
        """设置测试环境"""
        self.crypto = CryptoEngine(password='test_password')

    def test_encrypt_decrypt(self):
        """测试加密解密"""
        original = "测试文本 Hello World"
        encrypted = self.crypto.encrypt(original)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(original, decrypted)

    def test_crc_calculation(self):
        """测试CRC计算"""
        data = "test data"
        crc1 = self.crypto.calculate_crc(data)
        crc2 = self.crypto.calculate_crc(data)
        self.assertEqual(crc1, crc2)

    def test_validate_crc(self):
        """测试CRC验证"""
        data_dict = {"version": "1.0", "uid": "test"}
        data_dict["crc"] = self.crypto.calculate_crc(data_dict)
        self.assertTrue(CryptoEngine.validate_crc(data_dict))

        # 篡改数据
        data_dict["uid"] = "modified"
        self.assertFalse(CryptoEngine.validate_crc(data_dict))


class TestWatermarkEngine(unittest.TestCase):
    """水印引擎测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_docx = self._create_test_docx()
        self.engine = WatermarkEngine(password='test_password')

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def _create_test_docx(self):
        """创建测试文档"""
        from zipfile import ZipFile

        # 创建简单的 DOCX 文件
        docx_path = Path(self.temp_dir) / "test.docx"

        # document.xml 内容
        document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:b/><w:sz w:val="32"/></w:rPr><w:t>测试文档标题</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>这是一段测试文本，用于验证水印嵌入功能。</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>这是第二段测试文本。</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>这是第三段测试文本。</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>这是第四段测试文本。</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>这是第五段测试文本。</w:t></w:r>
    </w:p>
  </w:body>
</w:document>'''

        # [Content_Types].xml 内容
        content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

        # .rels 内容
        rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

        with ZipFile(docx_path, 'w') as zf:
            zf.writestr('[Content_Types].xml', content_types_xml)
            zf.writestr('_rels/.rels', rels_xml)
            zf.writestr('word/document.xml', document_xml)

        return str(docx_path)

    def test_build_watermark_data(self):
        """测试构建水印数据"""
        data = self.engine.build_watermark_data(
            user_info="张三-123",
            department="销售部",
            project="Project_Alpha"
        )

        self.assertEqual(data['version'], '1.0')
        self.assertEqual(data['uid'], '张三-123')
        self.assertEqual(data['department'], '销售部')
        self.assertEqual(data['project'], 'Project_Alpha')
        self.assertIn('timestamp', data)
        self.assertIn('crc', data)

        # 验证 CRC
        self.assertTrue(self.engine.crypto.validate_crc(data))

    def test_text_to_zw_string_and_back(self):
        """测试零宽字符转换"""
        original = "测试数据"
        zw_string = self.engine.text_to_zw_string(original)
        decoded = self.engine.zw_string_to_text(zw_string)

        self.assertEqual(original, decoded)

    def test_base64_watermark_conversion(self):
        """测试 base64 水印转换"""
        base64_data = self.engine.to_base64_watermark(
            user_info="李四-456",
            department="技术部",
            project="Project_Beta"
        )

        watermark_data = self.engine.from_base64_watermark(base64_data)

        self.assertIsNotNone(watermark_data)
        self.assertEqual(watermark_data['uid'], '李四-456')
        self.assertEqual(watermark_data['department'], '技术部')
        self.assertEqual(watermark_data['project'], 'Project_Beta')

    def test_embed_watermark(self):
        """测试嵌入水印"""
        output_path = Path(self.temp_dir) / "output.docx"

        result = self.engine.embed_watermark(
            input_path=self.test_docx,
            output_path=str(output_path),
            user_info="王五-789",
            department="市场部",
            project="Project_Gamma"
        )

        self.assertTrue(result['success'])
        self.assertGreater(result['paragraphs_processed'], 0)
        self.assertIn('custom.xml', result['backup_written'])
        self.assertTrue(output_path.exists())

    def test_extract_watermark(self):
        """测试提取水印"""
        # 先嵌入水印
        output_path = Path(self.temp_dir) / "output.docx"
        self.engine.embed_watermark(
            input_path=self.test_docx,
            output_path=str(output_path),
            user_info="赵六-999",
            department="财务部",
            project="Project_Delta"
        )

        # 提取水印
        result = self.engine.extract_watermark(str(output_path))

        self.assertTrue(result['success'])
        self.assertTrue(result['has_watermark'])
        self.assertIsNotNone(result['watermark_data'])

        data = result['watermark_data']
        self.assertEqual(data['uid'], '赵六-999')
        self.assertEqual(data['department'], '财务部')
        self.assertEqual(data['project'], 'Project_Delta')

    def test_find_embedding_positions(self):
        """测试查找嵌入位置"""
        xml_content = '<w:p><w:t>文本1</w:t></w:p><w:p><w:t>文本2</w:t></w:p><w:p><w:t>文本3</w:t></w:p>'

        positions = self.engine._find_embedding_positions(xml_content)

        self.assertGreater(len(positions), 0)
        self.assertLessEqual(len(positions), self.engine.EMBED_POSITIONS_STRATEGY['medium'])


def run_tests():
    """运行测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCryptoEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestWatermarkEngine))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)