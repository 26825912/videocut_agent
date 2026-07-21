# Docker 语音服务部署指南

## 概述

本项目将 FunASR (语音识别) 和 GPT-SoVITS v2Pro (语音合成) 部署为独立的 Docker 容器，通过 HTTP API 提供服务。

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                     Agent 环境                           │
│                 (videocut_agent)                         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           voice_api.py (统一接口)                 │  │
│  │              HTTP 客户端                          │  │
│  └────────────┬─────────────────┬───────────────────┘  │
└───────────────┼─────────────────┼──────────────────────┘
                │                 │
          HTTP  │                 │  HTTP
          8001  │                 │  9880
                │                 │
    ┌───────────▼─────────┐   ┌──▼──────────────────┐
    │   FunASR 容器       │   │ GPT-SoVITS 容器     │
    │   语音识别服务       │   │ 语音合成服务         │
    │   (FastAPI)         │   │ (FastAPI)           │
    └─────────────────────┘   └─────────────────────┘
```

## 前置要求

### 必需
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- docker-compose
- 至少 8GB 可用磁盘空间

### 可选（推荐）
- NVIDIA GPU + NVIDIA Docker 支持（用于 GPU 加速）
- 16GB+ RAM（用于并发请求）

## 快速开始

### 1. 确保模型已下载

```bash
# 检查 FunASR 模型
ls videocut_agent/models/funasr/

# 检查 GPT-SoVITS 模型
ls videocut_agent/models/gpt-sovits/GPT_SoVITS/pretrained_models/

# 如果模型缺失，运行下载脚本
cd videocut_agent/models
python download_gpt_sovits.py
python funasr_download.py --required
```

### 2. 启动服务

**Windows**:
```bash
videocut_agent\start_voice_services.bat
```

**Linux/Mac**:
```bash
bash videocut_agent/start_voice_services.sh
```

**手动启动**:
```bash
cd videocut_agent/docker_services
docker-compose up -d
```

### 3. 验证服务

```bash
# 检查容器状态
docker-compose ps

# 测试 FunASR 服务
curl http://127.0.0.1:8001/health

# 测试 GPT-SoVITS 服务
curl http://127.0.0.1:9880/

# 运行完整测试
python test_voice_services.py
```

### 4. 使用 API

```python
from videocut_agent.voice_api import VoiceAPI

api = VoiceAPI()

# 语音识别
result = api.speech_to_text("audio.wav")
print(result)

# 语音合成
audio_path = api.text_to_speech("你好世界", use_local=True)
print(audio_path)
```

## 目录结构

```
videocut_agent/
├── docker_services/                    # Docker 服务目录
│   ├── funasr_service/                 # FunASR 服务
│   │   ├── Dockerfile
│   │   ├── app.py                      # FastAPI 服务
│   │   └── requirements.txt
│   ├── gpt_sovits_service/             # GPT-SoVITS 服务
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── docker-compose.yml              # 服务编排
│   └── temp/                           # 临时文件（自动创建）
├── models/
│   ├── funasr/                         # FunASR 模型
│   ├── gpt-sovits/                     # GPT-SoVITS 源码和模型
│   ├── download_gpt_sovits.py
│   └── gpt_sovits_client.py
├── voice_api.py                        # 统一 API 接口
├── start_voice_services.bat            # Windows 启动脚本
├── start_voice_services.sh             # Linux 启动脚本
└── VOICE_API_GUIDE.md                  # 详细文档
```

## 服务端口

| 服务 | 端口 | 健康检查 | 主要接口 |
|------|------|----------|----------|
| FunASR | 8001 | GET /health | POST /asr |
| GPT-SoVITS | 9880 | GET / | POST /tts |

## 配置

### 环境变量

在 `docker-compose.yml` 中修改：

**FunASR**:
```yaml
environment:
  - USE_GPU=true          # 是否使用 GPU
  - LANGUAGE=zh           # 默认语言
  - FUNASR_MODEL_DIR=/models/funasr
```

**GPT-SoVITS**:
```yaml
environment:
  - USE_GPU=true          # 是否使用 GPU
  - DEVICE=cuda           # cuda 或 cpu
```

### GPU 支持

如果没有 GPU 或不需要 GPU 加速，修改 `docker-compose.yml`:

```yaml
services:
  funasr:
    environment:
      - USE_GPU=false
    # 注释掉 deploy 部分
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
```

### 端口修改

如果端口冲突，修改 `docker-compose.yml`:

```yaml
services:
  funasr:
    ports:
      - "8002:8001"  # 外部端口:内部端口
