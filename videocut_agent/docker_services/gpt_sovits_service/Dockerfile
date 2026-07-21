FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 直接从 GitHub 克隆 GPT-SoVITS 源码
RUN git clone https://github.com/RVC-Boss/GPT-SoVITS.git /app && \
    cd /app && \
    git checkout be6a4f1e9d8a22d41b7d42c22df9d7ef36f225d2

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建模型目录
RUN mkdir -p GPT_SoVITS/pretrained_models

# 复制启动脚本
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 暴露端口
EXPOSE 9880

# 使用启动脚本（首次启动会自动下载模型）
ENTRYPOINT ["/entrypoint.sh"]
