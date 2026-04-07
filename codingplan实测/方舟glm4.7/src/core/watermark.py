"""
Docx智能水印核心模块
实现水印嵌入和提取功能
"""

import zipfile
import json
import zlib
import base64
import re
from pathlib import Path
from datetime import datetime
from lxml import etree
from collections import Counter
from typing import Dict, List, Optional, Tuple

# 固定默认密码（用于派生默认密钥）
DEFAULT_PASSWORD = 'docx_watermark_default_key_2024'


class DocxWatermarkTool:
    """Docx 智能水印溯源工具核心类"""

    # XML 命名空间
    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    }

    def __init__(self, master_password: str = None, salt: bytes = None):
        """
        初始化水印工具

        Args:
            master_password: 主密码，用于派生加密密钥
            salt: 盐值，增强安全性
        """
        # 导入加密模块（避免循环导入）
        from .crypto import CryptoManager

        if master_password:
            self.salt = salt or b'docx_watermark_salt_v1'
            self.master_key = CryptoManager.derive_key(master_password, self.salt)
        else:
            self.salt = b'default_salt'
            self.master_key = CryptoManager.derive_key(DEFAULT_PASSWORD, self.salt)

        self.cipher = CryptoManager.get_cipher(self.master_key)

        # Unicode 映射 (零宽字符)
        self.ZERO_WIDTH_MAP = {'0': '\u200b', '1': '\u200c'}
        self.REV_ZERO_WIDTH_MAP = {'\u200b': '0', '\u200c': '1'}

    def _calculate_crc(self, data: str) -> str:
        """计算 CRC 校验码"""
        return format(zlib.crc32(data.encode()) & 0xFFFFFFFF, '04X')

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
        data["crc"] = self._calculate_crc(json.dumps(data, sort_keys=True))
        return data

    def _text_to_zw_string(self, text: str) -> str:
        """将文本转换为零宽字符字符串"""
        encrypted_data = self.cipher.encrypt(text.encode('utf-8'))
        binary_string = ''.join(format(b, '08b') for b in encrypted_data)
        return ''.join(self.ZERO_WIDTH_MAP[b] for b in binary_string)

    def _zw_string_to_text(self, zw_string: str) -> Optional[str]:
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
            decrypted_data = self.cipher.decrypt(bytes(byte_arr))
            return decrypted_data.decode('utf-8')
        except Exception:
            return None  # 密钥不匹配或数据损坏

    def _find_paragraph_ends(self, xml_content: str) -> List[int]:
        """
        在XML字符串中查找段落的结尾位置（</w:t>标签）

        Returns:
            包含所有</w:t>标签位置的列表
        """
        positions = []
        pattern = re.compile(r'</w:t>')
        for match in pattern.finditer(xml_content):
            positions.append(match.end())
        return positions

    def embed_watermark(self, input_path: str, output_path: str,
                        user_info: str, department: str = '', project: str = '') -> Dict:
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
        # 构建水印数据
        watermark_data = self._build_watermark_data(user_info, department, project)
        watermark_json = json.dumps(watermark_data, ensure_ascii=False)
        zw_watermark = self._text_to_zw_string(watermark_json)

        result = {
            'success': False,
            'paragraphs_processed': 0,
            'backup_written': [],
            'error': None
        }

        try:
            # 1. 解压 DOCX
            input_path = Path(input_path)
            output_path = Path(output_path)

            with zipfile.ZipFile(input_path, 'r') as zin:
                # 读取 document.xml
                with zin.open('word/document.xml') as f:
                    doc_xml_content = f.read().decode('utf-8')

                # 2. 查找插入点
                insert_positions = self._find_paragraph_ends(doc_xml_content)

                if not insert_positions:
                    result['error'] = '文档中没有可用的文本段落'
                    return result

                # 3. 根据文档长度选择嵌入位置数
                positions = self._select_embed_positions(insert_positions)

                # 4. 从后往前插入零宽字符（避免位置偏移）
                modified_xml = doc_xml_content
                for pos in sorted(positions, reverse=True):
                    modified_xml = modified_xml[:pos] + zw_watermark + modified_xml[pos:]

                result['paragraphs_processed'] = len(positions)

                # 5. 准备备份数据（base64编码的完整水印JSON）
                backup_data = base64.b64encode(watermark_json.encode('utf-8')).decode('utf-8')

                # 6. 写入新文档
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.namelist():
                        if item == 'word/document.xml':
                            zout.writestr(item, modified_xml.encode('utf-8'))
                        elif item == 'docProps/custom.xml':
                            # 层1: custom.xml
                            try:
                                custom_xml = self._add_to_custom_xml(zin.read(item), backup_data)
                                zout.writestr(item, custom_xml)
                                result['backup_written'].append('docProps/custom.xml')
                            except:
                                zout.writestr(item, zin.read(item))
                        elif item == '[Content_Types].xml':
                            # 层2: Content_Types.xml 注释
                            try:
                                ct_xml = self._add_to_xml_comment(zin.read(item), 'wm_data', backup_data)
                                zout.writestr(item, ct_xml)
                                result['backup_written'].append('[Content_Types].xml')
                            except:
                                zout.writestr(item, zin.read(item))
                        elif item == 'word/settings.xml':
                            # 层3: settings.xml 注释
                            try:
                                settings_xml = self._add_to_xml_comment(zin.read(item), 'wm_store', backup_data)
                                zout.writestr(item, settings_xml)
                                result['backup_written'].append('word/settings.xml')
                            except:
                                zout.writestr(item, zin.read(item))
                        elif item.startswith('word/header') or item.startswith('word/footer'):
                            # 层4: 页眉/页脚隐藏文本
                            try:
                                header_xml = self._add_hidden_text(zin.read(item), backup_data)
                                zout.writestr(item, header_xml)
                                result['backup_written'].append(item)
                            except:
                                zout.writestr(item, zin.read(item))
                        else:
                            zout.writestr(item, zin.read(item))

                    # 层5: 独立备份文件
                    backup_xml = self._create_backup_xml(backup_data)
                    zout.writestr('word/watermark_backup.xml', backup_xml.encode('utf-8'))
                    result['backup_written'].append('word/watermark_backup.xml')

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _select_embed_positions(self, all_positions: List[int]) -> List[int]:
        """根据文档长度选择嵌入位置"""
        total = len(all_positions)

        if total <= 10:
            # 短文档：嵌入3个位置
            count = min(3, total)
            step = max(1, total // count)
            return [all_positions[i * step] for i in range(count)]
        elif total <= 30:
            # 中等文档：嵌入5个位置
            count = min(5, total)
            step = max(1, total // count)
            return [all_positions[i * step] for i in range(count)]
        else:
            # 长文档：嵌入8个位置
            count = min(8, total)
            step = max(1, total // count)
            return [all_positions[i * step] for i in range(count)]

    def _add_to_custom_xml(self, original: bytes, backup_data: str) -> bytes:
        """将备份数据添加到custom.xml"""
        try:
            if original:
                tree = etree.fromstring(original)
            else:
                # 创建新的属性文件
                tree = etree.Element('{http://schemas.openxmlformats.org/officeDocument/2006/custom-properties}Properties')

            # 添加自定义属性
            prop = etree.SubElement(tree, 'property')
            prop.set('name', 'wm_backup')
            prop.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
            value = etree.SubElement(prop, '{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}lpwstr')
            value.text = backup_data

            # 添加标记
            marker = etree.SubElement(tree, 'property')
            marker.set('name', 'wm_marker')
            marker.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
            marker_value = etree.SubElement(marker, '{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}lpwstr')
            marker_value.text = 'WATERMARK_V1'

            return etree.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
        except:
            return original

    def _add_to_xml_comment(self, original: bytes, prefix: str, backup_data: str) -> bytes:
        """将备份数据添加到XML注释"""
        xml_str = original.decode('utf-8')
        comment = f'<!-- {prefix}:{backup_data} -->'

        # 在xml声明后插入注释
        if xml_str.startswith('<?xml'):
            idx = xml_str.find('>') + 1
            return (xml_str[:idx] + '\n' + comment + xml_str[idx:]).encode('utf-8')
        else:
            return (comment + '\n' + xml_str).encode('utf-8')

    def _add_hidden_text(self, original: bytes, backup_data: str) -> bytes:
        """将备份数据作为隐藏文本添加到页眉/页脚"""
        xml_str = original.decode('utf-8')
        hidden_text = f'<w:r><w:rPr><w:vanish/></w:rPr><w:t>WM:{backup_data}</w:t></w:r>'

        # 在</w:p>标签前插入
        if '</w:p>' in xml_str:
            return xml_str.replace('</w:p>', hidden_text + '</w:p>', 1).encode('utf-8')
        else:
            return (hidden_text + xml_str).encode('utf-8')

    def _create_backup_xml(self, backup_data: str) -> str:
        """创建独立的备份XML文件"""
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<wm:WatermarkBackup xmlns:wm="http://watermark.local/2024">
  <wm:data>{backup_data}</wm:data>
  <wm:version>1.0</wm:version>
</wm:WatermarkBackup>'''

    def analyze_docx(self, file_path: str) -> Dict:
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
            'extracted_count': 0,
            'extracted_from': None,
            'error': None
        }

        try:
            file_path = Path(file_path)

            with zipfile.ZipFile(file_path, 'r') as z:
                # 按优先级依次尝试提取
                extraction_methods = [
                    ('backup_custom_xml', self._extract_from_custom_xml),
                    ('backup_content_types', self._extract_from_content_types),
                    ('backup_settings', self._extract_from_settings),
                    ('backup_header', self._extract_from_header),
                    ('backup_file', self._extract_from_backup_file),
                    ('zero_width', self._extract_from_zero_width),
                    ('base64_scan', self._extract_from_base64_scan)
                ]

                for method_name, method in extraction_methods:
                    try:
                        watermark_json = method(z)
                        if watermark_json:
                            result['extracted_from'] = method_name
                            return self._parse_watermark_json(watermark_json, result)
                    except Exception:
                        continue

                result['error'] = '未发现水印'

        except Exception as e:
            result['error'] = str(e)

        return result

    def _extract_from_custom_xml(self, z: zipfile.ZipFile) -> Optional[str]:
        """从custom.xml提取备份数据"""
        if 'docProps/custom.xml' in z.namelist():
            with z.open('docProps/custom.xml') as f:
                xml_content = f.read().decode('utf-8')

            # 检查标记
            if 'WATERMARK_V1' in xml_content and 'wm_backup' in xml_content:
                try:
                    tree = etree.fromstring(xml_content)
                    props = tree.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/custom-properties}property')
                    for prop in props:
                        if prop.get('name') == 'wm_backup':
                            value = prop.find('.//{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}lpwstr')
                            if value and value.text:
                                return base64.b64decode(value.text).decode('utf-8')
                except:
                    pass
        return None

    def _extract_from_content_types(self, z: zipfile.ZipFile) -> Optional[str]:
        """从[Content_Types].xml注释提取备份数据"""
        if '[Content_Types].xml' in z.namelist():
            with z.open('[Content_Types].xml') as f:
                content = f.read().decode('utf-8')

            match = re.search(r'<!-- wm_data:([A-Za-z0-9+/=]+) -->', content)
            if match:
                try:
                    return base64.b64decode(match.group(1)).decode('utf-8')
                except:
                    pass
        return None

    def _extract_from_settings(self, z: zipfile.ZipFile) -> Optional[str]:
        """从settings.xml注释提取备份数据"""
        if 'word/settings.xml' in z.namelist():
            with z.open('word/settings.xml') as f:
                content = f.read().decode('utf-8')

            match = re.search(r'<!-- wm_store:([A-Za-z0-9+/=]+) -->', content)
            if match:
                try:
                    return base64.b64decode(match.group(1)).decode('utf-8')
                except:
                    pass
        return None

    def _extract_from_header(self, z: zipfile.ZipFile) -> Optional[str]:
        """从页眉/页脚隐藏文本提取备份数据"""
        for item in z.namelist():
            if item.startswith('word/header') or item.startswith('word/footer'):
                with z.open(item) as f:
                    content = f.read().decode('utf-8')

                match = re.search(r'<w:t>WM:([A-Za-z0-9+/=]+)</w:t>', content)
                if match:
                    try:
                        return base64.b64decode(match.group(1)).decode('utf-8')
                    except:
                        pass
        return None

    def _extract_from_backup_file(self, z: zipfile.ZipFile) -> Optional[str]:
        """从独立备份文件提取备份数据"""
        if 'word/watermark_backup.xml' in z.namelist():
            with z.open('word/watermark_backup.xml') as f:
                content = f.read().decode('utf-8')

            match = re.search(r'<wm:data>([A-Za-z0-9+/=]+)</wm:data>', content)
            if match:
                try:
                    return base64.b64decode(match.group(1)).decode('utf-8')
                except:
                    pass
        return None

    def _extract_from_zero_width(self, z: zipfile.ZipFile) -> Optional[str]:
        """从零宽字符提取备份数据"""
        with z.open('word/document.xml') as f:
            content = f.read().decode('utf-8')

        # 提取所有零宽字符序列
        zw_pattern = re.compile(r'[\u200b\u200c]+')
        zw_sequences = zw_pattern.findall(content)

        if not zw_sequences:
            return None

        # 多数投票确定有效数据
        counter = Counter(zw_sequences)
        most_common = counter.most_common(1)[0]

        return self._zw_string_to_text(most_common[0])

    def _extract_from_base64_scan(self, z: zipfile.ZipFile) -> Optional[str]:
        """从所有XML文件中扫描base64数据"""
        for item in z.namelist():
            if item.endswith('.xml'):
                try:
                    with z.open(item) as f:
                        content = f.read().decode('utf-8')

                    # 查找可能的base64编码数据（尝试解密）
                    # 这里简化处理，实际可能需要更复杂的模式匹配
                    continue
                except:
                    continue
        return None

    def _parse_watermark_json(self, watermark_json: str, result: Dict) -> Dict:
        """解析水印JSON数据"""
        try:
            watermark_data = json.loads(watermark_json)

            # 验证 CRC
            stored_crc = watermark_data.pop('crc', None)
            calculated_crc = self._calculate_crc(json.dumps(watermark_data, sort_keys=True))

            if stored_crc == calculated_crc:
                result['watermark_data'] = watermark_data
                result['has_watermark'] = True
                result['success'] = True
                result['integrity'] = 100.0
            else:
                result['error'] = '水印数据校验失败，可能已被篡改'
        except Exception as e:
            result['error'] = str(e)

        return result
