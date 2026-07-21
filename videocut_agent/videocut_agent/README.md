# VideoCut Agent

视频剪辑智能体 - 专业的视频编辑和处理工具

## 📝 功能概述

VideoCut Agent 是一个专业的视频编辑智能体，负责处理各种视频剪辑、合并、调整、格式转换等任务。基于 LangGraph 构建，可以智能理解用户的视频处理需求并自动选择合适的工具完成任务。

## 🎯 核心能力

### 1. 视频裁剪
- 裁剪视频片段（按时间范围）
- 调整视频时长
- 精确到帧的剪辑

### 2. 视频合并
- 将多个视频文件合并为一个
- 支持不同格式视频的合并
- 自动处理分辨率和编码差异

### 3. 视频调整
- 调整视频音量（增加/减少）
- 调整视频尺寸和分辨率
- 视频格式转换（MP4, AVI, MOV等）

### 4. 背景处理
- 去除绿幕背景
- 填充视频背景
- 背景替换

### 5. 音频处理
- 为视频添加背景音乐
- 为视频添加音效
- 音频混合

### 6. 字幕处理
- 为视频添加硬字幕（烧录字幕）
- 字幕时间轴偏移调整
- 支持 ASS/SRT 格式

### 7. 其他功能
- 图片转视频
- 视频插入到指定时间点
- 视频格式转换

## 🛠️ 工具列表

| 工具名称 | 功能描述 | 输入参数 |
|---------|---------|---------|
| `clip_video` | 裁剪视频片段 | 视频路径、开始时间、结束时间 |
| `merge_videos` | 合并多个视频 | 视频路径列表、输出路径 |
| `resize_and_cut_video` | 调整尺寸并裁剪 | 视频路径、目标尺寸、裁剪参数 |
| `adjust_video_volume` | 调整视频音量 | 视频路径、音量倍数 |
| `insert_video_at_time` | 在指定时间插入视频 | 主视频、插入视频、时间点 |
| `format_video` | 转换视频格式 | 视频路径、目标格式 |
| `image_to_video` | 图片转视频 | 图片路径、时长、FPS |
| `remove_green_screen` | 去除绿幕 | 视频路径、色键参数 |
| `fill_video` | 填充视频背景 | 视频路径、填充色 |
| `add_audio_to_video` | 添加音频 | 视频路径、音频路径 |
| `add_hardsub_with_offset` | 添加硬字幕 | 视频路径、字幕文件、偏移量 |

## 📖 使用示例

### 示例 1: 裁剪视频片段

```python
from videocut_agent.graph import video_cut_agent

# 裁剪视频从10秒到30秒
result = video_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "将 input.mp4 裁剪为 10秒到30秒的片段"
    }]
})

print(result)
# 输出: {"success": True, "result_video_path": "output.mp4", ...}
```

### 示例 2: 合并多个视频

```python
result = video_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "将 video1.mp4, video2.mp4, video3.mp4 合并成一个视频"
    }]
})
```

### 示例 3: 调整音量

```python
result = video_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "将 input.mp4 的音量提高到原来的2倍"
    }]
})
```

### 示例 4: 添加字幕

```python
result = video_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "为 video.mp4 添加字幕文件 subtitles.ass"
    }]
})
```

### 示例 5: 去除绿幕

```python
result = video_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "去除 greenscreen_video.mp4 的绿色背景"
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

- **LLM Call**: 智能体根据用户需求决定调用哪个工具
- **Tool Node**: 执行具体的视频处理工具
- **Should Continue**: 判断是否需要继续调用其他工具

### 系统提示词

智能体具有以下系统提示：

```
你是一个专业的视频编辑助手，专门处理视频剪辑、合并、调整、格式转换等任务。

你可以处理以下类型的任务：
- 视频裁剪：裁剪视频片段、调整视频时长
- 视频合并：将多个视频文件合并为一个
- 视频调整：调整视频音量、尺寸、格式
- 背景处理：去除绿幕、填充背景
- 音频添加：为视频添加背景音乐或音效
- 字幕添加：为视频添加硬字幕
- 调整视频音量：增加或减少视频音量
```

## 🎨 工作流程

1. **接收用户请求**: 用户描述需要完成的视频处理任务
2. **任务理解**: LLM 分析用户需求，识别所需的工具
3. **工具选择**: 从工具库中选择合适的工具
4. **工具执行**: 调用底层视频处理工具（基于 FFmpeg）
5. **结果验证**: 检查处理结果是否符合要求
6. **返回结果**: 返回处理后的视频路径和状态

## 📋 输出格式

```python
{
    "success": bool,              # 任务是否成功
    "result_video_path": str,     # 生成的视频文件路径
    "origin_video_path": str      # 原始视频文件路径
}
```

## ⚙️ 配置要求

### 环境依赖
- Python 3.10+
- FFmpeg (必须安装)
- OpenCV
- MoviePy
- LangChain

### 环境变量
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_API_BASE=https://api.openai.com/v1
```

## 🚀 快速开始

```python
from videocut_agent.graph import video_cut_agent

# 使用智能体
result = video_cut_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "你的视频处理需求"
    }]
})
```

## 📝 注意事项

1. **文件路径**: 确保提供正确的文件路径（绝对路径或相对路径）
2. **格式支持**: 支持常见视频格式（MP4, AVI, MOV, MKV等）
3. **性能考虑**: 大视频文件处理可能需要较长时间
4. **临时文件**: 工具会创建临时文件，处理完成后会自动清理
5. **FFmpeg**: 必须预先安装 FFmpeg 命令行工具

## 🔗 相关工具

- `tools/video_cut_tools.py` - 视频处理工具实现
- `tools/videocut_methods.py` - 视频剪辑方法
- `tools/video_ops_v2.py` - 视频操作底层实现

## 📚 更多资源

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [FFmpeg 文档](https://ffmpeg.org/documentation.html)
- [MoviePy 文档](https://zulko.github.io/moviepy/)
