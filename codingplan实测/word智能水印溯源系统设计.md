 **“word智能数字水印与溯源系统”**。

它不再是一个通用的隐写工具，而是一个专用的安全工具。

以下是针对该目标重新设计的**需求文档 (PRD)** 和 **技术架构文档 (TD)**。

# ---

**1\. 需求文档 (Product Requirement Document)**

## **1.1 项目背景与目标**

针对企业敏感 Word 文档流出后难以追溯责任人的问题，开发一款具备 UI 界面的工具。用户可以使用该工具为文档嵌入唯一的、不易察觉的、且具有一定抗破坏能力的溯源水印（UID），并在发现疑似泄露文档时，通过分析对比功能还原该 UID，从而锁定泄密源头。

## **1.2 用户角色与场景**

* **发布者（审计员）：** 在分发敏感文档前，打开 UI 工具，输入接收者信息（如姓名/工号），工具生成带有唯一标识的 docx 文件。  
* **取证员：** 在公网或竞品处发现疑似泄露的 docx 文件，打开 UI 工具，导入文件进行“分析对比”，工具解密并输出原始接收者信息。

## **1.3 核心功能需求**

| 模块 | 功能点 | 描述 | 优先级 |
| :---- | :---- | :---- | :---- |
| **A. 水印嵌入 (Watermarking)** | **用户/部门映射** | 在界面输入“张三-工号123”，系统自动生成唯一 ID（UID）并记录。 | 高 |
|  | **无损嵌入** | 将加密后的 UID 嵌入 DOCX，不改变文档视觉排版、字体、颜色。 | 高 |
|  | **冗余嵌入** | 水印信息需遍布文档全局（如每个段落、表格），防止部分截取导致水印丢失。 | 高 |
|  | **预处理加密** | 水印数据必须经由系统秘钥加密，防止被第三方轻易识别和伪造。 | 高 |
| **B. 分析溯源 (Analysis)** | **单文件分析** | 导入可疑 docx 文件，自动扫描全文档并尝试提取、解密水印。 | 高 |
|  | **溯源对比** | 将提取的 UID 与本地记录（或用户手动输入的记录）对比，输出明确的溯源结果。 | 高 |
|  | **鲁棒性支持** | 支持对仅剩部分内容的文本（如复制出的纯文本）进行水印提取（依赖所选算法）。 | 中 |
| **C. 管理与 UI (Admin & UI)** | **图形化界面** | 简洁直观的界面，支持文件拖拽、状态显示。 | 高 |
|  | **项目/秘钥管理** | 支持为不同项目设置不同的加密秘钥，增强安全性。 | 高 |
|  | **密钥导入/导出** | 支持密钥备份到文件和从文件恢复。 | 高 |
|  | **密钥删除** | 支持删除不再需要的密钥。 | 中 |

## **1.4 非功能性需求**

* **隐蔽性：** 普通用户在 Word 中正常阅读时无法察觉水印存在。  
* **抗破坏性（鲁棒性）：** 能够抵御剪切、部分内容删除、轻微样式修改的破坏。  
* **兼容性：** 支持 Office 2007+ 的标准 .docx 格式。

# ---

**2\. 技术文档 (Technical Design Document)**

## **2.1 技术栈选择**

* **UI 框架：** Python 的 PyQt6 或 PySide6（成熟、专业、跨平台，适合安全工具开发）。  
* **DOCX 处理库：** python-docx（处理基础内容）+ lxml（处理底层原生 XML，用于更隐蔽的嵌入）。  
* **加密库：** cryptography（用于 AES-256 加密）。

## **2.2 核心算法方案：多层冗余水印 (Multi-Layer Redundant Watermark)**

鉴于目的是溯源且要求无损，采用**零宽字符为主、元数据备份为辅**的组合方案。

### **2.2.1 水印层级设计**

| 层级 | 技术 | 隐蔽性 | 鲁棒性 | 用途 |
|------|------|--------|--------|------|
| 主层 | 零宽字符嵌入 | 极高 | 中等 | 主要溯源载体 |
| 备层1 | 文档属性(自定义) base64 | 低 | 高 | 零宽丢失时的备用 |
| 备层2 | [Content_Types].xml 注释 | 高 | 高 | 文档结构完整时可用 |
| 备层3 | settings.xml 注释 | 高 | 高 | WPS兼容层 |
| 备层4 | 页眉隐藏文本 | 极高 | 高 | 不可见但保留 |
| 备层5 | 独立XML备份文件 | 中 | 高 | 独立文件不易被覆盖 |

### **嵌入原理：**

