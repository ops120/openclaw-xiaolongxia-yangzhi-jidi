#!/bin/bash

echo "Installing Word Watermark Tracing System..."
echo

# 创建缓存目录
mkdir -p .pip_cache

# 使用清华镜像源安装依赖
echo "Installing dependencies using Tsinghua mirror..."
pip install --cache-dir .pip_cache -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "Installation completed successfully!"
    echo "========================================"
    echo
    echo "Run the application:"
    echo "  python main.py"
else
    echo
    echo "========================================"
    echo "Installation failed. Please check the error message above."
    echo "========================================"
    exit 1
fi
