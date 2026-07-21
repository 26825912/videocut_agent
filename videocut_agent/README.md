# Video AI Agent System

基于 LangGraph 的多智能体视频制作系统

## ✨ 特性

- **7个专业化智能体**: 覆盖视频制作全流程
- **完整视频制作流程**: 从脚本生成到最终合成
- **Streamlit可视化界面**: 直观的用户交互
- **FastAPI后端服务**: RESTful API支持

## 🤖 智能体介绍

### 1. VideoCut Agent - 视频剪辑
负责视频的剪辑、裁剪、转格式等操作

### 2. Subtitle Agent - 字幕生成
自动生成字幕文件，支持时间轴对齐

### 3. AudioCut Agent - 音频处理
处理音频剪辑、TTS语音合成、ASR识别

### 4. VideoScript Agent - 脚本生成
智能生成视频脚本，支持原创和爆款仿写

### 5. Asset Search Agent - 素材搜索
搜索和管理视频、图片素材

### 6. VideoGen Agent - 视频生成
根据脚本和素材生成完整视频

### 7. VideoCopywrite Agent - 文案视频
生成带文案的营销视频

## 📦 安装

### 环境要求

- Python 3.10+
- FFmpeg (用于视频处理)
- CUDA (可选，用于GPU加速)

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/yourusername/videocut_agent_system.git
cd videocut_agent_system

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写你的 API keys
```

### 安装 FFmpeg

**Windows**:
```bash
# 使用 chocolatey
choco install ffmpeg

# 或从官网下载: https://ffmpeg.org/download.html
```

**Linux**:
```bash
sudo apt-get install ffmpeg
```

**macOS**:
```bash
brew install ffmpeg
```

## 🚀 快速开始

### 1. 启动 Streamlit UI

```bash
streamlit run app.py
```

访问 http://localhost:8501 使用图形界面

### 2. 启动 API 服务

```bash
python server.py
```

API 服务将在 http://localhost:8000 启动

访问 http://localhost:8000/docs 查看 API 文档

### 3. 使用单个智能体

```python
from videocut_agent.core.agents import video_cut_agent

result = video_cut_agent.invoke({
    "messages": [{"role": "user", "content": "剪辑视频从10秒到30秒"}]
})
```

## 📖 使用示例

### 完整视频制作流程

```python
# 1. 生成脚本
script = videoscript_agent.invoke("生成一个30秒的产品介绍视频脚本")

# 2. 生成音频
audio = audiocut_agent.invoke(f"将以下脚本转为语音: {script}")

# 3. 生成字幕
subtitles = subtitle_agent.invoke(f"为音频生成字幕: {audio}")

# 4. 搜索素材
assets = assert_search_agent.invoke("搜索产品相关的图片和视频素材")

# 5. 合成视频
video = generate_video_agent.invoke({
    "audio": audio,
    "subtitles": subtitles,
    "assets": assets
})
```

### 单点任务

```python
# 仅剪辑视频
result = video_cut_agent.invoke("将 input.mp4 剪辑为 0:10-0:30")

# 仅生成字幕
result = subtitle_agent.invoke("为 video.mp4 生成中文字幕")

# 仅音频处理
result = audiocut_agent.invoke("将文本转为语音并降噪")
```

## 🏗️ 架构

### 智能体架构

```
AgentManager (智能体管理器)
├── VideoCut Agent
├── Subtitle Agent
├── AudioCut Agent
├── VideoScript Agent
├── Asset Search Agent
├── VideoGen Agent
└── VideoCopywrite Agent
```

### 工作流程

参见 [workflow.md](workflow.md) 查看完整的 Mermaid 流程图

### 工具系统

每个智能体都有自己的工具管理器(ToolManager)，负责管理该智能体可用的工具集。

## 🔧 配置

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `GEMINI_API_KEY` | LLM API密钥 | ✅ |
| `GEMINI_API_BASE` | LLM API地址 | ✅ |
| `IMAGE_SEARCH_API_KEY` | 图片搜索API | ❌ |
| `VIDEO_SEARCH_API_KEY` | 视频搜索API | ❌ |

### 模型配置

默认使用 `gemini-2.5-pro` 模型，可在代码中修改：

```python
model = ChatOpenAI(
    model="gpt-4",  # 修改模型
    openai_api_key=GEMINI_API_KEY,
    openai_api_base=GEMINI_API_BASE
)
```

## 📚 文档

- [API 文档](docs/API.md) - API 接口说明
- [工作流程](workflow.md) - 详细工作流程图
- [开发指南](docs/DEVELOPMENT.md) - 开发和贡献指南
- [常见问题](docs/FAQ.md) - 常见问题解答

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 运行单个智能体测试
python -m tests.test_videocut_agent
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

请参考 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献指南。

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 智能体编排
- [Streamlit](https://streamlit.io/) - 前端框架
- [FFmpeg](https://ffmpeg.org/) - 视频处理

## ⚠️ 注意事项

1. **API 费用**: 使用 LLM API 会产生费用，请注意控制调用次数
2. **视频处理**: 视频处理需要较大内存和计算资源
3. **外部服务**: 部分功能依赖外部服务(图片搜索、视频搜索等)

## 📞 支持

- 问题反馈: [GitHub Issues](https://github.com/yourusername/videocut_agent_system/issues)
- 讨论: [GitHub Discussions](https://github.com/yourusername/videocut_agent_system/discussions)
