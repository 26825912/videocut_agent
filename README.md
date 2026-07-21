# 🎬 Video AI Agent System

基于 LangGraph 的智能视频制作系统，集成多个专业化 AI Agent，覆盖从脚本生成到视频合成的完整工作流。

[![GitHub](https://img.shields.io/github/license/26825912/videocut_agent)](https://github.com/26825912/videocut_agent)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 核心特性

- **🤖 7 个专业化 AI Agent**：覆盖视频制作全流程的智能代理系统
- **🎙️ 先进语音技术**：集成 GPT-SoVITS 和 FunASR，支持语音克隆和高精度识别
- **🎨 完整视频能力**：30+ 视频处理工具，支持剪辑、特效、字幕、音频等
- **💻 现代化界面**：Reflex 前端 + FastAPI 后端，流式响应和实时预览
- **🐳 容器化部署**：Docker Compose 一键部署语音服务
- **⚡ GPU 加速**：支持 NVIDIA NVENC 硬件编码加速

---

## 🤖 AI Agent 体系

### 1️⃣ VideoScript Agent - 脚本生成
智能生成视频脚本，支持原创和爆款仿写
- 基于主题和时长生成完整脚本
- 分析视频 URL 提取文案结构
- AI 文案改写和优化

### 2️⃣ VideoGen Agent - 视频生成
端到端自动化视频生成
- 脚本解析和时间轴规划
- 自动素材搜索和下载
- TTS 配音 + 字幕生成
- 视频合成和后期处理

### 3️⃣ VideoCopywrite Agent - 文案视频
生成营销和推广视频
- 三层文案结构分析（开头/主体/结尾）
- 关键词提取和时间对齐
- 图文视频自动合成

### 4️⃣ VideoCut Agent - 视频剪辑
专业视频编辑和后期处理
- 精确裁剪、拼接、格式化
- 绿幕抠像和特效处理
- 音频混合和音量标准化
- 硬字幕/软字幕添加

### 5️⃣ AudioCut Agent - 音频处理
音频编辑和语音合成
- 音频裁剪、拼接、音量调整
- 文本转语音（Fish Audio / GPT-SoVITS）
- 语音识别（Azure / FunASR）
- 音频质量分析

### 6️⃣ Subtitle Agent - 字幕处理
自动字幕生成和样式管理
- 逐词级精确时间戳
- ASS 字幕格式支持
- 多种字幕样式预设
- 自动时间轴对齐

### 7️⃣ Asset Search Agent - 素材搜索
智能搜索图片和视频素材
- Unsplash 高质量图片搜索
- Pixabay 视频素材搜索和下载
- 自动素材格式化和裁剪

---

## 🎬 核心能力

### 视频剪辑
视频裁剪、拼接、格式转换、尺寸调整、从指定位置插入片段、循环重复、绿幕抠像、图片转视频

### 音频处理
音频裁剪、拼接、音量调整、音频混合、LUFS 响度标准化、叠加语音（保留原声）

### 字幕处理
语音转字幕、视频转字幕、硬字幕/软字幕、ASS 样式支持、逐词级时间戳对齐

### 素材搜索
图片搜索（Unsplash）、视频搜索（Pixabay）、自动下载和格式化

### 语音合成（TTS）
- **Fish Audio**：云端 API，多语言支持，语音克隆，流式返回
- **GPT-SoVITS**：本地推理，零样本语音克隆，高质量合成

### 语音识别（ASR）
- **FunASR**：专为中文优化，逐词级时间戳，GPU 加速
- **Azure Speech**：100+ 语言支持，云端高精度识别
- **统一架构**：自动 fallback，支持 Whisper、WhisperX、腾讯云

---

## 📦 安装部署

### 环境要求
- Python 3.10+
- FFmpeg 7.0+
- Node.js 18+（前端需要）
- CUDA 11.8+（GPU 加速可选）

### 快速开始

#### 1. 克隆仓库
```bash
git clone https://github.com/26825912/videocut_agent.git
cd videocut_agent
```

#### 2. 安装 FFmpeg
**Windows**:
```bash
choco install ffmpeg
```

**Linux**:
```bash
sudo apt-get install ffmpeg
```

**macOS**:
```bash
brew install ffmpeg
```

#### 3. 安装 Python 依赖
```bash
# 后端依赖
cd videocut_agent
pip install -r requirements.txt

# 前端依赖
cd ../video_studio
pip install -r requirements.txt
```

#### 4. 配置环境变量
```bash
cd videocut_agent
cp .env.example .env
```

编辑 `.env` 文件，配置 API Keys：
```env
# LLM API
GEMINI_API_KEY=your-api-key
GEMINI_API_BASE=https://api.openai.com/v1

# Fish Audio TTS
TTS_API_URL=https://api.fish.audio/v1/tts
TTS_API_TOKEN=your-token

# Azure Speech
AZURE_SERVICE_REGION=eastasia
AZURE_SERVICE_KEY=your-key

# Pixabay 素材搜索
PIXABAY_API_KEY=your-key
```

---

## 🚀 启动服务

### 方式一：本地启动

**终端 1 - 启动后端**
```bash
cd videocut_agent
python server.py
```
访问 http://localhost:8000/docs 查看 API 文档

**终端 2 - 启动前端**
```bash
cd video_studio
reflex run
```
访问 http://localhost:3000 使用 Web 界面

### 方式二：Docker 部署（语音服务）

```bash
cd videocut_agent/docker_services

# 启动 FunASR 语音识别服务
docker-compose up -d funasr_service

# 启动 GPT-SoVITS 语音合成服务
docker-compose up -d gpt_sovits_service
```

**服务端口**：
- FunASR: http://localhost:8001
- GPT-SoVITS: http://localhost:9880

---

## 💻 使用示例

### 1. 通过 Web 界面使用

打开 http://localhost:3000，在聊天窗口输入：

```
帮我生成一个30秒的产品介绍视频，主题是智能手表
```

系统会自动：
1. 生成视频脚本
2. 搜索相关素材
3. 生成配音
4. 合成字幕
5. 输出最终视频

### 2. 通过 API 调用

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "剪辑视频：保留 10-30 秒，添加字幕",
        "session_id": "user123"
    },
    stream=True
)

