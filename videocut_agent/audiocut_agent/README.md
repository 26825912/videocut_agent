# AudioCut Agent

音频处理智能体 - 专业的音频编辑和语音合成工具

## 📝 功能概述

AudioCut Agent 是一个专业的音频处理智能体，提供音频剪辑、合并、音量调整、TTS语音合成、ASR语音识别等功能。基于 LangGraph 构建，可以智能完成各种音频处理任务。

## 🎯 核心能力

### 1. 音频剪辑
- **音频片段裁剪**: 按时间范围裁剪音频
- **精确剪辑**: 支持毫秒级精度
- **格式保留**: 保持原始音频格式和质量

### 2. 音频合并
- **多音频合并**: 将多个音频文件顺序合并
- **无缝拼接**: 自动处理音频之间的过渡
- **格式兼容**: 支持不同格式音频的合并

### 3. 音量调整
- **音量放大/缩小**: 调整音频音量倍数
- **音量标准化**: 统一音频音量水平
- **防失真**: 自动避免音量过大导致的失真

### 4. 文字转语音 (TTS)
- **文本转语音**: 将文本转换为自然语音
- **多音色支持**: 支持不同的声音风格
- **语速调节**: 可调整语音速度
- **多语言支持**: 支持中文、英文等多种语言

### 5. 语音识别 (ASR)
- **音频转文字**: 自动识别音频中的语音内容
- **高准确率**: 基于先进的 ASR 模型
- **实时识别**: 快速处理音频文件

## 🛠️ 工具列表

| 工具名称 | 功能描述 | 输入参数 |
|---------|---------|---------|
| `clip_audio` | 裁剪音频片段 | 音频路径、开始时间、结束时间 |
| `concate_audios` | 合并多个音频 | 音频路径列表、输出路径 |
| `adjust_audio_volume` | 调整音量 | 音频路径、音量倍数 |
| `text_to_speech_tool` | 文字转语音 | 文本内容、语言、音色 |
| `asr_audio_file` | 语音识别 | 音频路径、语言代码 |

## 📖 使用示例

### 示例 1: 裁剪音频

```python
from audiocut_agent.graph import audio_cut_agent

# 裁剪音频从5秒到15秒
result = audio_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "将 audio.mp3 裁剪为 5秒到15秒的片段"
    }]
})
```

### 示例 2: 合并音频

```python
result = audio_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "将 audio1.mp3, audio2.mp3, audio3.mp3 合并成一个音频文件"
    }]
})
```

### 示例 3: 调整音量

```python
result = audio_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "将 audio.mp3 的音量提高到原来的1.5倍"
    }]
})
```

### 示例 4: 文字转语音

```python
result = audio_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "将以下文本转为语音：'欢迎使用音频处理智能体'"
    }]
})
```

### 示例 5: 语音识别

```python
result = audio_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "识别 speech.mp3 中的语音内容"
    }]
})
```

## 🔧 技术架构

### LangGraph 状态图

```
START → LLM Call → Tool Node → Should Continue? → END
              ↑          ↓           ↓
              └──────────┘          END
```

- **LLM Call**: 根据用户需求选择工具
- **Tool Node**: 执行音频处理工具
- **Should Continue**: 判断是否需要继续处理

### 系统提示词

```
你是一个专业的音频编辑助手，专门处理音频剪辑、合并、TTS、ASR等任务。

你可以处理以下类型的任务：
- 音频裁剪：裁剪音频片段
- 音频合并：将多个音频文件合并
- 音量调整：调整音频音量
- TTS：文字转语音
- ASR：语音识别
```

## 🎨 工作流程

1. **接收用户请求**: 理解音频处理需求
2. **任务分析**: 识别所需的音频处理操作
3. **工具选择**: 选择合适的音频工具
4. **执行处理**: 调用底层音频处理库
5. **质量检查**: 验证处理结果
6. **返回结果**: 返回处理后的音频文件路径

## 📋 输出格式

```python
{
    "success": bool,              # 任务是否成功
    "result_audio_path": str,     # 生成的音频文件路径
    "duration": float            # 音频时长（秒）
}
```

## ⚙️ 配置要求

### 环境依赖
- Python 3.10+
- FFmpeg
- pydub
- TTS 服务（用于文字转语音）
- ASR 服务（用于语音识别）

### 环境变量
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_API_BASE=https://api.openai.com/v1

# TTS 服务配置
TTS_API_URL=your-tts-service-url
TTS_API_KEY=your-tts-api-key

# ASR 服务配置
ASR_API_URL=your-asr-service-url
ASR_API_KEY=your-asr-api-key
```

## 🚀 快速开始

```python
from audiocut_agent.graph import audio_cut_agent

# 使用智能体处理音频
result = audio_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "你的音频处理需求"
    }]
})
```

## 📝 注意事项

1. **文件格式**:
   - 支持: MP3, WAV, M4A, AAC, OGG, FLAC
   - 推荐使用 MP3 或 WAV 格式

2. **音频质量**:
   - 保持原始音频的采样率和比特率
   - 避免多次重复压缩导致质量损失

3. **TTS 限制**:
   - 单次文本长度限制（通常 500-1000 字）
   - 注意 API 调用频率限制

4. **ASR 准确率**:
   - 清晰的录音效果更好
   - 背景噪音影响识别准确率
   - 建议使用降噪处理

5. **性能考虑**:
   - 大音频文件处理需要时间
   - TTS 和 ASR 依赖外部服务响应速度

## 🔗 相关工具

- `tools/audiocut_tools.py` - 音频剪辑工具
- `tools/tts_tools.py` - TTS 文字转语音
- `tools/asr_tools.py` - ASR 语音识别
- `tools/audio_ops_v2.py` - 音频操作底层实现

## 🎯 典型应用场景

1. **播客制作**: 音频剪辑、合并、音量调整
2. **有声书制作**: 将文本转为语音
3. **会议记录**: 语音转文字
4. **音频清理**: 裁剪静音、调整音量
5. **多语言配音**: TTS 生成不同语言的语音

## 📚 更多资源

- [FFmpeg 音频处理文档](https://trac.ffmpeg.org/wiki/AudioChannelManipulation)
- [pydub 文档](https://github.com/jiaaro/pydub)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