```

然后更新 `voice_api.py`:

```python
api = VoiceAPI(
    asr_api_url="http://127.0.0.1:8002",
    tts_api_url="http://127.0.0.1:9880"
)
```

## 常用命令

### 服务管理

```bash
cd videocut_agent/docker_services

# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 重建并启动
docker-compose up -d --build

# 启动特定服务
docker-compose up -d funasr
docker-compose up -d gpt-sovits
```

### 日志查看

```bash
# 查看所有日志
docker-compose logs

# 实时查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs funasr
docker-compose logs gpt-sovits

# 查看最近 100 行
docker-compose logs --tail=100
```

### 容器管理

```bash
# 查看容器状态
docker-compose ps

# 进入容器
docker-compose exec funasr bash
docker-compose exec gpt-sovits bash

# 查看容器资源使用
docker stats funasr-service gpt-sovits-service
```

## 故障排查

### 1. 容器无法启动

**检查日志**:
```bash
docker-compose logs funasr
docker-compose logs gpt-sovits
```

**常见原因**:
- 模型文件缺失
- 端口被占用
- GPU 驱动问题
- 磁盘空间不足

### 2. GPU 不可用

**检查 NVIDIA Docker**:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

如果失败，参考：https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

### 3. 服务无响应

```bash
# 重启服务
docker-compose restart

# 查看健康检查状态
docker-compose ps
```

### 4. 内存不足

减少并发或添加资源限制：

```yaml
services:
  funasr:
    deploy:
      resources:
        limits:
          memory: 4G
```

### 5. 模型加载失败

确保模型文件存在且可读：

```bash
# FunASR 模型
ls -lh videocut_agent/models/funasr/

# GPT-SoVITS 模型
ls -lh videocut_agent/models/gpt-sovits/GPT_SoVITS/pretrained_models/
```

## 性能优化

### 1. 使用 GPU

确保 `USE_GPU=true` 且 GPU 驱动正常。

### 2. 调整 batch_size

修改服务代码中的 `batch_size` 参数（默认为 1）。

### 3. 预热模型

首次请求会加载模型，可以在启动后立即发送测试请求预热。

### 4. 使用连接池

在高并发场景下使用 HTTP 连接池：

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount('http://', adapter)
```

## 与旧版本的差异

### 旧版本（Conda 环境）
- ASR: 直接在 agent 环境中调用
- TTS: 在 gpt-sovits conda 环境中运行
- 依赖冲突，无法共存

### 新版本（Docker）
- ASR: 独立 Docker 容器，HTTP 调用
- TTS: 独立 Docker 容器，HTTP 调用
- 完全隔离，无依赖冲突
- 易于部署和扩展

## 迁移指南

如果你之前使用 Conda 环境部署：

1. **停止旧服务**
   ```bash
   # 停止 GPT-SoVITS 服务（如果在运行）
   # Ctrl+C 或关闭终端
   ```

2. **启动 Docker 服务**
   ```bash
   bash videocut_agent/start_voice_services.sh
   ```

3. **更新代码**（已完成）
   - `voice_api.py` 已更新为调用 Docker 服务
   - 无需修改使用代码

4. **验证功能**
   ```bash
   python test_voice_services.py
   ```

## 生产部署建议

1. **使用反向代理**（如 Nginx）进行负载均衡
2. **配置日志轮转**避免日志文件过大
3. **设置资源限制**防止单个容器占用过多资源
4. **监控服务健康**使用 Prometheus + Grafana
5. **定期备份模型**防止数据丢失
6. **使用 Docker Swarm 或 Kubernetes**进行容器编排

## 参考文档

- [VOICE_API_GUIDE.md](./VOICE_API_GUIDE.md) - 详细 API 文档
- [FunASR GitHub](https://github.com/alibaba-damo-academy/FunASR)
- [GPT-SoVITS GitHub](https://github.com/RVC-Boss/GPT-SoVITS)
- [Docker 文档](https://docs.docker.com/)

## 技术支持

如遇问题：
1. 查看日志: `docker-compose logs -f`
2. 检查健康状态: `docker-compose ps`
3. 查看本文档的"故障排查"章节
4. 提交 Issue 到项目仓库