1. **数据生成：** UID ("ZhangSan-123") + 时间戳 + CRC校验 → 压缩 → AES加密 → 二进制流 (e.g., 0110...)。
2. **字符映射：** 将二进制 0 映射为 \u200b (零宽空格)，1 映射为 \u200c (零宽不连通符)。
3. **冗余插入：** 遍历 document.xml 中的所有 `<w:p>`（段落标签），将生成的零宽字符串链插入到每个段落最后一个 `<w:t>` 节点末尾。
4. **五层备份写入：** 将加密后的完整水印数据（base64格式）同时写入5个不同位置，防止WPS/Word重写时全部丢失。

### **识别流程：**

1. **优先从备份层提取**（按优先级依次尝试）：
   - `docProps/custom.xml` 自定义属性
   - `[Content_Types].xml` 注释
   - `word/settings.xml` 注释
   - 页眉XML隐藏文本
   - `word/watermark_backup.xml` 独立文件
2. **主层提取：** 读取全文档的 XML，使用正则表达式 [\u200b\u200c]+ 提取所有连串的零宽字符。
3. **少数服从多数：** 由于是冗余嵌入，如果文档被部分修改，提取出的多组零宽字符串可能不一致。系统需对比所有提取出的字符串，选择出现频率最高的一组作为有效数据。
4. **校验完整性：** 对提取数据进行 CRC 校验，确保数据未损坏。
5. **还原：** 零宽串/base64 → 二进制 → AES解密 → 原始UID。
6. **全文件扫描：** 若以上全部失败，扫描所有XML文件中的base64数据尝试解密。

### **2.2.2 潜在风险与应对策略**

| 风险场景 | 影响 | 应对策略 |
|----------|------|----------|
| 复制粘贴为纯文本 | 零宽字符丢失 | 五层备份策略 |
| 微信/钉钉传输 | 可能清洗零宽字符 | 建议打包为ZIP传输 |
| Word转PDF | 部分情况丢失 | 转换后需验证水印 |
| 格式刷/清除格式 | 可能删除零宽字符 | 多段落冗余+备份层 |
| 第三方编辑器 | 可能过滤特殊字符 | settings.xml/页眉备份层保留 |
| **WPS重写文档** | **清除零宽+覆盖custom.xml** | **五层备份+base64完整存储** |
| **Word另存为** | **可能重建XML结构** | **独立XML备份文件+隐藏文本** |

### **2.2.3 五层备份策略（防WPS/Word重写优化）**

经过实际测试发现，WPS/Word在重新保存文档时会：
1. 清除所有零宽字符（主水印层丢失）
2. 完全覆盖 `docProps/custom.xml`（自定义属性丢失）
3. 可能清理 `[Content_Types].xml` 注释

针对此问题，采用**五层冗余备份**策略，将水印数据写入多个WPS/Word不会修改的位置：

| 层级 | 存储位置 | 数据格式 | 特点 |
|------|----------|----------|------|
| 层1 | `docProps/custom.xml` | 自定义属性 base64 | 标准属性，Word可能保留 |
| 层2 | `[Content_Types].xml` 注释 | XML注释 base64 | Word通常保留注释 |
| 层3 | `word/settings.xml` 注释 | XML注释 base64 | WPS通常保留此文件 |
| 层4 | 页眉XML隐藏文本 | `<w:vanish/>` run | 不可见但保留 |
| 层5 | `word/watermark_backup.xml` | 独立XML文件 | 独立备份，不易被覆盖 |

**备份数据格式改进**：
- 旧方案：截取200个零宽字符作为备份（数据不足，无法解密）
- 新方案：完整加密数据使用base64编码存储（数据完整，体积小，可靠）

**提取优先级**：
1. `docProps/custom.xml` 自定义属性
2. `[Content_Types].xml` 注释
3. `word/settings.xml` 注释
4. 页眉XML隐藏文本
5. `word/watermark_backup.xml` 独立文件
6. 全文零宽字符搜索（多数投票）
7. 全XML文件base64数据扫描

### **2.2.4 水印数据结构**

```json
{
  "version": "1.0",
  "uid": "ZhangSan-123",
  "department": "销售部",
  "timestamp": "2024-01-15T10:30:00",
  "project": "Project_Alpha",
  "crc": "A3F2"
}
```

## **2.3 UI 界面设计草图**

工具将采用双标签页（Tab）结构：

### **Tab 1: 文档处理 (Embedder)**

Plaintext

