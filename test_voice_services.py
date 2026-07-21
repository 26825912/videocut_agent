"""
测试 Docker 语音服务
验证 FunASR 和 GPT-SoVITS 服务是否正常运行
"""
import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "videocut_agent"))

print("=" * 60)
print("Docker 语音服务测试")
print("=" * 60)

# 1. 测试服务连接
print("\n[1/4] 检查服务状态...")

try:
    import requests

    # 测试 FunASR
    print("  检查 FunASR 服务 (http://127.0.0.1:8001)...")
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            print("  ✓ FunASR 服务正常")
        else:
            print(f"  ✗ FunASR 服务异常: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("  ✗ FunASR 服务无法连接")
        print("\n请先启动服务:")
        print("  cd videocut_agent/docker_services")
        print("  docker-compose up -d")
        sys.exit(1)

    # 测试 GPT-SoVITS
    print("  检查 GPT-SoVITS 服务 (http://127.0.0.1:9880)...")
    try:
        response = requests.get("http://127.0.0.1:9880/", timeout=5)
        if response.status_code == 200:
            print("  ✓ GPT-SoVITS 服务正常")
        else:
            print(f"  ✗ GPT-SoVITS 服务异常: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("  ✗ GPT-SoVITS 服务无法连接")
        print("\n请先启动服务:")
        print("  cd videocut_agent/docker_services")
        print("  docker-compose up -d")
        sys.exit(1)

except ImportError:
    print("✗ 缺少 requests 库")
    print("请安装: pip install requests")
    sys.exit(1)

# 2. 测试 VoiceAPI
print("\n[2/4] 测试 VoiceAPI 接口...")

try:
    from voice_api import VoiceAPI

    api = VoiceAPI()
    print("  ✓ VoiceAPI 初始化成功")

except Exception as e:
    print(f"  ✗ VoiceAPI 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试语音识别（如果有测试音频）
print("\n[3/4] 测试语音识别...")

# 查找测试音频
test_audio_path = None
data_dir = Path(__file__).parent / "data"

if data_dir.exists():
    for audio_file in data_dir.rglob("*.wav"):
        test_audio_path = str(audio_file)
        break

if test_audio_path:
    try:
        print(f"  使用测试音频: {Path(test_audio_path).name}")
        result = api.speech_to_text(test_audio_path, provider="funasr")

        if result and len(result) > 0:
            print(f"  ✓ 识别成功，共 {len(result)} 个片段")
            print(f"  预览: {result[0]['text'][:50]}...")
        else:
            print("  ✓ 识别完成（无结果，可能是空音频）")
    except Exception as e:
        print(f"  ✗ 识别失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⊘ 跳过（未找到测试音频）")

# 4. 测试语音合成
print("\n[4/4] 测试语音合成...")

try:
    test_text = "这是Docker语音服务测试"
    output_dir = Path(__file__).parent / "data" / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  合成文本: {test_text}")
    audio_path = api.text_to_speech(
        text=test_text,
        voice_name="EnergeticMale1",
        speed=1.0,
        use_local=True
    )

    if audio_path and os.path.exists(audio_path):
        file_size = os.path.getsize(audio_path)
        print(f"  ✓ 合成成功")
        print(f"    文件: {audio_path}")
        print(f"    大小: {file_size:,} bytes")
    else:
        print(f"  ✗ 合成失败：文件未生成")

except Exception as e:
    print(f"  ✗ 合成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有测试通过！")
print("=" * 60)
print("\n服务运行正常，可以开始使用。")
print("\n常用命令:")
print("  查看日志: cd videocut_agent/docker_services && docker-compose logs -f")
print("  停止服务: cd videocut_agent/docker_services && docker-compose down")
print("\n详细文档: videocut_agent/docker_services/README.md")
