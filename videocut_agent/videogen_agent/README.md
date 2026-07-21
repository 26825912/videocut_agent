# VideoGen Agent

视频生成智能体 - 全自动TikTok短视频生成工具

## 📝 功能概述

VideoGen Agent 是一个通用的 TikTok 短视频生成智能体，可以根据主题和时长要求自动生成完整的短视频。从脚本创作到最终合成，完全自动化处理，是短视频制作的一站式解决方案。

## 🎯 核心能力

### 1. 全流程自动化
- **一键生成**: 只需提供主题和时长，自动完成所有制作步骤
- **端到端**: 从文案创作到视频输出，无需人工干预
- **智能编排**: 自动协调各个制作环节的顺序和参数

### 2. 脚本生成
- **主题驱动**: 根据用户提供的主题自动创作视频脚本
- **时长控制**: 精确控制脚本对应的视频时长
- **内容优化**: 自动优化脚本结构和节奏

### 3. 语音合成
- **文字转语音**: 将脚本转换为自然流畅的语音
- **多语言支持**: 支持中文和英文（默认英文）
- **音质优化**: 高质量的TTS输出

### 4. 字幕生成
- **自动字幕**: 根据语音自动生成时间轴对齐的字幕
- **格式标准**: 生成 ASS 格式字幕文件
- **精确同步**: 字幕与语音完美同步

### 5. 素材匹配
- **智能检索**: 根据脚本内容自动提取关键词
- **场景匹配**: 搜索与内容匹配的视频和图片素材
- **时间对齐**: 素材与脚本的时间轴精确对应

### 6. 视频合成
- **自动合成**: 将素材、语音、字幕合成为完整视频
- **质量保证**: 确保输出视频的质量和流畅度
- **格式统一**: 输出标准的 MP4 格式

## 🛠️ 工具列表

| 工具名称 | 功能描述 | 处理阶段 |
|---------|---------|---------|
| `get_video_scripts` | 生成视频脚本 | 阶段1 |
| `text_to_speech_tool` | 文字转语音 | 阶段2 |
| `get_script_text_time` | 获取脚本文字时间轴 | 阶段3 |
| `audio2ass_tool` | 音频转ASS字幕 | 阶段3 |
| `video_serach_and_clip_tools` | 搜索并剪辑视频素材 | 阶段4 |
| `merge_videos` | 合并视频片段 | 阶段5 |
| `add_hardsub_with_offset` | 添加硬字幕 | 阶段5 |
| `add_audio_to_video` | 添加音频到视频 | 阶段5 |

## 📖 使用示例

### 示例 1: 生成科技主题短视频

```python
from videogen_agent.graph import generate_video_agent

# 生成30秒的AI主题短视频
result = generate_video_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "生成一个30秒的关于人工智能的短视频，使用中文"
    }]
})

print(result)
# 输出: {
#     "success": True,
#     "result_video_path": "output_video.mp4",
#     "theme": "人工智能",
#     "language": "zh",
#     "duration": "30"
# }
```

### 示例 2: 生成英文教育视频

```python
# 默认使用英文
result = generate_video_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Create a 45-second video about Python programming tips"
    }]
})
```

### 示例 3: 生成营销视频

```python
result = generate_video_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "生成一个60秒的产品介绍视频，主题是智能手表，使用中文"
    }]
})
```

### 示例 4: 生成故事类视频

```python
result = generate_video_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Create a 20-second motivational story video in English"
    }]
})
```

## 🔧 技术架构

### LangGraph 自动化流程

```
START → 需求分析 → 脚本生成 → 语音合成 → 字幕生成 → 素材搜索 → 视频合成 → END
                      ↓            ↓           ↓           ↓           ↓
                   Tool Call    Tool Call   Tool Call   Tool Call   Tool Call
```

### 完整工作流程

1. **阶段1: 脚本生成**
   - 输入: 主题、时长、语言
   - 工具: `get_video_scripts`
   - 输出: 视频脚本文件

2. **阶段2: 语音合成**
   - 输入: 脚本文本
   - 工具: `text_to_speech_tool`
   - 输出: 音频文件

3. **阶段3: 字幕生成**
   - 输入: 音频文件
   - 工具: `get_script_text_time`, `audio2ass_tool`
   - 输出: ASS字幕文件、时间轴数据

4. **阶段4: 素材搜索**
   - 输入: 脚本内容、关键词、时间轴
   - 工具: `video_serach_and_clip_tools`
   - 输出: 匹配的视频素材片段

5. **阶段5: 视频合成**
   - 输入: 素材、音频、字幕
   - 工具: `merge_videos`, `add_audio_to_video`, `add_hardsub_with_offset`
   - 输出: 最终视频文件

