# GPT-SoVITS 快速启动 (v2Pro版本)

## 一键部署

```bash
# 1. 安装依赖
cd videocut_agent/models/gpt-sovits && pip install -r requirements.txt

# 2. 下载v2Pro模型
cd .. && python download_gpt_sovits.py --required

# 3. 启动服务（自动使用v2Pro）
cd gpt-sovits && python api_v2.py -a 127.0.0.1 -p 9880
```

## 验证部署

```bash
# 检查模型状态
python download_gpt_sovits.py --list

# 测试API服务
curl http://127.0.0.1:9880/
```

## 使用本地TTS

在任何TTS工具调用中添加 `use_local=True`:

```python
text_to_speech_tool(text="测试", voice_name="EnergeticMale1", use_local=True)
```

详细文档见: [GPT_SOVITS_DEPLOYMENT.md](GPT_SOVITS_DEPLOYMENT.md)
