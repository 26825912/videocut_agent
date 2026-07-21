# Subtitle Agent

字幕生成智能体 - 自动化字幕生成和编辑工具

## 📝 功能概述

Subtitle Agent 是一个专业的字幕生成和编辑智能体，可以自动为视频或音频生成字幕文件，支持多种字幕格式。基于 LangChain 的 Agent 架构构建。

## 🎯 核心能力

### 1. 语音转字幕
- **音频文件转字幕**: 从音频文件(.mp3, .wav等)生成 ASS 字幕
- **视频文件转字幕**: 从视频文件提取音频并生成字幕
- **自动语音识别**: 使用 ASR 技术自动识别语音内容

### 2. 字幕编辑
- **时间轴调整**: 调整字幕的时间偏移
- **格式转换**: 支持 ASS/SRT 等字幕格式
- **字幕优化**: 自动分段、断句

### 3. 字幕处理
- **多语言支持**: 支持中文、英文等多种语言
- **时间轴对齐**: 确保字幕与音频精确同步
- **字幕样式**: 可自定义字幕样式（字体、颜色、位置）

## 🛠️ 工具列表

| 工具名称 | 功能描述 | 输入参数 |
|---------|---------|---------|
| `audio_to_subtitle` | 音频转字幕 | 音频文件路径 |
| `video_to_subtitle` | 视频转字幕 | 视频文件路径 |
| `asr_audio_file` | ASR 语音识别 | 音频文件路径、语言代码 |
| `adjust_subtitle_timing` | 调整字幕时间轴 | 字幕文件、偏移量 |

## 📖 使用示例

### 示例 1: 为视频生成字幕

```python
from subtitle_agent.agent import subtitle_editor_agent

# 为视频生成中文字幕
result = subtitle_editor_agent.invoke(
    "为 video.mp4 生成中文字幕文件"
)

print(result)
# 输出: {"success": True, "result_subtitle_path": "video.ass"}
```

### 示例 2: 为音频生成字幕

```python
result = subtitle_editor_agent.invoke(
    "将 audio.mp3 转换为 ASS 字幕文件"
)
```

### 示例 3: 多语言字幕

```python
# 生成英文字幕
result = subtitle_editor_agent.invoke(
    "为 english_video.mp4 生成英文字幕"
)

# 生成中文字幕
result = subtitle_editor_agent.invoke(
    "为 chinese_video.mp4 生成中文字幕"
)
```

## 🔧 技术架构

### LangChain Agent 架构

```
User Input → Agent → Tool Selection → Tool Execution → Response
                ↑                            ↓
                └────────────────────────────┘
```

- **Agent**: 理解用户需求，选择合适的工具
- **Tool Selection**: 根据任务类型选择字幕生成工具
- **Tool Execution**: 执行 ASR 和字幕生成
- **Response**: 返回结构化的字幕文件路径

### 系统提示词

```
你是一个专业字幕编辑助手

你的核心能力是：
- 语音文件转 ASS 字幕文件
- 视频文件转 ASS 字幕文件
```

## 🎨 工作流程

1. **接收请求**: 用户提供视频或音频文件
2. **音频提取**: 如果是视频文件，先提取音频轨道
3. **语音识别**: 使用 ASR 技术识别语音内容
4. **字幕生成**: 根据识别结果生成带时间轴的字幕
5. **格式化**: 生成标准的 ASS 或 SRT 格式字幕
6. **返回结果**: 返回字幕文件路径

## 📋 输出格式

```python
{
    "success": bool,                  # 处理是否成功
    "result_subtitle_path": str      # 生成的字幕文件路径
}
```

## ⚙️ 配置要求

### 环境依赖
- Python 3.10+
- ASR 服务（语音识别）
- FFmpeg（音频提取）

### 环境变量
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_API_BASE=https://api.openai.com/v1
```

### ASR 配置
需要配置 ASR 服务的 API endpoint 和认证信息（在 `tools/asr_tools.py` 中）

## 🚀 快速开始

```python
from subtitle_agent.agent import subtitle_editor_agent

# 生成字幕
result = subtitle_editor_agent.invoke(
    "为 my_video.mp4 生成字幕"
)

print(f"字幕文件已生成: {result['result_subtitle_path']}")
```

## 📝 注意事项

1. **文件格式**: 
   - 支持视频: MP4, AVI, MOV, MKV
   - 支持音频: MP3, WAV, M4A, AAC
   
2. **语音质量**: 
   - 清晰的语音识别效果更好
   - 背景噪音会影响识别准确率
   
3. **语言支持**:
   - 主要支持中文和英文
   - 其他语言需要配置相应的 ASR 模型

4. **字幕格式**:
   - 默认生成 ASS 格式（Advanced SubStation Alpha）
   - ASS 格式支持更丰富的样式

5. **时间同步**:
   - 自动处理时间轴对齐
   - 确保字幕与音频精确同步

## 🔗 相关工具

- `tools/asr_tools.py` - ASR 语音识别工具
- `tools/subtitle_v2_tools.py` - 字幕处理工具
- `tools/video_ops_v2.py` - 视频操作工具

## 🎯 典型应用场景

1. **视频字幕制作**: 为自制视频快速生成字幕
2. **会议记录**: 将会议录音转为文字字幕
3. **教育内容**: 为教学视频添加字幕
4. **多语言支持**: 为不同语言的视频生成对应字幕
5. **无障碍访问**: 为听障用户提供字幕支持

## 📚 更多资源

- [LangChain Agent 文档](https://python.langchain.com/docs/modules/agents/)
- [ASS 字幕格式规范](http://www.tcax.org/docs/ass-specs.htm)
- [FFmpeg 音频处理](https://trac.ffmpeg.org/wiki/AudioChannelManipulation)