\+-------------------------------------------------------+  
|  \[ 标签页1：水印嵌入 \]    \[ 标签页2：分析溯源 \]          |  
\+-------------------------------------------------------+  
|                                                       |  
|  1\. 选择原始文档:                                     |  
|     \[\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\] \[浏览...\]  |  
|                                                       |  
|  2\. 输入溯源信息 (如接收者姓名/工号/项目):             |  
|     \[ 张三 \- 销售部 \- 20231015           \]             |  
|                                                       |  
|  3\. 安全设置:                                         |  
|     秘钥 ID: \[ Project\_Alpha\_Key \] (下拉选择/新建)    |  
|                                                       |  
|                     \[ 开始嵌入水印 \]                   |  
|                                                       |  
|  日志输出:                                            |  
|  \[+\] 秘钥已就绪...                                    |  
|  \[+\] 成功生成 UID...                                  |  
|  \[+\] 已在 45 个段落中冗余嵌入水印...                    |  
|  \[+\] 成功保存至: C:\\output\\confidential\_signed.docx |  
\+-------------------------------------------------------+

### **Tab 2: 分析对比 (Analyzer)**

Plaintext

\+-------------------------------------------------------+  
|  \[ 标签页1：水印嵌入 \]    \[ 标签页2：分析溯源 \]          |  
\+-------------------------------------------------------+  
|                                                       |  
|  1\. 选择待分析文档 (支持拖拽):                         |  
|     \[\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\] \[浏览...\]  |  
|                                                       |  
|  2\. 安全设置:                                         |  
|     尝试使用秘钥 ID: \[ Project\_Alpha\_Key \] (下拉选择)  |  
|                                                       |  
|                     \[ 开始分析对比 \]                   |  
|                                                       |  
|  分析结果:                                            |  
|  \+-------------------------------------------------+  |  
|  |  是否发现水印: \[ 是 \]                            |  |  
|  |  水印完整度:   \[ 85% (可信度高) \]                |  |  
|  |  \*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\* |  |  
|  |  溯源信息: \[ 张三 \- 销售部 \- 20231015 \]         |  |  
|  |  \*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\* |  |  
|  \+-------------------------------------------------+  |  
|                                                       |  
|  提取详情日志:                                        |  
|  \[+\] 发现 42 组零宽字符标记...                         |  
|  \[+\] 经多点对比，确定有效数据链...                    |  
|  \[+\] 解密成功。                                      |  
\+-------------------------------------------------------+

## **2.4 关键数据结构与核心代码实现**

### **2.4.1 数据库设计**

```sql
-- 数据存储建议：使用轻量级 SQLite 存储秘钥和分发记录
-- table: keys (密钥管理)
CREATE TABLE keys (
    id INTEGER PRIMARY KEY,
    key_name TEXT UNIQUE NOT NULL,
    key_value_encrypted BLOB NOT NULL,
    salt BLOB NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- table: trace_logs (分发记录)
CREATE TABLE trace_logs (
    id INTEGER PRIMARY KEY,
    uid TEXT UNIQUE NOT NULL,
    user_info TEXT NOT NULL,
    key_id INTEGER,
    original_filename TEXT,
    watermark_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (key_id) REFERENCES keys(id)
);
```

### **2.4.2 核心类实现**

