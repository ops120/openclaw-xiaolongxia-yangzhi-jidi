"""
水印核心模块 - 实现水印嵌入和提取
"""

import json
import re
import zipfile
import base64
from pathlib import Path
from datetime import datetime
from collections import Counter
from lxml import etree

from .crypto import CryptoManager


class DocxWatermarkTool:
    """Docx 智能水印溯源工具核心类"""

    # XML 命名空间
    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
        'cp': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties'
    }

    # 零宽字符映射
    ZERO_WIDTH_MAP = {'0': '\u200b', '1': '\u200c'}  # 零宽空格, 零宽不连通符
    REV_ZERO_WIDTH_MAP = {'\u200b': '0', '\u200c': '1'}

    def __init__(self, master_password: str = None):
        """
        初始化水印工具

        Args:
            master_password: 主密码，用于加密水印数据
        """
        self.crypto = CryptoManager(master_password)

    def _build_watermark_data(self, user_info: str, department: str = '',
                              project: str = '') -> dict:
        """构建水印数据结构"""
        timestamp = datetime.now().isoformat()
        data = {
            "version": "1.0",
            "uid": user_info,
            "department": department,
            "timestamp": timestamp,
            "project": project
        }
        data["crc"] = self.crypto.calculate_crc(json.dumps(data, sort_keys=True))
        return data

    def _text_to_zw_string(self, text: str) -> str:
        """将文本转换为零宽字符字符串"""
        encrypted_data = self.crypto.encrypt(text)
        binary_string = ''.join(format(b, '08b') for b in encrypted_data)
        return ''.join(self.ZERO_WIDTH_MAP[b] for b in binary_string)

    def _zw_string_to_text(self, zw_string: str) -> str:
        """将零宽字符字符串还原为原始文本"""
        binary_string = ''.join(
            self.REV_ZERO_WIDTH_MAP[char]
            for char in zw_string
            if char in self.REV_ZERO_WIDTH_MAP
        )

        if not binary_string or len(binary_string) % 8 != 0:
            return None

        # 将二进制串转回 bytes
        byte_arr = bytearray()
        for i in range(0, len(binary_string), 8):
            byte_arr.append(int(binary_string[i:i+8], 2))

        try:
            return self.crypto.decrypt(bytes(byte_arr))
        except Exception:
            return None  # 密钥不匹配或数据损坏

    def _get_insert_positions(self, root, max_positions: int = 8) -> list:
        """
        获取水印插入位置

        Args:
            root: document.xml 的根节点
            max_positions: 最大插入位置数

        Returns:
            包含 <w:t> 节点的列表
        """
        paragraphs = root.findall('.//w:p', self.NAMESPACES)
        insert_points = []

        # 查找每个段落的最后一个非空 <w:t> 节点
        for para in paragraphs:
            text_nodes = para.findall('.//w:t', self.NAMESPACES)
            if text_nodes:
                for t_node in reversed(text_nodes):
                    if t_node.text and len(t_node.text.strip()) > 0:
                        insert_points.append(t_node)
                        break

        if not insert_points:
            return []

        # 根据段落数量决定嵌入位置数
        num_paragraphs = len(insert_points)
        if num_paragraphs <= 10:
            positions_to_use = min(3, num_paragraphs)
        elif num_paragraphs <= 30:
            positions_to_use = min(5, num_paragraphs)
        else:
            positions_to_use = min(8, num_paragraphs)

        # 从中间开始均匀分布选择位置
        if positions_to_use >= num_paragraphs:
            return insert_points

        step = num_paragraphs // positions_to_use
        start_idx = (num_paragraphs - step * (positions_to_use - 1)) // 2
        selected = []
        for i in range(positions_to_use):
            idx = start_idx + i * step
            if idx < num_paragraphs:
                selected.append(insert_points[idx])

        return selected

    def _add_custom_property(self, root, b64_watermark: str):
        """将水印添加到文档自定义属性"""
        # 查找或创建 Properties 节点
        props = root

        # 添加水印标记
        marker_prop = etree.SubElement(props, 'property')
        marker_prop.set('name', 'wm_marker')
        marker_prop.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
        marker_prop.set('pid', '1')
        marker_value = etree.SubElement(marker_prop, '{%s}lpwstr' % self.NAMESPACES['vt'])
        marker_value.text = 'WATERMARK_V1'

        # 添加水印备份数据
        data_prop = etree.SubElement(props, 'property')
        data_prop.set('name', 'wm_backup')
        data_prop.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
        data_prop.set('pid', '2')
        data_value = etree.SubElement(data_prop, '{%s}lpwstr' % self.NAMESPACES['vt'])
        data_value.text = b64_watermark

    def _add_content_types_comment(self, content: str, b64_watermark: str) -> str:
        """在 [Content_Types].xml 添加注释"""
        # 在 XML 声明后添加注释
        if '<?xml' in content:
            parts = content.split('?>', 1)
            if len(parts) == 2:
                return parts[0] + '?>\n<!-- wm_data:' + b64_watermark + ' -->\n' + parts[1]
        return content

    def _add_settings_comment(self, content: str, b64_watermark: str) -> str:
        """在 settings.xml 添加注释"""
        # 在根节点开始标签后添加注释
        if '<w:settings' in content:
            # 找到第一个 > 后插入
            idx = content.find('>', content.find('<w:settings'))
            if idx != -1:
                return content[:idx+1] + '\n<!-- wm_store:' + b64_watermark + ' -->\n' + content[idx+1:]
        return content

    def _add_header_hidden_text(self, header_content: str, b64_watermark: str) -> str:
        """在页眉添加隐藏文本"""
        # 在 </w:p> 前插入隐藏文本 run
        vanish_run = '''<w:r><w:rPr><w:vanish/></w:rPr><w:t>WM:%s</w:t></w:r>''' % b64_watermark
        # 在最后一个段落结束标签前插入
        if '</w:p>' in header_content:
            return header_content.replace('</w:p>', vanish_run + '</w:p>', 1)
        return header_content

    def _create_backup_xml(self, b64_watermark: str) -> bytes:
        """创建独立的备份 XML 文件"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<wm:WatermarkBackup xmlns:wm="http://watermark.local/2024">
  <wm:data>%s</wm:data>
  <wm:version>1.0</wm:version>
</wm:WatermarkBackup>''' % b64_watermark
        return xml_content.encode('utf-8')

    def embed_watermark(self, input_path: str, output_path: str,
                        user_info: str, department: str = '', project: str = '') -> dict:
        """
        核心嵌入方法

        Args:
            input_path: 原始文档路径
            output_path: 输出文档路径
            user_info: 用户标识信息
            department: 部门名称
            project: 项目名称

        Returns:
            嵌入结果统计
        """
        watermark_data = self._build_watermark_data(user_info, department, project)
        watermark_json = json.dumps(watermark_data, ensure_ascii=False)
        zw_watermark = self._text_to_zw_string(watermark_json)
        b64_watermark = self.crypto.text_to_base64(watermark_json)

        result = {
            'success': False,
            'positions_processed': 0,
            'backup_written': False,
            'error': None
        }

        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            with zipfile.ZipFile(input_path, 'r') as zin:
                # 读取并修改 document.xml
                with zin.open('word/document.xml') as f:
                    doc_xml = f.read()

                root = etree.fromstring(doc_xml)
                insert_points = self._get_insert_positions(root)

                if not insert_points:
                    result['error'] = '文档中没有可用的文本段落'
                    return result

                # 在选定位置插入零宽字符
                for t_node in insert_points:
                    if t_node.text:
                        t_node.text += zw_watermark

                result['positions_processed'] = len(insert_points)

                # 写入新文档
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.namelist():
                        content = zin.read(item)

                        if item == 'word/document.xml':
                            # 写入修改后的 document.xml
                            modified_xml = etree.tostring(root, xml_declaration=True,
                                                          encoding='UTF-8', standalone=True)
                            zout.writestr(item, modified_xml)

                        elif item == 'docProps/custom.xml':
                            # 添加自定义属性
                            try:
                                tree = etree.fromstring(content)
                                self._add_custom_property(tree, b64_watermark)
                                modified_xml = etree.tostring(tree, xml_declaration=True,
                                                              encoding='UTF-8', standalone=True)
                                zout.writestr(item, modified_xml)
                            except:
                                zout.writestr(item, content)

                        elif item == '[Content_Types].xml':
                            # 添加注释
                            content_str = content.decode('utf-8')
                            modified_content = self._add_content_types_comment(content_str, b64_watermark)
                            zout.writestr(item, modified_content.encode('utf-8'))

                        elif item == 'word/settings.xml':
                            # 添加注释
                            content_str = content.decode('utf-8')
                            modified_content = self._add_settings_comment(content_str, b64_watermark)
                            zout.writestr(item, modified_content.encode('utf-8'))

                        elif item.startswith('word/header'):
                            # 在页眉添加隐藏文本
                            content_str = content.decode('utf-8')
                            modified_content = self._add_header_hidden_text(content_str, b64_watermark)
                            zout.writestr(item, modified_content.encode('utf-8'))

                        else:
                            # 复制其他文件
                            zout.writestr(item, content)

                    # 添加独立的备份文件
                    zout.writestr('word/watermark_backup.xml', self._create_backup_xml(b64_watermark))
                    result['backup_written'] = True

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _extract_from_custom_xml(self, zin) -> str:
        """从 docProps/custom.xml 提取水印"""
        try:
            with zin.open('docProps/custom.xml') as f:
                content = f.read().decode('utf-8')
            if 'wm_backup' in content:
                # 提取 base64 数据
                match = re.search(r'<vt:lpwstr>([^<]+)</vt:lpwstr>', content)
                if match:
                    return match.group(1)
        except:
            pass
        return None

    def _extract_from_content_types_comment(self, zin) -> str:
        """从 [Content_Types].xml 注释提取"""
        try:
            with zin.open('[Content_Types].xml') as f:
                content = f.read().decode('utf-8')
            match = re.search(r'<!-- wm_data:([A-Za-z0-9_-]+) -->', content)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def _extract_from_settings_comment(self, zin) -> str:
        """从 word/settings.xml 注释提取"""
        try:
            with zin.open('word/settings.xml') as f:
                content = f.read().decode('utf-8')
            match = re.search(r'<!-- wm_store:([A-Za-z0-9_-]+) -->', content)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def _extract_from_header(self, zin) -> str:
        """从页眉提取隐藏文本"""
        try:
            for item in zin.namelist():
                if item.startswith('word/header'):
                    with zin.open(item) as f:
                        content = f.read().decode('utf-8')
                    match = re.search(r'WM:([A-Za-z0-9_-]+)', content)
                    if match:
                        return match.group(1)
        except:
            pass
        return None

    def _extract_from_backup_file(self, zin) -> str:
        """从独立备份文件提取"""
        try:
            with zin.open('word/watermark_backup.xml') as f:
                content = f.read().decode('utf-8')
            match = re.search(r'<wm:data>([^<]+)</wm:data>', content)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def _extract_from_zero_width(self, zin) -> tuple:
        """从零宽字符提取（多数投票）"""
        try:
            with zin.open('word/document.xml') as f:
                content = f.read().decode('utf-8')

            zw_pattern = re.compile(r'[\u200b\u200c]+')
            zw_sequences = zw_pattern.findall(content)

            if not zw_sequences:
                return None, 0

            # 多数投票
            counter = Counter(zw_sequences)
            most_common = counter.most_common(1)[0]

            return most_common[0], most_common[1]
        except:
            return None, 0

    def _scan_all_base64(self, zin) -> str:
        """扫描所有 XML 文件中的 base64 数据"""
        try:
            for item in zin.namelist():
                if item.endswith('.xml'):
                    with zin.open(item) as f:
                        content = f.read().decode('utf-8')
                    # 查找类似 base64 的字符串
                    matches = re.findall(r'[A-Za-z0-9_-]{32,}', content)
                    for match in matches:
                        try:
                            # 尝试解密
                            data = self.crypto.base64_to_text(match)
                            if '"version"' in data and '"uid"' in data:
                                return match
                        except:
                            continue
        except:
            pass
        return None

    def analyze_docx(self, file_path: str) -> dict:
        """
        分析并提取水印

        Args:
            file_path: 待分析的文档路径

        Returns:
            分析结果
        """
        result = {
            'success': False,
            'has_watermark': False,
            'integrity': 0,
            'watermark_data': None,
            'extraction_source': None,
            'extracted_count': 0,
            'error': None
        }

        try:
            file_path = Path(file_path)

            with zipfile.ZipFile(file_path, 'r') as z:
                # 按优先级尝试提取
                extractors = [
                    ('custom.xml', self._extract_from_custom_xml),
                    ('[Content_Types].xml comment', self._extract_from_content_types_comment),
                    ('settings.xml comment', self._extract_from_settings_comment),
                    ('header hidden text', self._extract_from_header),
                    ('backup file', self._extract_from_backup_file),
                    ('zero-width characters', lambda z: self._extract_from_zero_width(z)[0]),
                    ('base64 scan', self._scan_all_base64),
                ]

                watermark_json = None
                for source_name, extractor in extractors:
                    try:
                        extracted = extractor(z)
                        if extracted:
                            # 尝试解密
                            if source_name == 'zero-width characters':
                                watermark_json = self._zw_string_to_text(extracted)
                            else:
                                watermark_json = self.crypto.base64_to_text(extracted)

                            if watermark_json:
                                result['extraction_source'] = source_name
                                break
                    except:
                        continue

                if not watermark_json:
                    result['error'] = '未发现水印或密钥不匹配'
                    return result

                # 解析水印数据
                watermark_data = json.loads(watermark_json)

                # 验证 CRC
                stored_crc = watermark_data.pop('crc', None)
                calculated_crc = self.crypto.calculate_crc(json.dumps(watermark_data, sort_keys=True))

                if stored_crc != calculated_crc:
                    result['error'] = '水印数据校验失败，可能已被篡改'
                    return result

                result['watermark_data'] = watermark_data
                result['has_watermark'] = True
                result['success'] = True
                result['integrity'] = 100  # 从备份提取默认100%

        except Exception as e:
            result['error'] = str(e)

        return result
