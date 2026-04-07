"""
水印核心模块 - 实现水印嵌入和提取功能
"""
import re
import json
import base64
import zipfile
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Optional, Dict, List, Tuple

from .crypto import CryptoEngine


class WatermarkEngine:
    """水印引擎"""

    # XML 命名空间
    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
        'custom': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties',
        'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
    }

    # 零宽字符映射
    ZERO_WIDTH_MAP = {'0': '\u200b', '1': '\u200c'}  # 零宽空格, 零宽不连通符
    REV_ZERO_WIDTH_MAP = {'\u200b': '0', '\u200c': '1'}

    # 嵌入位置数量策略
    EMBED_POSITIONS_STRATEGY = {
        'short': 3,    # ≤10 段落
        'medium': 5,   # 11-30 段落
        'long': 8,     # >30 段落
    }

    def __init__(self, password: str = None, salt: bytes = None):
        """
        初始化水印引擎

        Args:
            password: 加密密码
            salt: 盐值
        """
        self.crypto = CryptoEngine(password, salt)

    def build_watermark_data(self, user_info: str, department: str = '',
                             project: str = '') -> dict:
        """
        构建水印数据结构

        Args:
            user_info: 用户标识信息
            department: 部门名称
            project: 项目名称

        Returns:
            水印数据字典
        """
        timestamp = datetime.now().isoformat()
        data = {
            "version": "1.0",
            "uid": user_info,
            "department": department,
            "timestamp": timestamp,
            "project": project
        }
        # 先计算 CRC（排除 version 字段）
        data_for_crc = {k: v for k, v in data.items() if k != 'version'}
        data["crc"] = self.crypto.calculate_crc(json.dumps(data_for_crc, sort_keys=True))
        return data

    def text_to_zw_string(self, text: str) -> str:
        """
        将文本转换为零宽字符字符串

        Args:
            text: 原始文本

        Returns:
            零宽字符字符串
        """
        encrypted_data = self.crypto.encrypt(text)
        binary_string = ''.join(format(b, '08b') for b in encrypted_data)
        return ''.join(self.ZERO_WIDTH_MAP[b] for b in binary_string)

    def zw_string_to_text(self, zw_string: str) -> Optional[str]:
        """
        将零宽字符字符串还原为原始文本

        Args:
            zw_string: 零宽字符字符串

        Returns:
            解密后的文本，失败返回 None
        """
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
            decrypted_data = self.crypto.decrypt(bytes(byte_arr))
            return decrypted_data
        except Exception:
            return None

    def to_base64_watermark(self, user_info: str, department: str = '',
                            project: str = '') -> str:
        """
        生成 base64 编码的水印数据（用于备份层）

        Args:
            user_info: 用户标识信息
            department: 部门名称
            project: 项目名称

        Returns:
            base64 编码的加密水印数据
        """
        watermark_data = self.build_watermark_data(user_info, department, project)
        watermark_json = json.dumps(watermark_data, ensure_ascii=False)
        encrypted_data = self.crypto.encrypt(watermark_json)
        return base64.b64encode(encrypted_data).decode('utf-8')

    def from_base64_watermark(self, base64_data: str) -> Optional[dict]:
        """
        从 base64 编码的数据还原水印

        Args:
            base64_data: base64 编码的加密数据

        Returns:
            水印数据字典，失败返回 None
        """
        try:
            encrypted_data = base64.b64decode(base64_data)
            decrypted_data = self.crypto.decrypt(encrypted_data)
            watermark_data = json.loads(decrypted_data)

            # 验证 CRC
            if self.crypto.validate_crc(watermark_data):
                return watermark_data
            return None
        except Exception:
            return None

    def _find_embedding_positions(self, xml_content: str) -> List[int]:
        """
        在 XML 内容中查找嵌入位置（段落末尾的 </w:t> 标签）

        Args:
            xml_content: document.xml 的内容

        Returns:
            嵌入位置索引列表
        """
        # 查找所有 </w:t> 标签的位置
        pattern = re.compile(r'</w:t>')
        positions = [m.end() for m in pattern.finditer(xml_content)]

        if not positions:
            return []

        # 根据段落数量决定嵌入位置数
        paragraph_count = len(re.findall(r'<w:p[ >]', xml_content))

        if paragraph_count <= 10:
            positions_needed = self.EMBED_POSITIONS_STRATEGY['short']
        elif paragraph_count <= 30:
            positions_needed = self.EMBED_POSITIONS_STRATEGY['medium']
        else:
            positions_needed = self.EMBED_POSITIONS_STRATEGY['long']

        # 均匀选择嵌入位置
        if len(positions) <= positions_needed:
            return positions

        # 计算步长
        step = len(positions) // positions_needed
        return [positions[i * step] for i in range(positions_needed)]

    def _embed_to_document_xml(self, xml_content: str, watermark: str) -> str:
        """
        将水印嵌入到 document.xml 中

        Args:
            xml_content: 原始 XML 内容
            watermark: 水印字符串（零宽字符）

        Returns:
            修改后的 XML 内容
        """
        positions = self._find_embedding_positions(xml_content)
        if not positions:
            return xml_content

        # 从后向前插入，避免位置偏移
        result = list(xml_content)
        for pos in sorted(positions, reverse=True):
            for char in reversed(watermark):
                result.insert(pos, char)

        return ''.join(result)

    def _extract_from_document_xml(self, xml_content: str) -> Optional[str]:
        """
        从 document.xml 中提取水印

        Args:
            xml_content: XML 内容

        Returns:
            提取的水印数据，失败返回 None
        """
        # 提取所有零宽字符序列
        zw_pattern = re.compile(r'[\u200b\u200c]+')
        zw_sequences = zw_pattern.findall(xml_content)

        if not zw_sequences:
            return None

        # 多数投票确定有效数据
        counter = Counter(zw_sequences)
        most_common = counter.most_common(1)[0]

        # 解密水印
        return self.zw_string_to_text(most_common[0])

    def _write_backup_layer_1(self, custom_xml_content: Optional[str], base64_watermark: str) -> str:
        """
        备份层1: 写入 docProps/custom.xml 自定义属性

        Args:
            custom_xml_content: 原始 custom.xml 内容
            base64_watermark: base64 编码的水印

        Returns:
            修改后的 custom.xml 内容
        """
        base64_watermark = base64_watermark.replace('<', '&lt;').replace('>', '&gt;')

        if not custom_xml_content:
            # 创建新的 custom.xml
            return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <property name="wm_backup" fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="2">
    <vt:lpwstr>{base64_watermark}</vt:lpwstr>
  </property>
  <property name="wm_marker" fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="3">
    <vt:lpwstr>WATERMARK_V1</vt:lpwstr>
  </property>