```python
import zipfile
import json
import zlib
import base64
from pathlib import Path
from datetime import datetime
from lxml import etree
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from collections import Counter

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
        if master_password:
            self.salt = salt or b'docx_watermark_salt_v1'
            self.master_key = self._derive_key(master_password, self.salt)
        else:
            self.master_key = Fernet.generate_key()
            self.salt = b'default_salt'
        
        self.cipher = Fernet(self.master_key)
        
        # Unicode 映射 (零宽字符)
        self.ZERO_WIDTH_MAP = {'0': '\u200b', '1': '\u200c'}
        self.REV_ZERO_WIDTH_MAP = {'\u200b': '0', '\u200c': '1'}
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """从主密码派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
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
            decrypted_data = self.cipher.decrypt(bytes(byte_arr))
            return decrypted_data.decode('utf-8')
        except Exception:
            return None  # 密钥不匹配或数据损坏
    
    def _find_paragraph_ends(self, root) -> list:
        """
        精确定位每个段落的最后一个 <w:t> 节点
        
        Returns:
            包含 (段落索引, w:t节点) 的列表
        """
        paragraphs = root.findall('.//w:p', self.NAMESPACES)
        insert_points = []
        
        for p_idx, para in enumerate(paragraphs):
            # 查找段落内所有 <w:t> 节点
            text_nodes = para.findall('.//w:t', self.NAMESPACES)
            if text_nodes:
                # 选择最后一个非空的 <w:t> 节点
                for t_node in reversed(text_nodes):
                    if t_node.text and len(t_node.text.strip()) > 0:
                        insert_points.append((p_idx, t_node))
                        break
        
        return insert_points
    
    def _add_document_property(self, doc_props_path: Path, watermark: str):
        """将水印写入文档自定义属性（备用层）"""
        try:
            if doc_props_path.exists():
                tree = etree.parse(str(doc_props_path))
                root = tree.getroot()
            else:
                # 创建新的属性文件
                root = etree.Element('{http://schemas.openxmlformats.org/officeDocument/2006/custom-properties}Properties')
            
            # 添加自定义属性
            prop = etree.SubElement(root, 'property')
            prop.set('name', 'wm_backup')
            prop.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
            value = etree.SubElement(prop, '{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}lpwstr')
            value.text = watermark
            
            tree = etree.ElementTree(root)
            tree.write(str(doc_props_path), xml_declaration=True, encoding='UTF-8', standalone=True)
        except Exception as e:
            print(f"写入文档属性失败: {e}")
    
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
        # 构建水印数据
        watermark_data = self._build_watermark_data(user_info, department, project)
        watermark_json = json.dumps(watermark_data, ensure_ascii=False)
        zw_watermark = self._text_to_zw_string(watermark_json)
        
        result = {
            'success': False,
            'paragraphs_processed': 0,
            'backup_written': False,
            'error': None
        }
        
        try:
            # 1. 解压 DOCX
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            with zipfile.ZipFile(input_path, 'r') as zin:
                # 读取 document.xml
                with zin.open('word/document.xml') as f:
                    doc_xml = f.read()
                
                # 解析 XML
                root = etree.fromstring(doc_xml)
                
                # 2. 查找插入点
                insert_points = self._find_paragraph_ends(root)
                
                if not insert_points:
                    result['error'] = '文档中没有可用的文本段落'
                    return result
                
                # 3. 在每个段落末尾插入零宽字符
                for p_idx, t_node in insert_points:
                    if t_node.text:
                        t_node.text += zw_watermark
                
                result['paragraphs_processed'] = len(insert_points)
                
                # 4. 写入新文档
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.namelist():
                        if item == 'word/document.xml':
                            # 写入修改后的 document.xml
                            modified_xml = etree.tostring(root, xml_declaration=True, 
                                                          encoding='UTF-8', standalone=True)
                            zout.writestr(item, modified_xml)
                        else:
                            # 复制其他文件
                            zout.writestr(item, zin.read(item))
                    
                    # 5. 写入备份水印到文档属性
                    try:
                        doc_props_path = 'docProps/custom.xml'
                        props_data = zin.read(doc_props_path) if doc_props_path in zin.namelist() else None
                        
                        # 创建临时文件处理属性
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
                            if props_data:
                                tmp.write(props_data)
                            tmp_path = Path(tmp.name)
                        
                        self._add_document_property(tmp_path, zw_watermark[:100] + '...')  # 截取部分作为备份
                        zout.write(tmp_path, doc_props_path)
                        tmp_path.unlink()
                        result['backup_written'] = True
                    except:
                        pass  # 备份层写入失败不影响主流程
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
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
            'extracted_count': 0,
            'error': None
        }
        
        try:
            file_path = Path(file_path)
            
            with zipfile.ZipFile(file_path, 'r') as z:
                # 读取 document.xml
                with z.open('word/document.xml') as f:
                    content = f.read().decode('utf-8')
            
            # 提取所有零宽字符序列
            import re
            zw_pattern = re.compile(r'[\u200b\u200c]+')
            zw_sequences = zw_pattern.findall(content)
            
            if not zw_sequences:
                result['error'] = '未发现水印'
                return result
            
            result['extracted_count'] = len(zw_sequences)
            
            # 多数投票确定有效数据
            counter = Counter(zw_sequences)
            most_common = counter.most_common(1)[0]
            
            # 计算完整度
            total = len(zw_sequences)
            consistent = most_common[1]
            result['integrity'] = round(consistent / total * 100, 1)
            
            # 解密水印
            watermark_json = self._zw_string_to_text(most_common[0])
            
            if watermark_json:
                watermark_data = json.loads(watermark_json)
                
                # 验证 CRC
                stored_crc = watermark_data.pop('crc', None)
                calculated_crc = self._calculate_crc(json.dumps(watermark_data, sort_keys=True))
                
                if stored_crc == calculated_crc:
                    result['watermark_data'] = watermark_data
                    result['has_watermark'] = True
                    result['success'] = True
                else:
                    result['error'] = '水印数据校验失败，可能已被篡改'
            else:
                result['error'] = '水印解密失败，密钥可能不匹配'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result

## ---

## **2.5 进一步开发建议**

### **2.5.1 功能增强**

对于**溯源工具**，UI 界面可以更进一步集成：

1. **批量生成：** 导入一个 Excel 员工列表，自动为列表中的每个人生成一个专属的水印文档，存放于不同文件夹。
2. **水印抗性测试（内测功能）：** UI 提供按钮，自动模拟”删除第一段”、”修改字体”等操作，随后运行分析，计算水印的鲁棒性得分。
3. **密钥轮换机制：** 定期自动更新加密密钥，旧密钥归档保留用于解密历史文档。
4. **审计日志：** 记录所有水印嵌入和提取操作，支持导出审计报告。

### **2.5.2 安全增强建议**

```python
# 1. 密钥安全存储
class SecureKeyStorage:
    “””安全密钥存储 - 使用系统密钥库”””
    
    def __init__(self):
        # Windows: 使用 DPAPI
        # macOS: 使用 Keychain
        # Linux: 使用 Secret Service
        pass
    
    def store_key(self, key_name: str, key_value: bytes, master_password: str):
        “””使用主密码加密后存储密钥”””
        pass