for line in response.iter_lines():
    print(line.decode('utf-8'))
```

### 3. 使用单个 Agent

```python
from videocut_agent.videocut_agent.graph import video_cut_agent

# 视频剪辑
result = video_cut_agent.invoke({
    "messages": [{"role": "user", "content": "裁剪视频 0-10 秒"}],
    "video_path": "input.mp4"
})
```

---

## 📁 项目结构

```
videocut_agent/
├── videocut_agent/          # 后端核心
│   ├── server.py            # FastAPI 服务入口
│   ├── main_agent2.py       # 主 Agent 调度器
│   ├── agents_manager.py    # Agent 管理器
│   │
│   ├── videocut_agent/      # 视频剪辑 Agent
│   ├── audiocut_agent/      # 音频处理 Agent
│   ├── subtitle_agent/      # 字幕生成 Agent
│   ├── videoscript_agent/   # 脚本生成 Agent
│   ├── videogen_agent/      # 视频生成 Agent
│   ├── videocopywrite_agent/ # 文案视频 Agent
│   ├── assert_search_agent/ # 素材搜索 Agent
│   │
│   ├── tools/               # 核心工具库
│   │   ├── video_ops_v2.py  # 视频处理
│   │   ├── audio_ops_v2.py  # 音频处理
│   │   ├── subtitle_v2_tools.py # 字幕工具
│   │   ├── tts_tools.py     # TTS 语音合成
│   │   ├── asr_tools.py     # ASR 语音识别
│   │   └── ...
│   │
│   ├── models/              # 模型相关
│   │   ├── gpt-sovits/      # GPT-SoVITS 子模块
│   │   └── funasr/          # FunASR 模型
│   │
│   └── docker_services/     # Docker 容器化
│       ├── funasr_service/
│       └── gpt_sovits_service/
│
├── video_studio/            # Reflex 前端
│   ├── video_studio/
│   │   ├── video_studio.py  # 主应用
│   │   ├── state.py         # 状态管理
│   │   ├── api.py           # Agent API 客户端
│   │   └── components/      # UI 组件
│   └── rxconfig.py
│
├── data/                    # 数据目录
│   ├── clone_voice/         # 语音克隆音频
│   └── videoscript_json/    # 脚本缓存
│
├── .env                     # 环境变量配置
├── requirements.txt         # Python 依赖
└── README.md                # 项目文档
```

---

## 🔧 配置说明

### 语音合成配置

#### Fish Audio（推荐新手）
云端 API，零配置，开箱即用：
```env
TTS_API_URL=https://api.fish.audio/v1/tts
TTS_API_TOKEN=your-token
```

#### GPT-SoVITS（推荐专业用户）
本地推理，零样本语音克隆，支持商用（MIT 许可证）：

**快速启动**
```bash
# 1. 安装依赖
cd videocut_agent/models/gpt-sovits
pip install -r requirements.txt

# 2. 下载预训练模型（约 2.6GB）
cd ..
python download_gpt_sovits.py --required

# 3. 启动 API 服务
cd gpt-sovits
python api_v2.py -a 127.0.0.1 -p 9880
```

**在代码中使用**
```python
# 默认使用 Fish Audio
text_to_speech_tool(text="测试", voice_name="EnergeticMale1")

# 切换到本地 GPT-SoVITS
text_to_speech_tool(text="测试", voice_name="EnergeticMale1", use_local=True)
```

**硬件要求**
- 最低：6-8GB VRAM（fp16）
- 推荐：12GB+ VRAM
- 性能：RTX 4060Ti RTF=0.028

**语音克隆**
1. 准备 3-10 秒参考音频放入 `data/clone_voice/`
2. 编辑 `data/clone_voice/voice_mapping_gpt_sovits.json` 配置语音映射
3. 使用时指定 `voice_name` 即可

### 语音识别配置

#### FunASR（推荐）
专为中文优化，逐词级时间戳：
```bash
# Docker 方式（推荐）
docker-compose -f docker_services/docker-compose.yml up -d funasr_service

# 本地方式
# 会自动下载 Paraformer、FSMN-VAD、CT-Transformer 模型
```

#### Azure Speech
云端高精度识别，100+ 语言支持：
```env
AZURE_SERVICE_REGION=eastasia
AZURE_SERVICE_KEY=your-key
```

---

## 📊 性能优化

### GPU 加速
- 自动检测 NVIDIA GPU
- NVENC 硬件编码加速
- FunASR 模型 GPU 推理

### 处理优化
- 流复制模式（无损快速剪辑）
- 批量处理优化
- 智能音频混合
- LUFS 响度标准化

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](videocut_agent/LICENSE) 文件

---

## 🔗 相关资源

- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - 零样本语音克隆
- [FunASR](https://github.com/alibaba-damo-academy/FunASR) - 阿里达摩院语音识别
- [LangGraph](https://github.com/langchain-ai/langgraph) - AI Agent 框架
- [Reflex](https://reflex.dev/) - Python Web 框架

---

## 🙏 致谢

感谢以下开源项目的支持：
- GPT-SoVITS 团队
- FunASR 团队
- LangChain/LangGraph 社区
- Reflex 框架
- FFmpeg 项目
