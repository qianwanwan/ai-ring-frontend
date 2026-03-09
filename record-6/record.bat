@echo off
setlocal
:: 获取当前文件夹路径
set "ROOT_DIR=%~dp0"
:: 设置 Python 路径（指向你的绿色环境）
set "PYTHON_EXE=%ROOT_DIR%python_env\python\python.exe"

:: 启动程序，无需激活环境，直接调用
"%PYTHON_EXE%" "%ROOT_DIR%record.py"
pause