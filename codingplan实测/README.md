# Word智能水印溯源系统

## 项目简介

这是一个专用的安全工具，用于在Word文档中嵌入不可见的溯源水印，以便在文档泄露时追溯到责任人。

### 主要特性

- **多层冗余备份**：五层备份策略确保水印在WPS/Word重写后仍然可提取
- **零宽字符嵌入**：使用零宽字符作为主要水印载体，不影响文档阅读
- **AES-256加密**：水印数据经过强加密，防止伪造和篡改
- **图形化界面**：直观易用的PySide6界面
- **CLI支持**：提供命令行接口，支持批量操作

### 版本信息

当前版本：v1.1.0

## 快速开始

### 1. 安装依赖

Windows用户：
```cmd
.\install.bat
```

Linux/macOS用户：
```bash
chmod +x install.sh
./install.sh
```

### 2. 启动程序

图形界面模式：\n```bash
python main.py
```

## 使用指南

### 水印嵌入

1. 启动程序，选择"水印嵌入"标签页
2. 选择原始 .docx 文档
3. 输入溯源信息（用户标识、部门、项目）
4. 选择密钥（默认密钥或自定义密钥）
5. 点击"开始嵌入水印"
6. 输出文件保存在原目录的 `watermarked` 文件夹

### 水印分析

1. 选择"分析溯源"标签页
2. 选择待分析的水印文档
3. 选择与嵌入时相同的密钥
4. 点击"开始分析对比"
5. 查看分析结果

### 命令行使用

嵌入水印：
```bash
python main.py embed document.docx -o output.docx -u "张三-123"
```

分析水印：
```bash
python main.py analyze watermarked.docx
```

密钥管理：
```bash
# 列出所有密钥
python main.py key list

# 创建新密钥
python main.py key create --name mykey --password mypassword

# 导出密钥
python main.py key export -o backup.json

# 导入密钥
python main.py key import -f backup.json

# 删除密钥
python main.py key delete --name mykey
```

## 技术架构

### 水印层级设计

| 层级 | 技术 | 隐蔽性 | 鲁棒性 | 用途 |
|------|------|--------|--------|------|
| 主层 | 零宽字符嵌入 | 极高 | 中等 | 主要溯源载体 |
| 备层1 | 文档属性(自定义) base64 | 低 | 高 | 零宽丢失时的备用 |
| 备层2 | [Content_Types].xml 注释 | 高 | 高 | 文档结构完整时可用 |
| 备层3 | settings.xml 注释 | 高 | 高 | WPS兼容层 |
| 备层4 | 页眉隐藏文本 | 极高 | 高 | 不可见但保留 |
| 备层5 | 独立XML备份文件 | 中 | 高 | 独立文件不易被覆盖 |

### 提取优先级

1. `docProps/custom.xml` 自定义属性
2. `[Content_Types].xml` 注释
3. `word/settings.xml` 注释
4. 页眉XML隐藏文本
5. `word/watermark_backup.xml` 独立文件
6. 全文零宽字符搜索（多数投票）
7. 全XML文件base64数据扫描

## 注意事项

1. **密钥保管**：请妥善保管密钥密码，丢失将无法解密水印
2. **传输建议**：避免通过微信/钉钉等工具传输，可能过滤零宽字符
3. **离线使用**：建议在隔离环境使用，避免在线编辑
4. **定期备份**：定期导出密钥备份文件

## 项目结构

```
word智能水印溯源系统/
├── main.py                    # 主入口文件 (GUI + CLI)
├── requirements.txt           # 依赖包
├── install.bat                # Windows 依赖安装脚本
├── install.sh                 # Linux/macOS 依赖安装脚本
├── config.json               # 配置文件
├── watermark.db             # SQLite 数据库
├── Docx 智能水印溯源系统设计.md  # 设计文档
│
├── src/
│   ├── core/                  # 核心模块
│   │   ├── watermark.py       # 水印核心类
│   │   └── crypto.py          # 加密模块
│   ├── ui/                    # UI 模块
│   │   └── main_window.py     # 主窗口
│   ├── db/                    # 数据库模块
│   │   └── models.py          # 数据模型
│   └── utils/                 # 工具模块
│       ├── logger.py          # 日志工具
│       └── config.py          # 配置管理
│
└── tests/                     # 测试模块
    ├── test_watermark.py      # 功能测试
    └── test_robustness.py     # 鲁棒性测试
```

## 许可证

本项目仅供学习和研究使用。
