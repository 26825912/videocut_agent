#!/bin/bash
# 语音服务 Docker 一键启动脚本 (Linux/Mac)

echo "============================================================"
echo "语音服务 Docker 启动脚本"
echo "============================================================"

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "[错误] 未找到 docker 命令，请先安装 Docker"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "[错误] Docker 未运行，请先启动 Docker"
    exit 1
fi

echo
echo "[1/3] 切换到服务目录..."
cd "$(dirname "$0")/docker_services" || exit 1

echo "[2/3] 构建 Docker 镜像..."
docker-compose build

echo "[3/3] 启动服务..."
docker-compose up -d

echo
echo "============================================================"
echo "服务启动完成！"
echo
echo "FunASR 服务:    http://127.0.0.1:8001"
echo "GPT-SoVITS 服务: http://127.0.0.1:9880"
echo
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "============================================================"
echo