# 2. 水印时效性验证
def validate_watermark_freshness(watermark_data: dict, max_age_days: int = 365) -> bool:
    “””验证水印是否在有效期内”””
    timestamp = datetime.fromisoformat(watermark_data['timestamp'])
    age = datetime.now() - timestamp
    return age.days <= max_age_days

# 3. 防篡改校验
def generate_document_hash(file_path: str) -> str:
    “””生成文档哈希，用于检测篡改”””
    import hashlib
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]
```

### **2.5.3 项目结构建议**

```
docx-watermark-tool/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── watermark.py      # 水印核心类
│   │   ├── crypto.py         # 加密模块
│   │   └── parser.py         # DOCX解析模块
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py    # 主窗口
│   │   ├── embed_tab.py      # 嵌入标签页
│   │   └── analyze_tab.py    # 分析标签页
│   ├── db/
│   │   ├── __init__.py
│   │   └── models.py         # 数据库模型
│   └── utils/
│       ├── __init__.py
│       ├── logger.py         # 日志工具
│       └── config.py         # 配置管理
├── tests/
│   ├── test_watermark.py
│   └── test_robustness.py
├── requirements.txt
└── main.py
```

### **2.5.4 测试用例设计**

```python
# tests/test_robustness.py

def test_partial_deletion():
    “””测试部分删除后的水印提取”””
    # 1. 嵌入水印
    # 2. 删除文档 50% 内容
    # 3. 验证水印仍可提取
    pass

def test_copy_paste():
    “””测试复制粘贴后水印保留”””
    # 1. 嵌入水印
    # 2. 全选复制到新文档
    # 3. 验证水印完整性
    pass

def test_format_changes():
    “””测试格式修改后水印保留”””
    # 1. 嵌入水印
    # 2. 修改字体、颜色、大小
    # 3. 验证水印完整性
    pass

def test_key_mismatch():
    “””测试密钥不匹配时的错误处理”””
    # 使用错误密钥应返回明确的错误信息
    pass
```

### **2.5.5 已知限制与应对**

| 限制 | 说明 | 应对措施 |
|------|------|----------|
| PDF转换 | Word转PDF可能丢失零宽字符 | 转换后验证；或开发专用PDF水印模块 |
| 在线编辑 | WPS/Google Docs可能过滤特殊字符 | 五层备份策略（settings/页眉/独立文件） |
| OCR识别 | 扫描件无法提取零宽字符 | 不适用扫描件；可考虑图像水印 |
| 文本提取 | 纯文本导出会丢失水印 | 五层备份策略，至少保留XML层 |
| WPS重写 | 清除零宽+覆盖custom.xml | 五层冗余备份+base64完整存储 |

---

## **3. 开发问题记录与解决方案**

### **3.1 PyQt6 DLL 加载失败**

| 项目 | 内容 |
|------|------|
| **问题** | `ImportError: DLL load failed while importing QtWidgets: 找不到指定的程序` |
| **原因** | PyQt6 在 Windows 环境下 DLL 依赖问题 |
| **解决方案** | 改用 PySide6（Qt 官方维护的 Python 绑定），完全兼容 PyQt6 API |
| **修改文件** | `src/ui/main_window.py`, `main.py` |

```python
# 修改前
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# 修改后
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QThread, Signal  # pyqtSignal -> Signal
```

---

### **3.2 水印解密失败 - 密钥不匹配**

| 项目 | 内容 |
|------|------|
| **问题** | 嵌入水印成功，但分析时提示"密钥不匹配" |
| **原因** | 每次创建 `DocxWatermarkTool` 时，如果没有提供密码，会自动生成随机密钥 |
| **解决方案** | 使用固定默认密码派生密钥，确保嵌入和分析使用相同密钥 |
| **修改文件** | `src/core/crypto.py` |

```python
# 修改前
if master_password:
    self.key = self._derive_key(master_password, self.salt)
else:
    self.key = Fernet.generate_key()  # 每次生成随机密钥

