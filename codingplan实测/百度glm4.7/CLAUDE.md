# Word 智能水印溯源系统 - 项目约束

## 安装规范

### 必须遵守的约束

1. **镜像源**: 必须使用国内镜像（推荐清华源）
   - 清华: `https://pypi.tuna.tsinghua.edu.cn/simple`
   - 阿里云: `https://mirrors.aliyun.com/pypi/simple`
   - 腾讯云: `https://mirrors.cloud.tencent.com/pypi/simple`

2. **缓存目录**: pip 缓存必须存放在项目目录的 `.pip_cache` 下

3. **安装方式**: 使用项目提供的安装脚本
   - Windows: `.\install.bat`
   - Linux/macOS: `./install.sh`

### 手动安装命令

```bash
pip install --cache-dir ./pip_cache -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 项目结构

```
word智能水印溯源系统/
├── main.py                    # 主入口
├── requirements.txt           # 依赖包
├── install.bat / install.sh   # 安装脚本
├── config.json               # 配置文件
├── watermark.db             # SQLite 数据库
├── src/                      # 源码目录
│   ├── core/                # 核心模块
│   ├── ui/                  # UI 模块
│   ├── db/                  # 数据库模块
│   └── utils/               # 工具模块
└── tests/                    # 测试模块
```

## 运行程序

```bash
python main.py
```

## 功能说明

1. **水印嵌入**: 在 Word 文档中嵌入隐蔽的溯源水印
2. **分析溯源**: 从文档中提取水印，追溯泄密源头
3. **密钥管理**: 支持多密钥、导入导出功能
4. **五层备份**: 防止 WPS/Word 重写导致水印丢失
