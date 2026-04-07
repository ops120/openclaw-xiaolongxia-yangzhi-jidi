# -*- coding: utf-8 -*-
"""
水印核心模块 - 零宽字符水印嵌入与提取
"""

import zipfile
import json
import zlib
import base64
import re
import os
from pathlib import Path
from datetime import datetime
from io import BytesIO
from lxml import etree
from collections import Counter
from typing import Optional, List, Tuple, Dict, Any

from .crypto import CryptoManager


class DocxWatermarkTool:
    """
    Docx 智能水印溯源工具核心类

    支持五层冗余备份策略，防止WPS/Word重写导致水印丢失
    """

    # XML 命名空间
    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
        'cp': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }

    # 零宽字符映射
    ZERO_WIDTH_MAP = {'0': '\u200b', '1': '\u200c'}
    REV_ZERO_WIDTH_MAP = {'\u200b': '0', '\u200c': '1'}

    # 水印标记
    WATERMARK_MARKER = 'WATERMARK_V1'
    WATERMARK_PREFIX = 'WM:'

    def __init__(self, password: str = None):
        """
        初始化水印工具

        Args:
            password: 加密密码，用于派生加密密钥
        """
        self.crypto = CryptoManager(password)

    def _calculate_crc(self, data: str) -> str:
        """计算 CRC 校验码"""
        return format(zlib.crc32(data.encode('utf-8')) & 0xFFFFFFFF, '04X')

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
        """
        将文本转换为零宽字符字符串

        Args:
            text: 原始文本

        Returns:
            零宽字符编码的字符串
        """
        encrypted_data = self.crypto.encrypt(text)
        binary_string = ''.join(format(b, '08b') for b in encrypted_data)
        return ''.join(self.ZERO_WIDTH_MAP[b] for b in binary_string)

    def _zw_string_to_text(self, zw_string: str) -> Optional[str]:
        """
        将零宽字符字符串还原为原始文本

        Args:
            zw_string: 零宽字符编码的字符串

        Returns:
            解密后的原始文本，失败返回 None
        """
        binary_string = ''.join(
            self.REV_ZERO_WIDTH_MAP.get(char, '')
            for char in zw_string
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
            return None

    def _base64_to_watermark(self, base64_str: str) -> Optional[dict]:
        """
        从 base64 字符串解密水印数据

        Args:
            base64_str: base64 编码的加密数据

        Returns:
            水印数据字典，失败返回 None
        """
        try:
            decrypted = self.crypto.decrypt_from_base64(base64_str)
            return json.loads(decrypted)
        except Exception:
            return None

    def _watermark_to_base64(self, watermark_data: dict) -> str:
        """
        将水印数据加密并转换为 base64

        Args:
            watermark_data: 水印数据字典

        Returns:
            base64 编码的加密字符串
        """
        json_str = json.dumps(watermark_data, ensure_ascii=False)
        return self.crypto.encrypt_to_base64(json_str)

    def _get_embed_positions(self, total_paragraphs: int) -> List[int]:
        """
        根据文档长度计算最佳嵌入位置

        Args:
            total_paragraphs: 总段落数

        Returns:
            嵌入位置索引列表
        """
        if total_paragraphs <= 10:
            # 短文档：嵌入3个位置
            positions = [total_paragraphs // 4, total_paragraphs // 2,
                        total_paragraphs * 3 // 4]
        elif total_paragraphs <= 30:
            # 中等文档：嵌入5个位置
            positions = [total_paragraphs // 6, total_paragraphs // 3,
                        total_paragraphs // 2, total_paragraphs * 2 // 3,
                        total_paragraphs * 5 // 6]
        else:
            # 长文档：嵌入8个位置
            positions = [int(total_paragraphs * i / 9) for i in range(1, 9)]

        return sorted(set(max(0, min(p, total_paragraphs - 1)) for p in positions))

    def _insert_watermark_to_xml(self, xml_content: str, zw_watermark: str) -> Tuple[str, int]:
        """
        在 XML 内容中插入零宽字符水印

        Args:
            xml_content: 原始 XML 字符串
            zw_watermark: 零宽字符水印

        Returns:
            (修改后的 XML, 嵌入的位置数量)
        """
        # 查找所有 </w:t> 标签
        pattern = r'(<w:t[^>]*>)([^<]*)(</w:t>)'
        matches = list(re.finditer(pattern, xml_content))

        if not matches:
            return xml_content, 0

        # 计算嵌入位置
        positions = self._get_embed_positions(len(matches))

        # 从后向前插入，避免索引变化
        result = xml_content
        for idx in reversed(positions):
            match = matches[idx]
            # 在 </w:t> 前插入水印
            insert_pos = match.end() - len('</w:t>')
            result = result[:insert_pos] + zw_watermark + result[insert_pos:]

        return result, len(positions)

    def _write_custom_properties(self, existing_content: Optional[bytes],
                                   watermark_base64: str) -> bytes:
        """
        创建或更新 custom.xml 自定义属性

        Args:
            existing_content: 现有的 custom.xml 内容，None 表示新建
            watermark_base64: base64 编码的水印数据

        Returns:
            新的 custom.xml 内容
        """
        if existing_content:
            try:
                root = etree.fromstring(existing_content)
            except:
                root = etree.Element('{%s}Properties' % self.NAMESPACES['cp'])
        else:
            root = etree.Element('{%s}Properties' % self.NAMESPACES['cp'])

        # 移除旧的水印属性
        for prop in root.findall('.//{%s}property' % self.NAMESPACES.get('cp', '')):
            name = prop.get('name', '')
            if name.startswith('wm_'):
                root.remove(prop)

        # 查找所有命名空间
        nsmap = root.nsmap if hasattr(root, 'nsmap') and root.nsmap else {}

        # 添加水印数据属性
        prop = etree.SubElement(root, 'property')
        prop.set('name', 'wm_backup')
        prop.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
        vt_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
        value = etree.SubElement(prop, '{%s}lpwstr' % vt_ns)
        value.text = watermark_base64

        # 添加标记属性
        prop2 = etree.SubElement(root, 'property')
        prop2.set('name', 'wm_marker')
        prop2.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
        value2 = etree.SubElement(prop2, '{%s}lpwstr' % vt_ns)
        value2.text = self.WATERMARK_MARKER

        return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

    def _add_comment_to_content_types(self, content: bytes, watermark_base64: str) -> bytes:
        """
        在 [Content_Types].xml 中添加注释水印

        Args:
            content: 原始内容
            watermark_base64: base64 编码的水印数据

        Returns:
            修改后的内容
        """
        try:
            content_str = content.decode('utf-8')
            # 在 XML 声明后添加注释
            if '?>' in content_str:
                insert_pos = content_str.index('?>') + 2
                comment = f'\n<!-- wm_data:{watermark_base64} -->'
                content_str = content_str[:insert_pos] + comment + content_str[insert_pos:]
            return content_str.encode('utf-8')
        except:
            return content

    def _add_comment_to_settings(self, content: bytes, watermark_base64: str) -> bytes:
        """
        在 word/settings.xml 中添加注释水印

        Args:
            content: 原始内容
            watermark_base64: base64 编码的水印数据

        Returns:
            修改后的内容
        """
        try:
            content_str = content.decode('utf-8')
            # 在 XML 声明后添加注释
            if '?>' in content_str:
                insert_pos = content_str.index('?>') + 2
                comment = f'\n<!-- wm_store:{watermark_base64} -->'
                content_str = content_str[:insert_pos] + comment + content_str[insert_pos:]
            return content_str.encode('utf-8')
        except:
            return content

    def _create_header_with_watermark(self, watermark_base64: str) -> bytes:
        """
        创建包含隐藏水印的页眉 XML

        Args:
            watermark_base64: base64 编码的水印数据

        Returns:
            页眉 XML 内容
        """
        header_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr>
      <w:pStyle w:val="Header"/>
    </w:pPr>
    <w:r>
      <w:rPr>
        <w:vanish/>
      </w:rPr>
      <w:t>{self.WATERMARK_PREFIX}{watermark_base64}</w:t>
    </w:r>
  </w:p>
</w:hdr>'''
        return header_xml.encode('utf-8')

    def _create_backup_xml(self, watermark_base64: str) -> bytes:
        """
        创建独立的备份 XML 文件

        Args:
            watermark_base64: base64 编码的水印数据

        Returns:
            备份 XML 内容
        """
        backup_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<wm:WatermarkBackup xmlns:wm="http://watermark.local/2024">
  <wm:data>{watermark_base64}</wm:data>
  <wm:version>1.0</wm:version>
  <wm:timestamp>{datetime.now().isoformat()}</wm:timestamp>
</wm:WatermarkBackup>'''
        return backup_xml.encode('utf-8')

    def embed_watermark(self, input_path: str, output_path: str,
                        user_info: str, department: str = '',
                        project: str = '') -> dict:
        """
        核心嵌入方法 - 五层冗余备份策略

        Args:
            input_path: 原始文档路径
            output_path: 输出文档路径
            user_info: 用户标识信息
            department: 部门名称
            project: 项目名称

        Returns:
            嵌入结果统计
        """
        result = {
            'success': False,
            'paragraphs_processed': 0,
            'backup_layers': [],
            'error': None
        }

        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 构建水印数据
            watermark_data = self._build_watermark_data(user_info, department, project)
            watermark_json = json.dumps(watermark_data, ensure_ascii=False)

            # 生成两种格式的水印
            zw_watermark = self._text_to_zw_string(watermark_json)
            watermark_base64 = self._watermark_to_base64(watermark_data)

            with zipfile.ZipFile(input_path, 'r') as zin:
                # 读取 document.xml
                try:
                    doc_xml = zin.read('word/document.xml')
                except KeyError:
                    result['error'] = '无效的 DOCX 文件：缺少 document.xml'
                    return result

                # 插入零宽字符水印
                xml_str = doc_xml.decode('utf-8')
                modified_xml, positions_count = self._insert_watermark_to_xml(xml_str, zw_watermark)
                result['paragraphs_processed'] = positions_count

                # 读取其他文件
                file_contents = {}
                for item in zin.namelist():
                    file_contents[item] = zin.read(item)

                # === 五层备份写入 ===

                # 层1: custom.xml 自定义属性
                try:
                    custom_path = 'docProps/custom.xml'
                    existing_custom = file_contents.get(custom_path)
                    file_contents[custom_path] = self._write_custom_properties(
                        existing_custom, watermark_base64)
                    result['backup_layers'].append('custom.xml')
                except Exception as e:
                    pass

                # 层2: [Content_Types].xml 注释
                try:
                    ct_path = '[Content_Types].xml'
                    if ct_path in file_contents:
                        file_contents[ct_path] = self._add_comment_to_content_types(
                            file_contents[ct_path], watermark_base64)
                        result['backup_layers'].append('Content_Types.xml')
                except Exception as e:
                    pass

                # 层3: word/settings.xml 注释
                try:
                    settings_path = 'word/settings.xml'
                    if settings_path in file_contents:
                        file_contents[settings_path] = self._add_comment_to_settings(
                            file_contents[settings_path], watermark_base64)
                        result['backup_layers'].append('settings.xml')
                except Exception as e:
                    pass

                # 层4: 页眉隐藏文本
                try:
                    header_path = 'word/header1.xml'
                    file_contents[header_path] = self._create_header_with_watermark(watermark_base64)
                    result['backup_layers'].append('header.xml')
                except Exception as e:
                    pass

                # 层5: 独立备份文件
                try:
                    backup_path = 'word/watermark_backup.xml'
                    file_contents[backup_path] = self._create_backup_xml(watermark_base64)
                    result['backup_layers'].append('watermark_backup.xml')
                except Exception as e:
                    pass

                # 更新 document.xml
                file_contents['word/document.xml'] = modified_xml.encode('utf-8')

                # 写入新文档
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item, content in file_contents.items():
                        zout.writestr(item, content)

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _extract_from_custom_properties(self, content: bytes) -> Optional[str]:
        """从 custom.xml 提取水印"""
        try:
            root = etree.fromstring(content)
            vt_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
            for prop in root.iter():
                if prop.get('name') == 'wm_backup':
                    lpwstr = prop.find('.//{%s}lpwstr' % vt_ns)
                    if lpwstr is not None and lpwstr.text:
                        return lpwstr.text
        except:
            pass
        return None

    def _extract_from_comment(self, content: bytes, marker: str) -> Optional[str]:
        """从 XML 注释提取水印"""
        try:
            content_str = content.decode('utf-8')
            pattern = rf'<!--\s*{marker}:([A-Za-z0-9+/=]+)\s*-->'
            match = re.search(pattern, content_str)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def _extract_from_header(self, zin: zipfile.ZipFile) -> Optional[str]:
        """从页眉提取水印"""
        try:
            for name in zin.namelist():
                if 'header' in name.lower() and name.endswith('.xml'):
                    content = zin.read(name).decode('utf-8')
                    # 查找隐藏文本中的水印
                    pattern = rf'{self.WATERMARK_PREFIX}([A-Za-z0-9+/=]+)'
                    match = re.search(pattern, content)
                    if match:
                        return match.group(1)
        except:
            pass
        return None

    def _extract_from_backup_xml(self, zin: zipfile.ZipFile) -> Optional[str]:
        """从独立备份文件提取水印"""
        try:
            if 'word/watermark_backup.xml' in zin.namelist():
                content = zin.read('word/watermark_backup.xml')
                root = etree.fromstring(content)
                for elem in root.iter():
                    if elem.tag.endswith('}data') or elem.tag == 'data':
                        return elem.text
        except:
            pass
        return None

    def _extract_zw_sequences(self, content: str) -> List[str]:
        """提取所有零宽字符序列"""
        pattern = r'[\u200b\u200c]+'
        return re.findall(pattern, content)

    def _majority_vote(self, sequences: List[str]) -> Tuple[Optional[str], int, int]:
        """
        多数投票确定有效数据

        Args:
            sequences: 提取的零宽字符序列列表

        Returns:
            (最常见序列, 一致计数, 总计数)
        """
        if not sequences:
            return None, 0, 0

        # 过滤有效序列（长度足够的）
        valid_sequences = [s for s in sequences if len(s) >= 16]

        if not valid_sequences:
            return None, 0, len(sequences)

        counter = Counter(valid_sequences)
        most_common = counter.most_common(1)[0]

        return most_common[0], most_common[1], len(valid_sequences)

    def _scan_all_xml_for_base64(self, zin: zipfile.ZipFile) -> Optional[str]:
        """扫描所有 XML 文件中的 base64 数据"""
        base64_pattern = r'[A-Za-z0-9+/]{40,}={0,2}'

        for name in zin.namelist():
            if name.endswith('.xml'):
                try:
                    content = zin.read(name).decode('utf-8')
                    matches = re.findall(base64_pattern, content)
                    for match in matches:
                        data = self._base64_to_watermark(match)
                        if data and 'uid' in data:
                            return match
                except:
                    pass
        return None

    def analyze_docx(self, file_path: str) -> dict:
        """
        分析并提取水印 - 7层优先级策略

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
            'source': None,
            'log': [],
            'error': None
        }

        try:
            file_path = Path(file_path)

            if not file_path.exists():
                result['error'] = '文件不存在'
                return result

            with zipfile.ZipFile(file_path, 'r') as zin:
                # === 7层提取策略 ===

                # 层1: custom.xml 自定义属性
                result['log'].append('尝试从 custom.xml 提取...')
                if 'docProps/custom.xml' in zin.namelist():
                    base64_data = self._extract_from_custom_properties(
                        zin.read('docProps/custom.xml'))
                    if base64_data:
                        watermark_data = self._base64_to_watermark(base64_data)
                        if watermark_data:
                            result['watermark_data'] = watermark_data
                            result['source'] = 'custom.xml'
                            result['integrity'] = 100
                            result['log'].append('✓ 从 custom.xml 成功提取')

                # 层2: [Content_Types].xml 注释
                if not result['watermark_data']:
                    result['log'].append('尝试从 Content_Types.xml 提取...')
                    if '[Content_Types].xml' in zin.namelist():
                        base64_data = self._extract_from_comment(
                            zin.read('[Content_Types].xml'), 'wm_data')
                        if base64_data:
                            watermark_data = self._base64_to_watermark(base64_data)
                            if watermark_data:
                                result['watermark_data'] = watermark_data
                                result['source'] = 'Content_Types.xml'
                                result['integrity'] = 100
                                result['log'].append('✓ 从 Content_Types.xml 成功提取')

                # 层3: word/settings.xml 注释
                if not result['watermark_data']:
                    result['log'].append('尝试从 settings.xml 提取...')
                    if 'word/settings.xml' in zin.namelist():
                        base64_data = self._extract_from_comment(
                            zin.read('word/settings.xml'), 'wm_store')
                        if base64_data:
                            watermark_data = self._base64_to_watermark(base64_data)
                            if watermark_data:
                                result['watermark_data'] = watermark_data
                                result['source'] = 'settings.xml'
                                result['integrity'] = 100
                                result['log'].append('✓ 从 settings.xml 成功提取')

                # 层4: 页眉隐藏文本
                if not result['watermark_data']:
                    result['log'].append('尝试从页眉提取...')
                    base64_data = self._extract_from_header(zin)
                    if base64_data:
                        watermark_data = self._base64_to_watermark(base64_data)
                        if watermark_data:
                            result['watermark_data'] = watermark_data
                            result['source'] = 'header.xml'
                            result['integrity'] = 100
                            result['log'].append('✓ 从页眉成功提取')

                # 层5: 独立备份文件
                if not result['watermark_data']:
                    result['log'].append('尝试从备份文件提取...')
                    base64_data = self._extract_from_backup_xml(zin)
                    if base64_data:
                        watermark_data = self._base64_to_watermark(base64_data)
                        if watermark_data:
                            result['watermark_data'] = watermark_data
                            result['source'] = 'watermark_backup.xml'
                            result['integrity'] = 100
                            result['log'].append('✓ 从备份文件成功提取')

                # 层6: 全文零宽字符搜索
                if not result['watermark_data']:
                    result['log'].append('尝试零宽字符提取...')
                    if 'word/document.xml' in zin.namelist():
                        content = zin.read('word/document.xml').decode('utf-8')
                        sequences = self._extract_zw_sequences(content)
                        result['extracted_count'] = len(sequences)

                        if sequences:
                            result['log'].append(f'发现 {len(sequences)} 组零宽字符标记')

                            # 多数投票
                            most_common, consistent, total = self._majority_vote(sequences)

                            if most_common:
                                watermark_json = self._zw_string_to_text(most_common)
                                if watermark_json:
                                    watermark_data = json.loads(watermark_json)
                                    result['watermark_data'] = watermark_data
                                    result['source'] = 'zero_width'
                                    result['integrity'] = round(consistent / total * 100, 1)
                                    result['log'].append(f'✓ 零宽字符提取成功，完整度 {result["integrity"]}%')

                # 层7: 全 XML 文件 base64 扫描
                if not result['watermark_data']:
                    result['log'].append('尝试全文件扫描...')
                    base64_data = self._scan_all_xml_for_base64(zin)
                    if base64_data:
                        watermark_data = self._base64_to_watermark(base64_data)
                        if watermark_data:
                            result['watermark_data'] = watermark_data
                            result['source'] = 'full_scan'
                            result['integrity'] = 100
                            result['log'].append('✓ 全文件扫描成功提取')

            # 验证水印数据
            if result['watermark_data']:
                # 验证 CRC
                stored_crc = result['watermark_data'].pop('crc', None)
                if stored_crc:
                    calculated_crc = self._calculate_crc(
                        json.dumps(result['watermark_data'], sort_keys=True))
                    if stored_crc == calculated_crc:
                        result['has_watermark'] = True
                        result['success'] = True
                        result['log'].append('✓ CRC 校验通过')
                    else:
                        result['error'] = '水印数据校验失败，可能已被篡改'
                        result['log'].append('✗ CRC 校验失败')
                else:
                    result['has_watermark'] = True
                    result['success'] = True
            else:
                result['error'] = '未发现水印'
                result['log'].append('✗ 未发现有效水印')

        except Exception as e:
            result['error'] = str(e)
            result['log'].append(f'✗ 错误: {e}')

        return result
