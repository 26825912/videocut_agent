# GPT-SoVITS 集成总结

## 已完成的工作

### 1. 部署GPT-SoVITS仓库
- 位置: `videocut_agent/models/gpt-sovits/`
- 来源: https://github.com/RVC-Boss/GPT-SoVITS (MIT许可证，支持商用)

### 2. 创建推理客户端
- 文件: `videocut_agent/models/gpt_sovits_client.py`
- 功能:
  - `GPTSoVITSClient`: 原生客户端
  - `GPTSoVITSAdapter`: Fish Audio API兼容适配器

### 3. 修改TTS工具 (支持本地推理)

所有TTS工具已添加 `use_local` 参数:

| 文件路径 | 修改内容 |
|---------|---------|
| `videocut_agent/tools/tts_tools.py` | 添加本地推理支持 |
| `videocopywrite_agent/tools/tts_tools.py` | 添加本地推理支持 |
| `videogen_agent/tools/tts_tools.py` | 添加本地推理支持 |
| `audiocut_agent/tools/tts_tools.py` | 添加本地推理支持 |

### 4. 配置文件
- `data/clone_voice/voice_mapping_gpt_sovits.json` - 语音映射配置

### 5. 模型下载脚本
- `videocut_agent/models/download_gpt_sovits.py` - 自动下载预训练模型

### 6. 文档
- `videocut_agent/models/GPT_SOVITS_DEPLOYMENT.md` - 完整部署指南
- `videocut_agent/models/README_GPT_SOVITS.md` - 快速启动指南

## 使用方法

### 快速启动

```bash
# 1. 安装依赖
cd videocut_agent/models/gpt-sovits
pip install -r requirements.txt

# 2. 下载必需模型 (~2.6GB)
cd ..
python download_gpt_sovits.py --required

# 3. 启动GPT-SoVITS服务
cd gpt-sovits
python api_v2.py -a 127.0.0.1 -p 9880
```

### 在代码中使用

```python
# 使用Fish Audio API (默认)
text_to_speech_tool(
    text="测试文本",
    voice_name="EnergeticMale1",
    use_local=False  # 默认
)

# 使用本地GPT-SoVITS
text_to_speech_tool(
    text="测试文本",
    voice_name="EnergeticMale1",
    use_local=True  # 启用本地推理
)
```

## 显存要求

- **最低**: 6-8GB VRAM (fp16)
- **推荐**: 12GB+ VRAM
- **性能**: RTX 4060Ti RTF=0.028

## 受影响的子agent

✅ **videocut_agent** - 使用公共tools目录  
✅ **videocopywrite_agent** - 已集成本地推理  
✅ **videogen_agent** - 已集成本地推理  
✅ **audiocut_agent** - 已集成本地推理

## 下一步操作

1. **准备参考音频**: 将语音克隆用的参考音频放入 `data/clone_voice/` 目录
2. **配置语音映射**: 编辑 `voice_mapping_gpt_sovits.json` 添加你的语音配置
3. **下载模型**: 运行 `python download_gpt_sovits.py --required`
4. **启动服务**: 运行 `python api_v2.py` 启动GPT-SoVITS API服务
5. **测试**: 调用TTS工具时设置 `use_local=True`

## 商用说明

GPT-SoVITS使用MIT许可证，完全支持商业使用，无需额外授权。

## 文件清单

```
videocut_agent/
├── models/
│   ├── gpt-sovits/                    # GPT-SoVITS仓库
│   ├── gpt_sovits_client.py           # 推理客户端
│   ├── download_gpt_sovits.py         # 模型下载脚本
│   ├── GPT_SOVITS_DEPLOYMENT.md       # 部署文档
│   └── README_GPT_SOVITS.md           # 快速指南
├── tools/tts_tools.py                 # ✓ 已修改
├── videocopywrite_agent/
│   └── tools/tts_tools.py             # ✓ 已修改
├── videogen_agent/
│   └── tools/tts_tools.py             # ✓ 已修改
└── audiocut_agent/
    └── tools/tts_tools.py             # ✓ 已修改

data/
└── clone_voice/
    └── voice_mapping_gpt_sovits.json  # 语音配置
```
