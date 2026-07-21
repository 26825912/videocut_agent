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

## 🚀 快速开始

### 环境要求
- Python 3.10+
- FFmpeg 7.0+
- Node.js 18+（前端需要）
- CUDA 11.8+（GPU 加速可选）

### 1. 克隆并安装

```bash
# 克隆仓库
git clone https://github.com/26825912/videocut_agent.git
cd videocut_agent

# （可选）如需本地语音服务，初始化 submodule
# 注意：GPT-SoVITS 和 FunASR 源码仅在本地推理时需要
# 如果只使用云端 API（Fish Audio / Azure），可跳过此步骤
git submodule update --init --recursive

# 安装 FFmpeg
# Windows: choco install ffmpeg
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg

# 安装后端依赖
cd videocut_agent
pip install -r requirements.txt

# 安装前端依赖
cd ../video_studio
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cd videocut_agent
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM API
GEMINI_API_KEY=your-api-key
GEMINI_API_BASE=https://api.openai.com/v1

# 语音合成（选择一种）
TTS_API_URL=https://api.fish.audio/v1/tts
TTS_API_TOKEN=your-token

# 语音识别（选择一种）
AZURE_SERVICE_REGION=eastasia
AZURE_SERVICE_KEY=your-key

# 素材搜索
UNSPLASH_ACCESS_KEYS=your-unsplash-key
PIXABAY_API_KEY=your-pixabay-key

# 脚本生成与文案仿写（Dify 工作流 - 可选配置）
# 注意：以下功能暂未开放，如需使用请联系获取 API 访问权限
SCRIPTS_API_KEY=your-scripts-key              # 脚本生成 API Key
SCRIPTS_BASE_URL=https://difyzzc.zuzuche.com/v1/workflows/run

DIFY_API_KEY=your-dify-key                    # 爆款文案拆解 API Key
COPYWRITE_BASE_URL=https://difyzzc.zuzuche.com/v1/workflows/run

AI_COPYWRITE_API_KEY=your-copywrite-key       # AI 文案改写 API Key
AI_COPYWRITE_API_BASE_URL=https://difyzzc.zuzuche.com/v1/workflows/run
```

### 3. 启动服务

**终端 1 - 后端**
```bash
cd videocut_agent
python server.py
# 访问 http://localhost:8000/docs 查看 API 文档
```

**终端 2 - 前端**
```bash
cd video_studio
reflex run
# 访问 http://localhost:3000 使用 Web 界面
```

---

## 💻 使用示例

### Web 界面
打开 http://localhost:3000，输入：
```
帮我生成一个30秒的产品介绍视频，主题是智能手表
```

系统会自动完成：脚本生成 → 素材搜索 → 配音生成 → 字幕合成 → 视频输出

### API 调用
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

### 单个 Agent 调用
```python
from videocut_agent.videocut_agent.graph import video_cut_agent

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
│   ├── models/              # 模型相关
│   └── docker_services/     # Docker 容器化
│
├── video_studio/            # Reflex 前端
├── data/                    # 数据目录
├── .env                     # 环境变量配置
└── README.md
```

---

## ⚙️ 高级配置

### Docker 部署语音服务

**✅ 一键部署语音服务**

无需初始化 submodule 或下载模型，Docker 会自动处理所有依赖：

```bash
cd videocut_agent/docker_services

# 一键启动所有语音服务
docker-compose up -d

# 或单独启动服务
docker-compose up -d funasr        # 语音识别（端口 8001）
docker-compose up -d gpt-sovits    # 语音合成（端口 9880）
```

**服务说明**：
- **FunASR**（端口 8001）：首次启动会自动从 ModelScope 下载中文语音识别模型
- **GPT-SoVITS**（端口 9880）：自动从 GitHub 克隆源码，首次启动需下载预训练模型（~2.6GB）

**访问地址**：
- FunASR API: `http://localhost:8001/docs`
- GPT-SoVITS API: `http://localhost:9880/`

**前置条件**：
- Docker 和 Docker Compose
- NVIDIA GPU 和 Docker GPU 支持（nvidia-docker2）

### GPT-SoVITS 本地推理

支持零样本语音克隆（MIT 许可证，商用友好）

```bash
# 1. 安装依赖
cd videocut_agent/models/gpt-sovits
pip install -r requirements.txt

# 2. 下载预训练模型（约 2.6GB）
cd ..
python download_gpt_sovits.py --required

# 3. 启动服务
cd gpt-sovits
python api_v2.py -a 127.0.0.1 -p 9880
```

**语音克隆**：
1. 准备 3-10 秒参考音频放入 `data/clone_voice/`
2. 编辑 `data/clone_voice/voice_mapping_gpt_sovits.json`
3. 在代码中使用 `use_local=True` 切换到本地推理

**硬件要求**：
- 最低：6-8GB VRAM（fp16）
- 推荐：12GB+ VRAM
- 性能：RTX 4060Ti RTF=0.028

### 性能优化

- **GPU 加速**：自动检测 NVIDIA GPU，支持 NVENC 硬件编码
- **流复制模式**：无损快速剪辑
- **音频标准化**：LUFS 响度标准化（-14 LUFS）
- **批量处理**：智能音频混合和批量优化

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
