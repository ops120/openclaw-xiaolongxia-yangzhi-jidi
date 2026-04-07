@echo off
echo Installing Word Watermark Tracing System...
echo.

:: 创建缓存目录
if not exist ".pip_cache" mkdir .pip_cache

:: 使用清华镜像源安装依赖
echo Installing dependencies using Tsinghua mirror...
pip install --cache-dir .pip_cache -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Installation completed successfully!
    echo ========================================
    echo.
    echo Run the application:
    echo   python main.py
) else (
    echo.
    echo ========================================
    echo Installation failed. Please check the error message above.
    echo ========================================
)

pause
