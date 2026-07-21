FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制 GPT-SoVITS 代码和配置
COPY gpt-sovits/ /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建模型目录
RUN mkdir -p GPT_SoVITS/pretrained_models/v2Pro

# 暴露端口
EXPOSE 9880

# 启动服务
CMD ["python", "api_v2.py", "-a", "0.0.0.0", "-p", "9880", "-c", "GPT_SoVITS/configs/tts_infer.yaml"]