# 修改后
DEFAULT_PASSWORD = 'docx_watermark_default_key_2024'  # 固定默认密码
password = master_password or self.DEFAULT_PASSWORD
self.key = self._derive_key(password, self.salt)
```

---

### **3.3 数据库表结构不匹配**

| 项目 | 内容 |
|------|------|
| **问题** | `sqlite3.OperationalError: table keys has no column named key_password` |
| **原因** | 代码修改了表结构（从 `key_value_encrypted` 改为 `key_password`），但旧数据库未更新 |
| **解决方案** | 删除旧数据库文件，重新初始化新表结构 |
| **命令** | `Remove-Item -Force watermark.db` |

---

### **3.4 重复类定义导致方法冲突**

| 项目 | 内容 |
|------|------|
| **问题** | `KeyManager` 类定义了两次，导致方法签名冲突 |
| **原因** | 代码重构时保留了旧版本的 `KeyManager` 类 |
| **解决方案** | 删除重复的 `KeyManager` 类定义，保留最新版本 |
| **修改文件** | `src/db/models.py` |

```python
# 删除第 299-396 行的旧 KeyManager 类
class KeyManager:
    # ... 旧代码（已删除）
```

---

### **3.5 分析页面密钥列表不同步**

| 项目 | 内容 |
|------|------|
| **问题** | 在嵌入页面新建密钥后，切换到分析页面看不到新建的密钥 |
| **原因** | 两个页面使用独立的密钥列表，未实现同步机制 |
| **解决方案** | 在 `MainWindow` 中添加 `refresh_analyze_keys()` 方法，新建/导入密钥时调用同步 |
| **修改文件** | `src/ui/main_window.py` |

```python
# MainWindow 中添加方法
def refresh_analyze_keys(self):
    """刷新分析页面的密钥列表"""
    self.analyze_tab.refresh_keys()

# EmbedTab._new_key() 中添加同步调用
self.window().refresh_analyze_keys()
```

**注意**：`parent()` 路径不正确，需使用 `self.window()` 获取主窗口

```python
# 错误写法
self.parent().parent().refresh_analyze_keys()  # QStackedWidget -> QTabWidget

# 正确写法
self.window().refresh_analyze_keys()  # 直接获取主窗口
```

---

### **3.6 中文路径支持**

| 项目 | 内容 |
|------|------|
| **说明** | 代码已使用 `pathlib.Path` 处理路径，理论上支持中文路径 |
| **注意** | Windows 终端显示中文时可能出现乱码，但实际文件操作正常 |
| **建议** | 避免在命令行直接操作中文路径文件 |

---

### **3.7 嵌入后文档格式差异过大**

| 项目 | 内容 |
|------|------|
| **问题** | 嵌入水印后，文档在 Word 中打开时格式与原文档差异明显，影响阅读 |
| **原因** | 使用 lxml 解析 XML 后重新序列化，导致 XML 结构和格式完全改变 |
| **解决方案** | 直接操作 XML 字符串，只在指定位置插入零宽字符，保留原始格式 |
| **修改文件** | `src/core/watermark.py` |

```python
# 修改前：使用 lxml 解析
parser = DocxParser(input_path)
root = parser.root
# ... 修改节点 ...
xml_content = etree.tostring(root)  # 完全重写 XML

# 修改后：直接操作字符串
with zipfile.ZipFile(input_path, 'r') as zin:
    with zipfile.ZipFile(output_path, 'w') as zout:
        for item in zin.namelist():
            content = zin.read(item)
            if item == 'word/document.xml':
                # 直接在 XML 字符串中替换
                xml_content = content.decode('utf-8')
                xml_content = xml_content.replace('</w:t>', '</w:t>' + watermark)
                zout.writestr(item, xml_content.encode('utf-8'))
            else:
                zout.writestr(item, content)
```

---

### **3.8 数据库加密密钥每次重启变化**

| 项目 | 内容 |
|------|------|
| **问题** | 程序重启后，之前存储的密钥密码无法解密 |
| **原因** | `Database._cipher` 在类定义时使用 `Fernet.generate_key()` 生成随机密钥 |
| **解决方案** | 使用固定的 Fernet 密钥（32字节 base64编码） |
| **修改文件** | `src/db/models.py` |

```python
# 修改前
class Database:
    _master_key = Fernet.generate_key()  # 每次启动都不同
    _cipher = Fernet(_master_key)

# 修改后
class Database:
    _master_key = b'oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ='  # 固定密钥（32字节 url-safe base64）
    _cipher = Fernet(_master_key)