### 系统提示词

```
你是一个通用tiktok短视频生成助手，你可以根据主题和时间要求生成对应的短视频

注意：在没有指定语言时，默认使用英文，只能选择中文或英文

1. 根据主题和时间要求,生成对应的文案
2. 根据文案生成对应的语音
3. 根据语音生成对应的字幕
4. 根据脚本内容生成素材搜索关键词和时间轴
5. 搜索并剪辑视频素材
6. 合成最终视频
```

## 📋 输出格式

```python
{
    "success": bool,                # 视频是否成功生成
    "result_video_path": str,       # 生成的视频文件路径
    "theme": str,                   # 视频主题
    "language": str,                # 视频语言 (zh/en)
    "duration": str                 # 视频时长范围 (如 "30-35")
}
```

## ⚙️ 配置要求

### 环境依赖
- Python 3.10+
- FFmpeg (视频处理)
- LangChain + LangGraph
- TTS 服务（文字转语音）
- ASR 服务（语音识别）
- 素材搜索 API

### 环境变量
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_API_BASE=https://api.openai.com/v1
```

### 外部服务
需要配置以下服务的 API：
- TTS服务: 用于文字转语音
- 素材库API: 用于搜索视频和图片素材
- ASR服务: 用于生成字幕时间轴

## 🚀 快速开始

```python
from videogen_agent.graph import generate_video_agent

# 一键生成短视频
result = generate_video_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "生成一个关于[主题]的[时长]秒短视频，使用[语言]"
    }]
})

print(f"视频已生成: {result['result_video_path']}")
print(f"主题: {result['theme']}")
print(f"语言: {result['language']}")
print(f"时长: {result['duration']}秒")
```

## 📝 注意事项

1. **语言选择**:
   - 默认使用英文
   - 明确指定"使用中文"才会生成中文视频
   - 仅支持中文和英文

2. **时长限制**:
   - 推荐时长: 15-60秒
   - 过长的视频可能需要较长生成时间
   - 过短的视频内容可能不够完整

3. **主题要求**:
   - 主题描述越具体，生成效果越好
   - 避免过于宽泛或模糊的主题
   - 可以指定视频风格和目标受众

4. **生成时间**:
   - 完整流程需要2-5分钟
   - 取决于视频时长和素材搜索速度
   - 请耐心等待自动化流程完成

5. **素材质量**:
   - 自动搜索的素材可能不够完美
   - 建议人工审核最终视频
   - 可以多次生成选择最佳结果

6. **版权问题**:
   - 确保素材来源的合法性
   - 使用免费商用素材库
   - 标注素材来源（如需要）

## 🔗 相关工具

- `tools/video_scripts_tools.py` - 脚本生成
- `tools/tts_tools.py` - 文字转语音
- `tools/asr_tools.py` - 语音识别
- `tools/subtitle_v2_tools.py` - 字幕生成
- `tools/video_search_tools.py` - 素材搜索
- `tools/video_cut_tools.py` - 视频处理

## 🎯 典型应用场景

1. **社交媒体内容**: 快速生成 TikTok、抖音短视频
2. **营销推广**: 产品介绍、广告视频
3. **教育内容**: 知识分享、技巧讲解
4. **个人创作**: 故事、vlog、日常分享
5. **批量生产**: 批量生成多个主题的短视频

## 💡 使用技巧

### 优质提示词

**好的提示**:
```
生成一个30秒的手机摄影技巧视频，
面向初学者，展示3个实用技巧，
语言风格轻松幽默，使用中文
```

**不够好的提示**:
```
做个视频
```

### 提高生成质量

1. **明确主题**: 清楚描述视频要讲什么
2. **指定时长**: 给出具体的秒数
3. **说明风格**: 教程型、故事型、营销型等
4. **指定语言**: 明确使用中文或英文
5. **目标受众**: 说明面向哪类观众

## 🆚 与其他Agent的对比

| Agent | 功能 | 使用场景 |
|-------|------|---------|
| **VideoGen Agent** | 全自动生成原创视频 | 从零开始创作短视频 |
| VideoCopywrite Agent | 仿写爆款视频 | 基于成功案例创作 |
| VideoScript Agent | 仅生成脚本 | 只需要文案创作 |
| VideoC ut Agent | 视频剪辑编辑 | 处理已有视频素材 |

## 📚 更多资源

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [TikTok视频制作指南](https://www.tiktok.com/creators/creator-portal/)
- [短视频内容策略](https://blog.hootsuite.com/short-form-video/)
- [视频脚本创作技巧](https://www.videomarketingschool.com/script-writing/)
