@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM ===== 小K万能工作台 · Windows 一键启动 =====
REM 首次运行会自动安装依赖（需要联网一次）；之后离线也能跑。
REM 启动后不要关闭弹出的黑色窗口，关了服务就停。

set PORT=3000

REM 1) 检测 Python（优先 py，其次 python / python3）
set PY=
where py >nul 2>nul && set PY=py
if not defined PY (where python >nul 2>nul && set PY=python)
if not defined PY (where python3 >nul 2>nul && set PY=python3)

if not defined PY (
    echo.
    echo [错误] 没检测到 Python。请先安装：https://www.python.org/downloads/
    echo 安装时务必勾选 "Add Python to PATH"（添加到环境变量）。
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

echo 使用 %PY% 安装依赖（首次需联网，约十几秒）...
%PY% -m pip install -r requirements.txt -q

echo.
echo 正在启动小K万能工作台...
echo 浏览器将自动打开 http://localhost:3000
echo （若没自动打开，请手动在浏览器输入该地址）
echo.

REM 2) 后台启动服务（独立窗口），再打开浏览器
start "" %PY% app.py
timeout /t 4 >nul
start http://localhost:3000

echo 启动完成。需要时直接关掉那个黑色窗口即可停止。
echo 数据都保存在本文件夹的 data\app.db，换电脑把整个文件夹拷走即可。
pause
