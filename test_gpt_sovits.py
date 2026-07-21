"""
测试GPT-SoVITS语音合成功能
"""
import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "videocut_agent"))
sys.path.insert(0, str(Path(__file__).parent / "videocut_agent" / "models"))

print("=" * 60)
print("GPT-SoVITS 语音合成测试")
print("=" * 60)

# 1. 测试服务连接
print("\n[1/3] 检查GPT-SoVITS服务状态...")
try:
    from gpt_sovits_client import GPTSoVITSClient

    client = GPTSoVITSClient()
    if client.check_service():
        print("✓ GPT-SoVITS服务正常运行 (http://127.0.0.1:9880)")
    else:
        print("✗ GPT-SoVITS服务未运行")
        print("\n请先启动服务:")
        print("cd videocut_agent/models/gpt-sovits")
        print("python api_v2.py -a 127.0.0.1 -p 9880")
        sys.exit(1)
except Exception as e:
    print(f"✗ 连接失败: {e}")
    sys.exit(1)

# 2. 测试推理客户端
print("\n[2/3] 测试推理客户端...")
try:
    from gpt_sovits_client import GPTSoVITSAdapter

    adapter = GPTSoVITSAdapter()
    available_voices = adapter.get_available_voices()
    print(f"✓ 可用语音: {available_voices}")

except Exception as e:
    print(f"✗ 客户端初始化失败: {e}")
    sys.exit(1)

# 3. 测试语音合成
print("\n[3/3] 测试语音合成...")
try:
    # 使用第一个可用语音测试
    test_voice = available_voices[0] if available_voices else "EnergeticMale1"
    test_text = "你好，这是GPT-SoVITS语音合成测试。"

    output_dir = Path(__file__).parent / "data" / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "test_gpt_sovits.wav"

    print(f"使用语音: {test_voice}")
    print(f"测试文本: {test_text}")
    print(f"输出文件: {output_file}")

    # 调用合成
    audio_data = adapter.text_to_speech_simple(
        text=test_text,
        voice_name=test_voice,
        speed=1.0,
        output_path=str(output_file)
    )

    if output_file.exists():
        file_size = output_file.stat().st_size
        print(f"✓ 语音合成成功!")
        print(f"  - 文件大小: {file_size:,} bytes")
        print(f"  - 保存位置: {output_file}")
    else:
        print("✗ 音频文件未生成")
        sys.exit(1)

except Exception as e:
    print(f"✗ 语音合成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有测试通过!")
print("=" * 60)
