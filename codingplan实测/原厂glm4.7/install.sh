#!/bin/bash
# Word 智能水印溯源系统 - 依赖安装脚本 (Linux/macOS)

set -e

echo "===================================="
echo " Word 智能水印溯源系统 - 依赖安装"
echo "===================================="
echo ""

# 设置镜像源和缓存目录
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/.pip_cache"

echo "[配置] 镜像源: $MIRROR"
echo "[配置] 缓存目录: $CACHE_DIR"
echo ""

# 创建缓存目录
if [ ! -d "$CACHE_DIR" ]; then
    echo "[1/3] 创建缓存目录..."
    mkdir -p "$CACHE_DIR"
    echo "[+] 缓存目录创建成功"
else
    echo "[1/3] 缓存目录已存在"
fi
echo ""

# 检查 Python
echo "[2/3] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "[-] 错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi
python3 --version
echo ""

# 安装依赖
echo "[3/3] 安装依赖包..."
echo ""
pip3 install --cache-dir "$CACHE_DIR" -i "$MIRROR" -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[-] 安装失败，请检查网络连接或尝试手动安装"
    echo "    手动安装命令: pip3 install --cache-dir .pip_cache -i $MIRROR -r requirements.txt"
    exit 1
fi

echo ""
echo "===================================="
echo " [+] 安装完成！"
echo "===================================="
echo ""
echo "启动程序:"
echo "  python3 main.py"
echo ""
echo "命令行使用:"
echo "  python3 main.py embed --help"
echo "  python3 main.py analyze --help"
echo ""