```

**注意**：如果之前有使用旧密钥创建的数据库，需要删除重建。

> **2026-04-03 更新**：原密钥 `u2qmel6qYDwWxYr-w2ykIxvG4MqHUGsI3AIzBYkANjk=` 不是合法的 Fernet 密钥（Fernet 要求 32 字节 url-safe base64），已更正为 `oYlz74epy1ys1p12husdi70zFMifX6oJlwjgMbGKpfQ=`。

---

### **3.9 密钥列表数据存储不一致**

| 项目 | 内容 |
|------|------|
| **问题** | 选择密钥后提示"无法获取密钥密码" |
| **原因** | EmbedTab 使用 `key['id']` 作为下拉框数据，但获取密码需要 `key_name` |
| **解决方案** | 统一使用 `key['key_name']` 作为数据标识 |
| **修改文件** | `src/ui/main_window.py` |

```python
# EmbedTab._load_keys() 中
# 修改前
self.key_combo.addItem(key['key_name'], key['id'])

# 修改后
self.key_combo.addItem(key['key_name'], key['key_name'])
```

---

### **3.10 嵌入后完整度显示问题**

| 项目 | 内容 |
|------|------|
| **问题** | 删除部分内容后，一致性计数和完整度计算不准确 |
| **原因** | 嵌入位置减少后，每个段落的水印是完整的，完整度应该基于保留的段落数 |
| **解决方案** | 完整度基于多数投票的一致性计数比例计算 |

---

### **3.11 WPS/Word重写导致水印丢失**

| 项目 | 内容 |
|------|------|
| **问题** | 文档在WPS中修改保存后，水印提取失败，提示"未发现水印" |
| **原因分析** | WPS重写文档时：①清除所有零宽字符（主水印丢失）②完全覆盖`docProps/custom.xml`（备份丢失）③清理`[Content_Types].xml`注释 |
| **旧方案缺陷** | 备份仅存储200个零宽字符（不足解密）；备份位置单一（仅custom.xml） |
| **解决方案** | 五层冗余备份+base64完整存储 |
| **修改文件** | `src/core/watermark.py` |

**具体改进：**

1. **备份数据格式**：零宽字符编码 → base64编码（体积更小，更可靠）
2. **备份数据完整性**：截断200字符 → 完整加密数据
3. **备份位置**：1层 → 5层（custom.xml + Content_Types注释 + settings注释 + 页眉隐藏文本 + 独立XML文件）
4. **提取策略**：2种 → 7种（按优先级依次尝试）
5. **防覆盖设计**：在主文件复制循环中同步写入备份，避免重复写入同一文件

**测试验证**：
- 模拟Word清除零宽字符后，通过`docProps/custom.xml`备份层成功提取水印（完整度100%）
- 所有单元测试和鲁棒性测试通过

---

## **4. 最终实现方案**

### **4.1 水印嵌入策略**

| 文档长度 | 嵌入位置数 | 说明 |
|----------|------------|------|
| ≤10 段落 | 3 个位置 | 短文档多嵌入保证鲁棒性 |
| 11-30 段落 | 5 个位置 | 中等文档均衡 |
| >30 段落 | 8 个位置 | 长文档适度嵌入 |

**嵌入位置选择**：从文档中间开始，均匀分布。

### **4.2 水印提取策略（7层优先级）**

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | `docProps/custom.xml` 自定义属性 | 标准属性，Word可能保留 |
| 2 | `[Content_Types].xml` 注释 | XML注释，Word通常保留 |
| 3 | `word/settings.xml` 注释 | WPS兼容层 |
| 4 | 页眉XML隐藏文本 `<w:vanish/>` | 不可见但保留 |
| 5 | `word/watermark_backup.xml` 独立文件 | 独立备份，不易被覆盖 |
| 6 | 全文零宽字符搜索 | 多数投票确定有效数据 |
| 7 | 全XML文件base64扫描 | 最后的兜底方案 |

### **4.3 备份水印存储（五层写入）**

**层1 - custom.xml：**
```xml
<property name="wm_backup" fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}">
    <vt:lpwstr>base64加密的完整水印数据</vt:lpwstr>
</property>
<property name="wm_marker" fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}">
    <vt:lpwstr>WATERMARK_V1</vt:lpwstr>
</property>
```

**层2 - [Content_Types].xml 注释：**
```xml
<!-- wm_data:base64加密的完整水印数据 -->
```

**层3 - word/settings.xml 注释：**
```xml
<!-- wm_store:base64加密的完整水印数据 -->
```

**层4 - 页眉XML隐藏文本：**
```xml
<w:r><w:rPr><w:vanish/></w:rPr><w:t>WM:base64加密的完整水印数据</w:t></w:r>
```

**层5 - 独立备份文件 word/watermark_backup.xml：**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<wm:WatermarkBackup xmlns:wm="http://watermark.local/2024">
  <wm:data>base64加密的完整水印数据</wm:data>
  <wm:version>1.0</wm:version>
</wm:WatermarkBackup>
```

---

