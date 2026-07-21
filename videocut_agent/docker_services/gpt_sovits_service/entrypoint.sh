#!/bin/bash
set -e

MODEL_DIR="/app/GPT_SoVITS/pretrained_models"
MODEL_MARKER="$MODEL_DIR/.downloaded"

echo "🚀 启动 GPT-SoVITS 服务..."

# 检查模型是否已下载
if [ ! -f "$MODEL_MARKER" ]; then
    echo "📦 首次启动，正在下载预训练模型（约 2.6GB）..."
    echo "⏳ 这可能需要几分钟，请耐心等待..."

    # 下载模型文件
    mkdir -p "$MODEL_DIR"
    cd "$MODEL_DIR"

    # 从 HuggingFace 下载 GPT-SoVITS 预训练模型
    echo "下载 s2G488k.pth..."
    wget -q --show-progress https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/pretrained_models/s2G488k.pth

    echo "下载 s2D488k.pth..."
    wget -q --show-progress https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/pretrained_models/s2D488k.pth

    echo "下载 s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt..."
    wget -q --show-progress https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/pretrained_models/s1bert25hz-2kh-longer-epoch%3D68e-step%3D50232.ckpt

    # 下载中文 BERT 模型
    mkdir -p chinese-roberta-wwm-ext-large
    cd chinese-roberta-wwm-ext-large
    echo "下载 BERT 模型文件..."
    wget -q https://huggingface.co/hfl/chinese-roberta-wwm-ext-large/resolve/main/config.json
    wget -q https://huggingface.co/hfl/chinese-roberta-wwm-ext-large/resolve/main/pytorch_model.bin
    wget -q https://huggingface.co/hfl/chinese-roberta-wwm-ext-large/resolve/main/tokenizer.json

    cd "$MODEL_DIR"
    # 标记模型已下载
    touch "$MODEL_MARKER"
    echo "✅ 模型下载完成"
else
    echo "✅ 检测到已有模型文件，跳过下载"
fi

echo "🎙️ 启动 GPT-SoVITS API 服务..."
cd /app
exec python api_v2.py -a 0.0.0.0 -p 9880
