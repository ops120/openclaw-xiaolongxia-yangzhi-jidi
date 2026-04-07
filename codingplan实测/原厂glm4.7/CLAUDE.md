# Word 智能水印溯源系统 - 项目说明

## 安装规范

本项目依赖包必须使用国内镜像源安装，pip 缓存必须存放在程序所在目录的 `.pip_cache` 下。

### 快速安装

**Windows:**
```cmd
.\install.bat
```

**Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

### 手动安装

如需手动安装，请使用以下命令：

```bash
pip install --cache-dir ./pip_cache -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 常用镜像源

| 镜像 | 地址 |
|------|------|
| 清华 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple` |
| 腾讯云 | `https://mirrors.cloud.tencent.com/pypi/simple` |

## 项目概述

本项目实现了一个完整的 Word 文档水印溯源系统，主要功能包括：

- **水印嵌入**: 在 Word 文档中嵌入隐蔽的零宽字符水印
- **五层冗余备份**: 防止 WPS/Word 重写导致水印丢失
- **分析溯源**: 从文档中提取水印信息，定位泄密源头
- **密钥管理**: 支持密钥创建、导入、导出、删除
- **图形界面**: 基于 PySide6 的直观界面

## 版本信息

- **当前版本**: 1.1.0
- **更新日期**: 2026-04-03
- **主要更新**: 五层冗余备份策略，解决 WPS/Word 重写导致水印丢失问题
