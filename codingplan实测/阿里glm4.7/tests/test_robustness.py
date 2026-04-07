"""
鲁棒性测试 - 测试水印在各种场景下的可用性
"""
import unittest
import tempfile
import shutil
import zipfile
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.watermark import WatermarkEngine


class RobustnessTestCase(unittest.TestCase):
    """鲁棒性测试基类"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_docx = self._create_test_docx()
        self.engine = WatermarkEngine(password='test_password')
        self.watermarked_docx = self._create_watermarked_docx()

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def _create_test_docx(self):
        """创建测试文档"""
        docx_path = Path(self.temp_dir) / "test.docx"

        document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>段落1</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落2</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落3</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落4</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落5</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落6</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落7</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落8</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落9</w:t></w:r></w:p>
    <w:p><w:r><w:t>段落10</w:t></w:r></w:p>
  </w:body>
</w:document>'''

        content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

        rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

        with ZipFile(docx_path, 'w') as zf:
            zf.writestr('[Content_Types].xml', content_types_xml)
            zf.writestr('_rels/.rels', rels_xml)
            zf.writestr('word/document.xml', document_xml)

        return str(docx_path)

    def _create_watermarked_docx(self):
        """创建带水印的测试文档"""
        output_path = Path(self.temp_dir) / "watermarked.docx"
        self.engine.embed_watermark(
            input_path=self.test_docx,
            output_path=str(output_path),
            user_info="TestUser-001",
            department="TestDept",
            project="TestProject"
        )
        return str(output_path)


class TestPartialDeletion(RobustnessTestCase):
    """测试部分删除后的水印提取"""

    def test_delete_some_paragraphs(self):
        """测试删除部分段落"""
        output_path = Path(self.temp_dir) / "modified.docx"

        # 读取并修改文档
        with zipfile.ZipFile(self.watermarked_docx, 'r') as zin:
            with zipfile.ZipFile(output_path, 'w') as zout:
                for item in zin.namelist():
                    if item == 'word/document.xml':
                        content = zin.read(item).decode('utf-8')
                        # 删除部分段落
                        modified = content.replace('<w:p><w:r><w:t>段落1</w:t></w:r></w:p>', '')
                        modified = modified.replace('<w:p><w:r><w:t>段落2</w:t></w:r></w:p>', '')
                        zout.writestr(item, modified.encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item))

        # 提取水印
        result = self.engine.extract_watermark(str(output_path))

        # 应该能从备份层提取
        self.assertTrue(result['success'])
        self.assertTrue(result['has_watermark'])


class TestBackupLayerExtraction(RobustnessTestCase):
    """测试备份层提取"""

    def test_extract_from_custom_xml(self):
        """测试从 custom.xml 提取"""
        output_path = Path(self.temp_dir) / "modified.docx"

        # 清除零宽字符（模拟 WPS/Word 清除零宽字符）
        with zipfile.ZipFile(self.watermarked_docx, 'r') as zin:
            with zipfile.ZipFile(output_path, 'w') as zout:
                for item in zin.namelist():
                    if item == 'word/document.xml':
                        content = zin.read(item).decode('utf-8')
                        # 移除所有零宽字符
                        modified = content.replace('\u200b', '').replace('\u200c', '')
                        zout.writestr(item, modified.encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item))

        result = self.engine.extract_watermark(str(output_path))

        self.assertTrue(result['success'])
        self.assertTrue(result['has_watermark'])
        self.assertEqual(result['source'], 'docProps/custom.xml')

    def test_extract_from_content_types(self):
        """测试从 [Content_Types].xml 提取"""
        output_path = Path(self.temp_dir) / "modified.docx"

        # 清除 document.xml 和 custom.xml 中的水印
        with zipfile.ZipFile(self.watermarked_docx, 'r') as zin:
            with zipfile.ZipFile(output_path, 'w') as zout:
                for item in zin.namelist():
                    if item == 'word/document.xml':
                        content = zin.read(item).decode('utf-8')
                        modified = content.replace('\u200b', '').replace('\u200c', '')
                        zout.writestr(item, modified.encode('utf-8'))
                    elif item == 'docProps/custom.xml':
                        # 移除水印属性
                        original = zin.read(item).decode('utf-8')
                        modified = original.replace('wm_backup', 'wm_backup_removed')
                        zout.writestr(item, modified.encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item))

        result = self.engine.extract_watermark(str(output_path))

        self.assertTrue(result['success'])
        self.assertTrue(result['has_watermark'])
        self.assertEqual(result['source'], '[Content_Types].xml')

    def test_extract_from_settings_xml(self):
        """测试从 settings.xml 提取"""
        output_path = Path(self.temp_dir) / "modified.docx"

        # 清除前三层备份
        with zipfile.ZipFile(self.watermarked_docx, 'r') as zin:
            with zipfile.ZipFile(output_path, 'w') as zout:
                for item in zin.namelist():
                    if item == 'word/document.xml':
                        content = zin.read(item).decode('utf-8')
                        modified = content.replace('\u200b', '').replace('\u200c', '')
                        zout.writestr(item, modified.encode('utf-8'))
                    elif item == 'docProps/custom.xml':
                        original = zin.read(item).decode('utf-8')
                        modified = original.replace('wm_backup', 'wm_backup_removed')
                        zout.writestr(item, modified.encode('utf-8'))
                    elif item == '[Content_Types].xml':
                        original = zin.read(item).decode('utf-8')
                        modified = original.replace('wm_data:', 'wm_data_removed:')
                        zout.writestr(item, modified.encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item))

        result = self.engine.extract_watermark(str(output_path))

        self.assertTrue(result['success'])
        self.assertTrue(result['has_watermark'])
        self.assertEqual(result['source'], 'word/settings.xml')

    def test_extract_from_backup_file(self):
        """测试从独立备份文件提取"""
        output_path = Path(self.temp_dir) / "modified.docx"

        # 清除所有文档中的水印，保留备份文件
        with zipfile.ZipFile(self.watermarked_docx, 'r') as zin:
            with zipfile.ZipFile(output_path, 'w') as zout:
                for item in zin.namelist():
                    if item == 'word/document.xml':
                        content = zin.read(item).decode('utf-8')
                        modified = content.replace('\u200b', '').replace('\u200c', '')
                        zout.writestr(item, modified.encode('utf-8'))
                    elif item == 'docProps/custom.xml':
                        original = zin.read(item).decode('utf-8')
                        modified = original.replace('wm_backup', 'wm_backup_removed')
                        zout.writestr(item, modified.encode('utf-8'))
                    elif item == '[Content_Types].xml':
                        original = zin.read(item).decode('utf-8')
                        modified = original.replace('wm_data:', 'wm_data_removed:')
                        zout.writestr(item, modified.encode('utf-8'))
                    elif item == 'word/settings.xml':
                        original = zin.read(item).decode('utf-8')
                        modified = original.replace('wm_store:', 'wm_store_removed:')
                        zout.writestr(item, modified.encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item))

        result = self.engine.extract_watermark(str(output_path))

        self.assertTrue(result['success'])
        self.assertTrue(result['has_watermark'])
        self.assertEqual(result['source'], 'word/watermark_backup.xml')


class TestMultipleDocuments(RobustnessTestCase):
    """测试多文档场景"""

    def test_batch_embed_and_extract(self):
        """测试批量嵌入和提取"""
        results = []

        for i in range(5):
            # 嵌入
            output_path = Path(self.temp_dir) / f"doc_{i}.docx"
            self.engine.embed_watermark(
                input_path=self.test_docx,
                output_path=str(output_path),
                user_info=f"User-{i}",
                department="TestDept",
                project="TestProject"
            )

            # 提取
            result = self.engine.extract_watermark(str(output_path))
            results.append(result)

        # 验证所有文档都能成功提取
        for i, result in enumerate(results):
            self.assertTrue(result['success'])
            self.assertTrue(result['has_watermark'])
            self.assertEqual(result['watermark_data']['uid'], f"User-{i}")


def run_tests():
    """运行测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestPartialDeletion))
    suite.addTests(loader.loadTestsFromTestCase(TestBackupLayerExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestMultipleDocuments))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)