@echo off
chcp 65001 >nul
echo ====================================
echo  Word 智能水印溯源系统 - 依赖安装
echo ====================================
echo.

REM 设置镜像源和缓存目录
set MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
set CACHE_DIR=%~dp0.pip_cache

echo [配置] 镜像源: %MIRROR%
echo [配置] 缓存目录: %CACHE_DIR%
echo.

REM 创建缓存目录
if not exist "%CACHE_DIR%" (
    echo [1/3] 创建缓存目录...
    mkdir "%CACHE_DIR%"
    echo [+] 缓存目录创建成功
) else (
    echo [1/3] 缓存目录已存在
)
echo.

REM 检查 Python 是否安装
echo [2/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [-] 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
python --version
echo.

REM 安装依赖
echo [3/3] 安装依赖包...
echo.
pip install --cache-dir "%CACHE_DIR%" -i %MIRROR% -r requirements.txt

if errorlevel 1 (
    echo.
    echo [-] 安装失败，请检查网络连接或尝试手动安装
    echo     手动安装命令: pip install --cache-dir .pip_cache -i %MIRROR% -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ====================================
echo  [+] 安装完成！
echo ====================================
echo.
echo 启动程序:
echo   - 双击运行 main.py
echo   - 或在命令行执行: python main.py
echo.
echo 命令行使用:
echo   python main.py embed --help
echo   python main.py analyze --help
echo.
pause
