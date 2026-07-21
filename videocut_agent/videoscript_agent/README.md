# VideoScript Agent

视频脚本生成智能体 - AI驱动的视频文案创作工具

## 📝 功能概述

VideoScript Agent 是一个专业的视频脚本创作智能体，可以根据主题自动生成视频文案、分析爆款视频、仿写热门内容。基于 LangChain Agent 架构，结合大语言模型的创作能力。

## 🎯 核心能力

### 1. 视频文案生成
- **主题生成**: 根据给定主题和时长生成原创视频文案
- **多场景支持**: 支持教程、营销、介绍、故事等多种视频类型
- **时长控制**: 精确控制文案对应的视频时长

### 2. 爆款视频拆解
- **视频分析**: 深度分析爆款视频的内容结构
- **脚本提取**: 从视频中提取核心文案内容
- **创作要点**: 总结视频的成功要素

### 3. 爆款视频仿写
- **内容仿写**: 基于爆款视频风格创作新文案
- **主题迁移**: 将成功模式应用到新主题
- **风格保持**: 保持原视频的叙事风格和节奏

### 4. 多语言支持
- **中英文创作**: 默认支持中英文脚本生成
- **语言切换**: 根据需求自动调整输出语言
- **本地化**: 适应不同语言的表达习惯

## 🛠️ 工具列表

| 工具名称 | 功能描述 | 输入参数 |
|---------|---------|---------|
| `generate_video_script` | 生成视频脚本 | 主题、时长、语言 |
| `analyze_viral_video` | 分析爆款视频 | 视频链接或文件 |
| `rewrite_script` | 仿写脚本 | 参考视频、新主题、时长 |

## 📖 使用示例

### 示例 1: 生成产品介绍脚本

```python
from videoscript_agent.agent import videoscript_agent

# 生成30秒产品介绍脚本
result = videoscript_agent.invoke(
    "生成一个30秒的AI工具产品介绍视频脚本"
)

print(result)
# 输出: {"success": True, "result_script": "...", "language": "zh"}
```

### 示例 2: 生成教程脚本

```python
result = videoscript_agent.invoke(
    "为Python编程新手创作一个60秒的教程视频脚本，主题是列表操作"
)
```

### 示例 3: 分析爆款视频

```python
result = videoscript_agent.invoke(
    "分析这个爆款视频的脚本结构: https://www.youtube.com/watch?v=xxxxx"
)
```

### 示例 4: 仿写爆款视频

```python
result = videoscript_agent.invoke(
    "参考这个视频 https://www.youtube.com/watch?v=xxxxx 的风格，"
    "创作一个关于健康饮食的45秒视频脚本"
)
```

### 示例 5: 英文脚本生成

```python
result = videoscript_agent.invoke(
    "Generate a 30-second script about artificial intelligence in English"
)
```

## 🔧 技术架构

### LangChain Agent 架构

```
User Request → Agent → Tool Selection → LLM Generation → Response
                 ↑                           ↓
                 └───────────────────────────┘
```

- **Agent**: 理解创作需求，选择合适的工具
- **Tool Selection**: 选择生成、分析或仿写工具
- **LLM Generation**: 使用大语言模型生成内容
- **Response**: 返回结构化的脚本内容

### 系统提示词

```
你是一个专业的视频文案创作助手。

你的核心能力包括：
- 视频文案生成：根据主题和时间范围，调用工具生成视频文案
- 爆款视频的拆解：调用工具拆解视频文案
- 爆款视频文案的仿写：输入视频链接，仿写主题和时间可以仿写一个新的文案

注意，在没有指定语言的情况下默认使用英文
```

## 🎨 工作流程

1. **接收创作需求**: 理解用户的主题、时长、风格要求
2. **需求分析**: 判断是原创、分析还是仿写任务
3. **内容生成**: 
   - 原创：直接调用 LLM 生成脚本
   - 分析：提取视频内容并分析结构
   - 仿写：学习参考视频风格后创作
4. **内容优化**: 调整时长、优化表达、检查逻辑
5. **格式化输出**: 返回结构化的脚本内容

## 📋 输出格式

```python
{
    "success": bool,           # 是否成功生成
    "result_script": str,      # 生成的视频文案内容
    "language": str           # 文案语言 (zh/en)
}
```

## ⚙️ 配置要求

### 环境依赖
- Python 3.10+
- LangChain
- OpenAI/Gemini API

### 环境变量
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_API_BASE=https://api.openai.com/v1
```

### 模型配置
默认使用 `gemini-2.5-pro` 模型，可以根据需要调整：
- 创意内容：使用较高的 temperature (0.7-1.0)
- 技术内容：使用较低的 temperature (0.3-0.5)

## 🚀 快速开始

```python
from videoscript_agent.agent import videoscript_agent

# 生成视频脚本
result = videoscript_agent.invoke(
    "生成一个关于环保主题的60秒视频脚本"
)

print(f"脚本内容:\n{result['result_script']}")
print(f"语言: {result['language']}")
```

## 📝 注意事项

1. **时长控制**:
   - 一般语速: 每分钟约 150-180 字（中文）
   - 快速语速: 每分钟约 200-240 字
   - 预留画面停顿时间

2. **语言选择**:
   - 默认使用英文（按照系统提示）
   - 明确指定语言可获得更好效果
   - 建议在提示词中明确语言需求

3. **创作质量**:
   - 提供详细的主题描述可获得更好结果
   - 指定目标受众有助于调整语言风格
   - 明确视频类型（教程/营销/故事等）

4. **爆款分析**:
   - 需要提供有效的视频链接或文件
   - 分析结果可能需要人工审核
   - 仿写时注意版权问题

5. **内容审核**:
   - AI生成内容需要人工审核
   - 确保内容符合平台规范
   - 检查事实准确性

## 🔗 相关工具

- `tools/video_scripts_tools.py` - 视频脚本生成工具
- `tools/dify_workflower/` - Dify工作流集成

## 🎯 典型应用场景

1. **短视频创作**: 快速生成TikTok、抖音等平台的短视频文案
2. **营销内容**: 创作产品介绍、广告脚本
3. **教育内容**: 生成教程、讲解类视频脚本
4. **故事内容**: 创作故事类、剧情类视频
5. **热点追踪**: 快速仿写热门视频内容

## 💡 创作技巧

### 优质提示词示例

**好的提示**:
```
生成一个60秒的手机摄影技巧视频脚本，
面向初学者，语言风格轻松幽默，
包含3个实用技巧，使用中文
```

**不够好的提示**:
```
写个视频脚本
```

### 结构化创作

建议在脚本中包含：
- **开场（前5秒）**: 抓住注意力的钩子
- **主体内容**: 清晰的信息传递
- **结尾（最后5秒）**: 行动号召或总结

## 📚 更多资源

- [LangChain Agent 文档](https://python.langchain.com/docs/modules/agents/)
- [视频脚本创作指南](https://www.videomarketingschool.com/script-writing/)
- [短视频内容策略](https://blog.hootsuite.com/short-form-video/)
