# Word智能水印溯源系统 - 安装约束

本项目使用国内镜像源和本地缓存目录安装依赖，确保网络稳定性和可复现性。

## 安装要求

- **镜像源**：必须使用国内镜像（清华 https://pypi.tuna.tsinghua.edu.cn/simple）
- **缓存目录**：pip 缓存必须存放在程序所在目录的 `.pip_cache` 下
- **安装方式**：使用项目提供的 `install.bat`（Windows）或 `install.sh`（Linux/macOS）脚本

## 手动安装（如需要）

如需手动指定安装，请使用以下命令：

```bash
pip install --cache-dir ./.pip_cache -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 常用国内镜像源

| 镜像 | 地址 |
|------|------|
| 清华 | https://pypi.tuna.tsinghua.edu.cn/simple |
| 阿里云 | https://mirrors.aliyun.com/pypi/simple |
| 腾讯云 | https://mirrors.cloud.tencent.com/pypi/simple |