</Properties>'''

        # 在现有内容中添加水印属性
        if '<property name="wm_backup"' not in custom_xml_content:
            # 在 Properties 标签内添加
            props_pattern = re.compile(r'(</Properties>)')
            new_props = f'''  <property name="wm_backup" fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="2">
    <vt:lpwstr>{base64_watermark}</vt:lpwstr>
  </property>
  <property name="wm_marker" fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="3">
    <vt:lpwstr>WATERMARK_V1</vt:lpwstr>
  </property>
\\1'''
            return props_pattern.sub(new_props, custom_xml_content)

        return custom_xml_content

    def _write_backup_layer_2(self, content_types_xml_content: str, base64_watermark: str) -> str:
        """
        备份层2: 写入 [Content_Types].xml 注释

        Args:
            content_types_xml_content: 原始 [Content_Types].xml 内容
            base64_watermark: base64 编码的水印

        Returns:
            修改后的内容
        """
        # 在文件开头添加注释
        comment = f'<!-- wm_data:{base64_watermark} -->'

        if '<!-- wm_data:' not in content_types_xml_content:
            # 在 XML 声明后插入
            xml_decl_pattern = re.compile(r'(<\?xml[^>]*\\?>\\s*)')
            return xml_decl_pattern.sub(f'\\1{comment}\\n', content_types_xml_content)

        return content_types_xml_content

    def _write_backup_layer_3(self, settings_xml_content: str, base64_watermark: str) -> str:
        """
        备份层3: 写入 word/settings.xml 注释

        Args:
            settings_xml_content: 原始 settings.xml 内容
            base64_watermark: base64 编码的水印

        Returns:
            修改后的内容
        """
        comment = f'<!-- wm_store:{base64_watermark} -->'

        if '<!-- wm_store:' not in settings_xml_content:
            # 在根标签前插入
            root_pattern = re.compile(r'(<w:settings[^>]*>)')
            return root_pattern.sub(f'{comment}\\n\\1', settings_xml_content)

        return settings_xml_content

    def _write_backup_layer_4(self, header_xml_content: Optional[str], base64_watermark: str) -> Optional[str]:
        """
        备份层4: 写入页眉 XML 隐藏文本

        Args:
            header_xml_content: 页眉 XML 内容
            base64_watermark: base64 编码的水印

        Returns:
            修改后的页眉内容，如果没有页眉则返回 None
        """
        if not header_xml_content:
            return None

        # 检查是否已存在水印
        if 'WM:' in header_xml_content and '<w:vanish/>' in header_xml_content:
            return header_xml_content

        # 查找合适的位置插入隐藏文本
        # 在最后一个段落末尾添加
        hidden_run = f'<w:r><w:rPr><w:vanish/></w:rPr><w:t>WM:{base64_watermark}</w:t></w:r>'

        # 在最后一个 </w:p> 前插入
        p_end_pattern = re.compile(r'(</w:p>)(?!.*</w:p>)')
        if p_end_pattern.search(header_xml_content):
            return p_end_pattern.sub(f'{hidden_run}\\1', header_xml_content)

        return header_xml_content

    def _write_backup_layer_5(self) -> str:
        """
        备份层5: 生成独立备份文件内容

        Returns:
            独立备份文件的 XML 内容
        """
        # 这个方法需要在实际嵌入时传入 base64_watermark
        return ''  # 占位符，实际在 embed_watermark 中处理

    def _extract_from_backup_layer_1(self, custom_xml_content: str) -> Optional[dict]:
        """
        从备份层1提取水印

        Args:
            custom_xml_content: custom.xml 内容

        Returns:
            水印数据，失败返回 None
        """
        # 查找 wm_backup 属性
        pattern = re.compile(r'<property name="wm_backup"[^>]*>\\s*<vt:lpwstr>([^<]+)</vt:lpwstr>')
        match = pattern.search(custom_xml_content)

        if match:
            base64_data = match.group(1).replace('&lt;', '<').replace('&gt;', '>')
            return self.from_base64_watermark(base64_data)

        return None

    def _extract_from_backup_layer_2(self, content_types_xml_content: str) -> Optional[dict]:
        """
        从备份层2提取水印

        Args:
            content_types_xml_content: [Content_Types].xml 内容

        Returns:
            水印数据，失败返回 None
        """
        pattern = re.compile(r'<!-- wm_data:([^>]+) -->')
        match = pattern.search(content_types_xml_content)

        if match:
            return self.from_base64_watermark(match.group(1))

        return None

    def _extract_from_backup_layer_3(self, settings_xml_content: str) -> Optional[dict]:
        """
        从备份层3提取水印

        Args:
            settings_xml_content: settings.xml 内容

        Returns:
            水印数据，失败返回 None
        """
        pattern = re.compile(r'<!-- wm_store:([^>]+) -->')
        match = pattern.search(settings_xml_content)

        if match:
            return self.from_base64_watermark(match.group(1))

        return None

    def _extract_from_backup_layer_4(self, header_xml_content: str) -> Optional[dict]:
        """
        从备份层4提取水印

        Args:
            header_xml_content: 页眉 XML 内容

        Returns:
            水印数据，失败返回 None
        """
        pattern = re.compile(r'<w:t>WM:([^<]+)</w:t>')
        match = pattern.search(header_xml_content)

        if match:
            return self.from_base64_watermark(match.group(1))

        return None

    def _extract_from_backup_layer_5(self, backup_xml_content: str) -> Optional[dict]:
        """
        从备份层5提取水印

        Args:
            backup_xml_content: 独立备份文件内容

        Returns:
            水印数据，失败返回 None
        """
        pattern = re.compile(r'<wm:data>([^<]+)</wm:data>')
        match = pattern.search(backup_xml_content)

        if match:
            return self.from_base64_watermark(match.group(1))

        return None

    def embed_watermark(self, input_path: str, output_path: str,
                        user_info: str, department: str = '', project: str = '') -> dict:
        """
        嵌入水印到文档

        Args:
            input_path: 输入文档路径
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
            'backup_written': [],
            'error': None
        }

        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            # 生成 base64 水印（用于备份层）
            base64_watermark = self.to_base64_watermark(user_info, department, project)
            # 生成零宽水印（用于主层）
            watermark_data = self.build_watermark_data(user_info, department, project)
            zw_watermark = self.text_to_zw_string(json.dumps(watermark_data, ensure_ascii=False))

            with zipfile.ZipFile(input_path, 'r') as zin:
                # 处理每个文件
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.namelist():
                        content = zin.read(item).decode('utf-8', errors='ignore')

                        if item == 'word/document.xml':
                            # 嵌入零宽水印
                            modified_xml = self._embed_to_document_xml(content, zw_watermark)
                            result['paragraphs_processed'] = len(self._find_embedding_positions(content))
                            zout.writestr(item, modified_xml.encode('utf-8'))

                        elif item == 'docProps/custom.xml':
                            # 备份层1
                            modified_xml = self._write_backup_layer_1(content, base64_watermark)
                            zout.writestr(item, modified_xml.encode('utf-8'))
                            result['backup_written'].append('custom.xml')

                        elif item == '[Content_Types].xml':
                            # 备份层2
                            modified_xml = self._write_backup_layer_2(content, base64_watermark)
                            zout.writestr(item, modified_xml.encode('utf-8'))
                            result['backup_written'].append('[Content_Types].xml')

                        elif item == 'word/settings.xml':
                            # 备份层3
                            modified_xml = self._write_backup_layer_3(content, base64_watermark)
                            zout.writestr(item, modified_xml.encode('utf-8'))
                            result['backup_written'].append('settings.xml')

                        elif item.startswith('word/header') and item.endswith('.xml'):
                            # 备份层4: 页眉
                            modified_xml = self._write_backup_layer_4(content, base64_watermark)
                            if modified_xml:
                                zout.writestr(item, modified_xml.encode('utf-8'))
                                result['backup_written'].append(item)

                        else:
                            # 复制其他文件
                            zout.writestr(item, zin.read(item))

                    # 写入备份层5: 独立备份文件
                    backup_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<wm:WatermarkBackup xmlns:wm="http://watermark.local/2024">
  <wm:data>{base64_watermark}</wm:data>
  <wm:version>1.0</wm:version>
</wm:WatermarkBackup>'''
                    zout.writestr('word/watermark_backup.xml', backup_content.encode('utf-8'))
                    result['backup_written'].append('watermark_backup.xml')

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def extract_watermark(self, file_path: str) -> dict:
        """
        从文档中提取水印

        Args:
            file_path: 文档路径

        Returns:
            提取结果
        """
        result = {
            'success': False,
            'has_watermark': False,
            'integrity': 0,
            'watermark_data': None,
            'source': None,
            'error': None
        }

        try:
            file_path = Path(file_path)

            with zipfile.ZipFile(file_path, 'r') as z:
                # 按优先级尝试提取
                extraction_sources = [
                    ('docProps/custom.xml', self._extract_from_backup_layer_1),
                    ('[Content_Types].xml', self._extract_from_backup_layer_2),
                    ('word/settings.xml', self._extract_from_backup_layer_3),
                    ('word/watermark_backup.xml', self._extract_from_backup_layer_5),
                ]

                # 首先尝试从备份层提取
                for filename, extractor in extraction_sources:
                    if filename in z.namelist():
                        content = z.read(filename).decode('utf-8', errors='ignore')
                        watermark_data = extractor(content)
                        if watermark_data:
                            result['watermark_data'] = watermark_data
                            result['has_watermark'] = True
                            result['source'] = filename
                            result['success'] = True
                            result['integrity'] = 100
                            return result

                # 尝试从页眉提取
                header_files = [f for f in z.namelist() if f.startswith('word/header') and f.endswith('.xml')]
                for header_file in header_files:
                    content = z.read(header_file).decode('utf-8', errors='ignore')
                    watermark_data = self._extract_from_backup_layer_4(content)
                    if watermark_data:
                        result['watermark_data'] = watermark_data
                        result['has_watermark'] = True
                        result['source'] = header_file
                        result['success'] = True
                        result['integrity'] = 100
                        return result

                # 最后尝试从零宽字符提取
                if 'word/document.xml' in z.namelist():
                    content = z.read('word/document.xml').decode('utf-8', errors='ignore')

                    # 计算完整度
                    zw_pattern = re.compile(r'[\u200b\u200c]+')
                    zw_sequences = zw_pattern.findall(content)

                    if zw_sequences:
                        counter = Counter(zw_sequences)
                        most_common = counter.most_common(1)[0]

                        # 计算完整度
                        total = len(zw_sequences)
                        consistent = most_common[1]
                        result['integrity'] = round(consistent / total * 100, 1)

                        # 解密水印
                        watermark_data = self.zw_string_to_text(most_common[0])
                        if watermark_data:
                            try:
                                watermark_dict = json.loads(watermark_data)
                                if self.crypto.validate_crc(watermark_dict):
                                    result['watermark_data'] = watermark_dict
                                    result['has_watermark'] = True
                                    result['source'] = 'zero_width'
                                    result['success'] = True
                                    return result
                            except Exception:
                                pass

            result['error'] = '未发现水印'

        except Exception as e:
            result['error'] = str(e)

        return result