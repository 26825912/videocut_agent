# 语音处理统一接口文档

## 概述

`voice_api.py` 提供语音识别(ASR)和语音合成(TTS)的统一调用接口。

## 架构说明

```
┌─────────────────────────────────────┐
│         VoiceAPI (统一接口)          │
├─────────────────┬───────────────────┤
│  ASR (语音识别)  │  TTS (语音合成)    │
│  Docker 容器     │  Docker 容器       │
│  HTTP 调用       │  HTTP 调用         │
│  端口 8001       │  端口 9880         │
└─────────────────┴───────────────────┘
```

**关键**: ASR 和 TTS 运行在独立的 Docker 容器中，通过 HTTP 通信，完全隔离依赖环境。

## 快速开始

### 0. 启动 Docker 服务

**一键启动（推荐）**:
```bash
# Windows
videocut_agent\start_voice_services.bat

# Linux/Mac
bash videocut_agent/start_voice_services.sh
```

**手动启动**:
```bash
cd videocut_agent/docker_services
docker-compose up -d
```

**检查服务状态**:
```bash
# 查看所有服务
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 1. 语音识别 (ASR)

```python
from videocut_agent.voice_api import VoiceAPI

api = VoiceAPI()

# 语音转文字
result = api.speech_to_text(
    audio_file="audio.wav",
    provider="funasr",  # 可选: azure, whisperx
    language="zh"       # zh, en, ja, ko
)

# 输出结果
for segment in result:
    print(f"[{segment['start_time']:.2f}s] {segment['text']}")
```

**输出格式**:
```python
[
    {
        "text": "识别的文本",
        "start_time": 0.0,
        "end_time": 2.5,
        "duration": 2.5
    },
    ...
]
```

### 2. 语音合成 (TTS)

```python
from videocut_agent.voice_api import VoiceAPI

api = VoiceAPI()

# 文字转语音
audio_path = api.text_to_speech(
    text="你好，这是语音合成测试",
    voice_name="EnergeticMale1",  # 可选: EnergeticMale2, 小辉
    speed=1.0,                     # 0.5-2.0
    use_local=True                 # 使用本地GPT-SoVITS
)

print(f"音频文件: {audio_path}")
```

## 便捷函数

```python
from videocut_agent.voice_api import asr, tts

# 语音识别
result = asr("audio.wav")

# 语音合成
audio_path = tts("你好世界", voice="EnergeticMale1", speed=1.2)
```

## API参考

### VoiceAPI类

#### `__init__(asr_api_url="http://127.0.0.1:8001", tts_api_url="http://127.0.0.1:9880")`

初始化语音处理API

**参数**:
- `asr_api_url`: FunASR 服务地址
- `tts_api_url`: GPT-SoVITS 服务地址

#### `speech_to_text(audio_file, provider="funasr", language="zh")`

语音转文字

**参数**:
- `audio_file`: 音频文件路径
- `provider`: ASR提供商 (funasr, azure, whisperx)
- `language`: 语言代码

**返回**: 识别结果列表

#### `text_to_speech(text, voice_name, speed, volume, output_file, use_local)`

文字转语音

**参数**:
- `text`: 要合成的文本
- `voice_name`: 语音名称 (默认: EnergeticMale1)
- `speed`: 语速 (默认: 1.0)
- `volume`: 音量 (默认: 0.0)
- `output_file`: 输出路径 (可选)
- `use_local`: 使用本地GPT-SoVITS (推荐: True)

**返回**: 音频文件路径

#### `get_available_voices()`

获取可用语音列表

**返回**: 语音名称列表

## Docker 部署

### 服务端口

- **FunASR**: `http://127.0.0.1:8001`
  - 健康检查: `GET /health`
  - 识别接口: `POST /asr`

- **GPT-SoVITS**: `http://127.0.0.1:9880`
  - 健康检查: `GET /`
  - 合成接口: `POST /tts`

### 环境变量

**FunASR 服务**:
- `USE_GPU`: 是否使用 GPU (默认: true)
- `LANGUAGE`: 默认语言 (默认: zh)
- `FUNASR_MODEL_DIR`: 模型目录路径

**GPT-SoVITS 服务**:
- `USE_GPU`: 是否使用 GPU (默认: true)
- `DEVICE`: 设备类型 (默认: cuda)

### 目录挂载

**FunASR**:
- 模型: `videocut_agent/models/funasr` → `/models/funasr`
- 临时文件: `videocut_agent/docker_services/temp/funasr` → `/tmp`

**GPT-SoVITS**:
- 模型权重: `videocut_agent/models/gpt-sovits/GPT_SoVITS/pretrained_models` → `/app/GPT_SoVITS/pretrained_models`
- 配置文件: `videocut_agent/models/gpt-sovits/GPT_SoVITS/configs` → `/app/GPT_SoVITS/configs`
- 参考音频: `data/clone_voice` → `/app/data/clone_voice`

### GPU 支持

两个服务都配置了 NVIDIA GPU 支持。如果不需要 GPU，修改 `docker-compose.yml`:

```yaml
environment:
  - USE_GPU=false
  - DEVICE=cpu

# 注释掉 deploy 部分
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
```

## 故障排查

### Docker 服务未运行

**错误信息**:
```
无法连接到 FunASR 服务！
请确保 Docker 服务已启动
```

**解决**:
```bash
cd videocut_agent/docker_services
docker-compose up -d
```

### 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看 FunASR 日志
docker-compose logs funasr

# 查看 GPT-SoVITS 日志
docker-compose logs gpt-sovits

# 实时查看所有日志
docker-compose logs -f
```

### 服务无响应

```bash
# 重启服务
docker-compose restart

# 完全重建
docker-compose down
docker-compose up -d --build
```

### GPU 不可用

如果 GPU 不可用，修改 `docker-compose.yml` 禁用 GPU：

```yaml
environment:
  - USE_GPU=false
```

### 端口冲突

如果端口被占用，修改 `docker-compose.yml`:

```yaml
ports:
  - "8002:8001"  # FunASR
  - "9881:9880"  # GPT-SoVITS
```

然后更新 `voice_api.py` 中的 URL。

## 完整示例

```python
from videocut_agent.voice_api import VoiceAPI

# 初始化API
api = VoiceAPI()

# 1. 语音识别
print("语音识别...")
asr_result = api.speech_to_text("input.wav", provider="funasr")
for segment in asr_result:
    print(f"  {segment['text']}")

# 2. 语音合成
print("\n语音合成...")
text = "这是合成的语音"
audio_path = api.text_to_speech(text, voice_name="EnergeticMale1")
print(f"  输出: {audio_path}")

# 3. 获取可用语音
voices = api.get_available_voices()
print(f"\n可用语音: {voices}")
```

## 性能优化

### 首次启动优化

首次启动可能需要下载模型，建议：

1. 提前下载模型到本地
2. 使用 `docker-compose build` 预构建镜像
3. 设置合理的健康检查时间

### 并发处理

两个服务都支持并发请求，但注意：

- GPU 显存限制并发数
- 适当调整 batch_size
- 使用连接池管理 HTTP 请求

## 注意事项

1. **Docker 依赖**: 必须安装 Docker 和 docker-compose
2. **GPU 驱动**: 使用 GPU 需要安装 NVIDIA Docker 支持
3. **模型文件**: 确保模型已下载到正确位置
4. **端口可用**: 确保 8001 和 9880 端口未被占用
5. **网络隔离**: 两个服务通过 Docker 网络通信