## **5. 版本更新记录**

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2024-04-03 | 初始版本，支持零宽字符水印嵌入和提取 |
| 1.0.1 | 2024-04-03 | 修复 PyQt6 兼容性问题，改用 PySide6 |
| 1.0.2 | 2024-04-03 | 修复密钥不匹配问题，使用固定默认密钥 |
| 1.0.3 | 2024-04-03 | 添加密钥导入/导出功能 |
| 1.0.4 | 2024-04-03 | 修复密钥列表同步问题，添加密钥删除功能 |
| 1.0.5 | 2024-04-03 | 修复文档格式差异问题，直接操作 XML 字符串 |
| 1.0.6 | 2024-04-03 | 修复数据库加密密钥固定问题 |
| 1.0.7 | 2024-04-03 | 优化嵌入策略，减少嵌入位置数量 |
| 1.0.8 | 2024-04-03 | 添加水印完整度显示和分析日志 |
| 1.0.9 | 2026-04-03 | 添加安装约束：国内镜像源 + 本地缓存目录 |
| 1.1.0 | 2026-04-03 | **重大修复**：五层冗余备份策略，解决WPS/Word重写导致水印丢失问题。备份格式从零宽字符改为base64，数据完整性从200字符截断改为完整存储 |

---

## **6. 项目结构**

```
word智能水印溯源系统/
├── main.py                    # 主入口文件 (GUI + CLI)
├── requirements.txt           # 依赖包
├── install.bat                # Windows 依赖安装脚本（国内镜像 + 本地缓存）
├── install.sh                 # Linux/macOS 依赖安装脚本
├── CLAUDE.md                  # 项目约束说明（安装规范）
├── config.json               # 配置文件
├── watermark.db             # SQLite 数据库（密钥和记录）
├── Docx 智能水印溯源系统设计.md  # 设计文档
│
├── src/
│   ├── __init__.py
│   ├── core/                  # 核心模块
│   │   ├── __init__.py
│   │   ├── watermark.py       # 水印核心类（嵌入/提取）
│   │   └── crypto.py          # 加密模块（密钥派生）
│   │
│   ├── ui/                    # UI 模块
│   │   ├── __init__.py
│   │   └── main_window.py     # 主窗口（双标签页）
│   │
│   ├── db/                    # 数据库模块
│   │   ├── __init__.py
│   │   └── models.py          # 数据模型（密钥/记录管理）
│   │
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       ├── logger.py          # 日志工具
│       └── config.py          # 配置管理
│
└── tests/                     # 测试模块
    ├── __init__.py
    ├── test_watermark.py      # 功能测试
    └── test_robustness.py     # 鲁棒性测试
```

---

## **7. 环境安装**

### **7.1 安装约束**

| 约束项 | 要求 |
|--------|------|
| **镜像源** | 必须使用国内镜像（清华 `https://pypi.tuna.tsinghua.edu.cn/simple`） |
| **缓存目录** | pip 缓存必须存放在程序所在目录的 `.pip_cache` 下 |
| **安装方式** | 使用项目提供的 `install.bat`（Windows）或 `install.sh`（Linux/macOS）脚本 |

### **7.2 快速安装**

**Windows：**
```cmd
.\install.bat
```

**Linux/macOS：**
```bash
chmod +x install.sh
./install.sh
```

安装脚本会自动设置镜像源和本地缓存目录，无需手动指定参数。

### **7.3 常用国内镜像源**

如需手动指定，可选用以下任意镜像：

| 镜像 | 地址 |
|------|------|
| 清华 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple` |
| 腾讯云 | `https://mirrors.cloud.tencent.com/pypi/simple` |

手动安装示例：
```bash
pip install --cache-dir ./pip_cache -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

---

## **8. 使用说明**

### **8.1 基本流程**

**嵌入水印：**
1. 启动程序，选择"水印嵌入"标签页
2. 选择原始 .docx 文档
3. 输入溯源信息（用户标识、部门、项目）
4. 选择密钥（默认密钥或自定义密钥）
5. 点击"开始嵌入水印"
6. 输出文件保存在原目录的 `watermarked` 文件夹

**分析溯源：**
1. 选择"分析溯源"标签页
2. 选择待分析的水印文档
3. 选择与嵌入时相同的密钥
4. 点击"开始分析对比"
5. 查看分析结果

### **8.2 密钥管理**

- **新建密钥**：设置名称和密码
- **导出密钥**：备份到 JSON 文件
- **导入密钥**：从备份文件恢复
- **删除密钥**：移除不再需要的密钥

### **8.3 注意事项**

1. **密钥保管**：请妥善保管密钥密码，丢失将无法解密水印
2. **传输建议**：避免通过微信/钉钉等工具传输，可能过滤零宽字符
3. **离线使用**：建议在隔离环境使用，避免在线编辑
4. **定期备份**：定期导出密钥备份文件