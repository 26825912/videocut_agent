FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制服务代码
COPY app.py .

# 暴露端口
EXPOSE 8001

# 启动服务
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
