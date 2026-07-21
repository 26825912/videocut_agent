@echo off
REM GPT-SoVITS 一键启动脚本 (Windows)

echo ============================================================
echo GPT-SoVITS 独立环境启动脚本
echo ============================================================

REM 检查conda是否可用
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到conda命令，请先安装Anaconda或Miniconda
    pause
    exit /b 1
)

REM 检查gpt-sovits环境是否存在
conda env list | findstr /C:"gpt-sovits" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [提示] gpt-sovits环境不存在，正在创建...
    call conda create -n gpt-sovits python=3.10 -y
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] 创建环境失败
        pause
        exit /b 1
    )
    echo [成功] 环境创建完成
)

echo.
echo [1/3] 激活gpt-sovits环境...
call conda activate gpt-sovits
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 激活环境失败
    pause
    exit /b 1
)

echo [2/3] 检查依赖安装...
cd videocut_agent\models\gpt-sovits
python -c "import pytorch_lightning" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [提示] 依赖未安装，开始安装（约5-10分钟）...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
) else (
    echo [已跳过] 依赖已安装
)

echo [3/3] 启动GPT-SoVITS服务...
echo.
echo ============================================================
echo 服务启动中... (监听 http://127.0.0.1:9880)
echo 按 Ctrl+C 停止服务
echo ============================================================
echo.

python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
