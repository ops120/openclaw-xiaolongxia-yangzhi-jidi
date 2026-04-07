@echo off
echo Installing dependencies with Chinese mirror...
pip install --cache-dir .\.pip_cache -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
echo.
echo Installation complete!
pause