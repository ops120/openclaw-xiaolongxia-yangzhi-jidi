@echo off
chcp 65001 >nul
echo ========================================
echo Word 智能水印溯源系统 - 依赖安装脚本
echo ========================================
echo.

:: 设置镜像源和本地缓存目录
set MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
set CACHE_DIR=%~dp0.pip_cache

:: 创建缓存目录
if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"

echo [1/3] 正在设置 pip 配置...
pip config set global.index-url %MIRROR%
pip config set global.cache-dir "%CACHE_DIR%"
echo.

echo [2/3] 正在安装依赖包...
pip install --cache-dir "%CACHE_DIR%" -i %MIRROR% -r requirements.txt
if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败，请检查网络连接或手动安装。
    pause
    exit /b 1
)
echo.

echo [3/3] 验证安装...
python -c "import PySide6; import docx; import cryptography; import lxml; print('所有依赖安装成功！')"
if errorlevel 1 (
    echo [警告] 部分依赖可能未正确安装
) else (
    echo.
    echo ========================================
    echo 安装完成！运行 python main.py 启动程序
    echo ========================================
)
echo.
pause
