#!/bin/bash
# Word 智能水印溯源系统 - 依赖安装脚本 (Linux/macOS)

echo "========================================"
echo "Word 智能水印溯源系统 - 依赖安装脚本"
echo "========================================"
echo

# 设置镜像源和本地缓存目录
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/.pip_cache"

# 创建缓存目录
mkdir -p "$CACHE_DIR"

echo "[1/3] 正在设置 pip 配置..."
pip config set global.index-url "$MIRROR"
pip config set global.cache-dir "$CACHE_DIR"
echo

echo "[2/3] 正在安装依赖包..."
pip install --cache-dir "$CACHE_DIR" -i "$MIRROR" -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "[错误] 依赖安装失败，请检查网络连接或手动安装。"
    exit 1
fi
echo

echo "[3/3] 验证安装..."
python3 -c "import PySide6; import docx; import cryptography; import lxml; print('所有依赖安装成功！')"

if [ $? -ne 0 ]; then
    echo "[警告] 部分依赖可能未正确安装"
else
    echo
    echo "========================================"
    echo "安装完成！运行 python main.py 启动程序"
    echo "========================================"
fi
echo
