# Assert Search Agent

素材搜索智能体 - 视频和图片素材智能检索工具

## 📝 功能概述

Assert Search Agent 是一个专业的素材搜索智能体，负责为视频制作提供图片和视频素材。可以根据关键词、场景描述智能搜索并筛选合适的素材资源。

## 🎯 核心能力

### 1. 图片素材搜索
- **关键词搜索**: 根据关键词搜索高质量图片
- **场景匹配**: 根据场景描述找到匹配的图片
- **批量搜索**: 支持多个关键词批量检索
- **智能筛选**: 自动过滤低质量和不相关图片

### 2. 视频素材搜索
- **视频检索**: 搜索相关的视频素材
- **自动剪辑**: 搜索并自动剪辑视频片段
- **场景匹配**: 根据需求找到合适的视频场景
- **时长控制**: 可指定所需视频片段的时长

### 3. 素材管理
- **结果排序**: 按相关度、质量排序
- **格式兼容**: 支持多种图片和视频格式
- **去重处理**: 自动去除重复素材
- **本地缓存**: 缓存搜索结果提高效率

## 🛠️ 工具列表

| 工具名称 | 功能描述 | 输入参数 |
|---------|---------|---------|
| `img_search_tool_v2` | 搜索图片素材 | 关键词、数量、语言 |
| `video_serach_and_clip_tools` | 搜索并剪辑视频 | 关键词、时长、场景描述 |

## 📖 使用示例

### 示例 1: 搜索图片素材

```python
from assert_search_agent.graph import assert_search_agent

# 搜索科技主题图片
result = assert_search_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "搜索10张关于人工智能和机器人的高清图片"
    }]
})

print(result)
# 输出: {"images": ["url1", "url2", ...], "count": 10}
```

### 示例 2: 搜索视频素材

```python
# 搜索并剪辑视频片段
result = assert_search_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "搜索城市夜景的视频素材，需要15秒的片段"
    }]
})
```

### 示例 3: 批量素材搜索

```python
# 为脚本搜索配套素材
result = assert_search_agent.invoke({
    "messages": [{
        "role": "user",
        "content": """
        为以下脚本搜索素材：
        1. 开场：科技感的电路板 (5秒视频)
        2. 中间：AI机器人工作 (3张图片)
        3. 结尾：未来城市 (10秒视频)
        """
    }]
})
```

### 示例 4: 场景化搜索

```python
result = assert_search_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "搜索适合产品介绍视频的背景图片，要求简洁、专业、科技感"
    }]
})
```

## 🔧 技术架构

### LangGraph 状态图

```
START → LLM Call → Tool Selection → Search & Filter → END
              ↑           ↓              ↓
              └───────────┴──────────────┘
```

- **LLM Call**: 理解搜索需求，提取关键信息
- **Tool Selection**: 选择图片或视频搜索工具
- **Search & Filter**: 执行搜索并筛选结果
- **Quality Check**: 验证素材质量和相关性

### 系统提示词

智能体理解以下类型的搜索需求：
- 关键词搜索：直接的关键词列表
- 场景描述：描述性的场景要求
- 主题搜索：基于主题找相关素材
- 组合搜索：多个条件的组合查询

## 🎨 工作流程

1. **需求理解**: 分析用户的素材需求
2. **关键词提取**: 提取搜索关键词和约束条件
3. **工具选择**: 判断需要图片还是视频素材
4. **执行搜索**: 调用搜索API获取结果
5. **结果筛选**: 根据质量和相关性筛选
6. **格式化返回**: 返回素材URL和元信息

## 📋 输出格式

### 图片搜索结果
```python
{
    "images": [
        {
            "url": "https://...",
            "thumbnail": "https://...",
            "title": "...",
            "source": "..."
        }
    ],
    "count": int,
    "query": str
}
```

### 视频搜索结果
```python
{
    "videos": [
        {
            "url": "https://...",
            "thumbnail": "https://...",
            "duration": float,
            "clip_start": float,
            "clip_end": float
        }
    ],
    "count": int,
    "query": str
}
```

## ⚙️ 配置要求

### 环境依赖
- Python 3.10+
- LangChain
- 图片搜索API（Unsplash, Pexels等）
- 视频搜索API（Pexels Video等）

### 环境变量
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_API_BASE=https://api.openai.com/v1

# 素材搜索API配置
IMAGE_SEARCH_API_KEY=your-image-api-key
VIDEO_SEARCH_API_KEY=your-video-api-key
```

### API配置
需要在 `tools/image_search_tools.py` 和 `tools/video_search_tools.py` 中配置：
- API endpoint
- API key
- 搜索参数（数量、质量、授权类型）

## 🚀 快速开始

```python
from assert_search_agent.graph import assert_search_agent

# 搜索素材
result = assert_search_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "搜索太空主题的图片和视频素材"
    }]
})
```

## 📝 注意事项

1. **版权问题**:
   - 优先使用免费商用素材库
   - 检查素材的使用许可
   - 标注素材来源（如需要）
   - 避免使用有版权争议的素材

2. **素材质量**:
   - 图片：推荐 1920x1080 或更高分辨率
   - 视频：推荐 1080p 或 4K
   - 确保素材清晰度和色彩

3. **搜索效率**:
   - 使用具体的关键词而非泛泛描述
   - 批量搜索时注意API限流
   - 缓存常用素材减少重复搜索

4. **素材相关性**:
   - AI搜索结果可能不够精准
   - 建议人工审核筛选
   - 可以多次搜索获取更多选择

5. **文件管理**:
   - 自动下载的素材需要整理
   - 注意存储空间占用
   - 定期清理临时文件

## 🔗 相关工具

- `tools/image_search_tools.py` - 图片搜索工具
- `tools/video_search_tools.py` - 视频搜索工具
- `tools/videocut_methods.py` - 视频剪辑方法

## 🎯 典型应用场景

1. **短视频制作**: 为短视频找配图和B-roll素材
2. **营销内容**: 搜索产品相关的场景素材
3. **教程视频**: 找示例图片和演示视频
4. **内容创作**: 快速获取主题相关素材
5. **社交媒体**: 为帖子找吸引眼球的图片

## 💡 搜索技巧

### 有效的搜索关键词

**好的关键词**:
- 具体: "macbook pro on desk" 而非 "computer"
- 场景化: "business meeting in modern office"
- 多词组合: "sunset, ocean, peaceful"

**避免的关键词**:
- 过于泛泛: "good", "nice", "beautiful"
- 中英混合: 最好统一使用英文关键词
- 品牌名称: 可能违反版权

### 提高搜索精度

1. **明确需求**: 清楚描述场景、风格、色调
2. **指定数量**: 说明需要多少张/个素材
3. **提供上下文**: 说明素材用于什么场景
4. **风格要求**: 指定照片风格、视频类型

## 📊 推荐素材来源

### 免费图片库
- Unsplash: 高质量免费图片
- Pexels: 图片和视频
- Pixabay: 多语言支持

### 免费视频库
- Pexels Videos: 高质量视频素材
- Pixabay Videos: 多种类型视频
- Videvo: 4K视频素材

## 📚 更多资源

- [Unsplash API 文档](https://unsplash.com/documentation)
- [Pexels API 文档](https://www.pexels.com/api/documentation/)
- [视频素材使用指南](https://www.videvo.net/blog/guide-to-stock-footage/)
