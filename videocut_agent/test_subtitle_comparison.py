"""
对比测试Azure和FunASR两种字幕生成接口
使用项目中的示例音频文件进行实际测试
"""

import sys
import os
from pathlib import Path

# 添加必要路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "subtitle_agent"))
sys.path.append(str(current_dir / "audiocut_agent"))
sys.path.append(str(current_dir / "tools"))

def test_azure_subtitle():
    """测试Azure字幕生成接口"""
    print("=== Azure 字幕生成测试 ===")

    try:
        # 导入Azure字幕工具
        from subtitle_agent.tools.subtitle_v2_tools import audio2ass_tool

        # 使用示例音频
        audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"

        print(f"测试音频: {audio_path}")
        print("调用Azure接口...")

        result = audio2ass_tool(audio_path, "中文")

        print("Azure接口调用成功！")
        print("返回结果:")
        if isinstance(result, dict) and "tool_return" in result:
            for item in result["tool_return"]:
                print(f"  字幕文件: {item.get('ass_file', 'N/A')}")
                print(f"  描述: {item.get('describe', 'N/A')}")
        else:
            print(f"  原始返回: {result}")

        return result

    except Exception as e:
        print(f"Azure接口测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def test_funasr_subtitle():
    """测试FunASR字幕生成接口"""
    print("\n=== FunASR 字幕生成测试 ===")

    try:
        # 导入FunASR字幕工具
        from subtitle_agent.tools.funasr_subtitle_tools import funasr_audio2ass_tool

        # 使用相同的示例音频
        audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"

        print(f"测试音频: {audio_path}")
        print("调用FunASR接口...")

        result = funasr_audio2ass_tool(audio_path, "中文")

        print("FunASR接口调用成功！")
        print("返回结果:")
        if isinstance(result, dict) and "tool_return" in result:
            for item in result["tool_return"]:
                print(f"  字幕文件: {item.get('ass_file', 'N/A')}")
                print(f"  提供商: {item.get('provider', 'N/A')}")
                print(f"  语言: {item.get('language', 'N/A')}")
                print(f"  描述: {item.get('describe', 'N/A')}")
        else:
            print(f"  原始返回: {result}")

        return result

    except Exception as e:
        print(f"FunASR接口测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def compare_subtitle_files(azure_result, funasr_result):
    """比较两种方法生成的字幕文件"""
    print("\n=== 字幕文件对比 ===")

    azure_file = None
    funasr_file = None

    # 提取字幕文件路径
    if azure_result and isinstance(azure_result, dict):
        try:
            azure_file = azure_result["tool_return"][0].get("ass_file")
        except:
            pass

    if funasr_result and isinstance(funasr_result, dict):
        try:
            funasr_file = funasr_result["tool_return"][0].get("ass_file")
        except:
            pass

    if not azure_file or not funasr_file:
        print("无法获取字幕文件路径进行比较")
        return

    # 构建完整路径
    data_dir = current_dir / "data"
    azure_path = data_dir / azure_file if azure_file else None
    funasr_path = data_dir / funasr_file if funasr_file else None

    print(f"Azure字幕文件: {azure_path}")
    print(f"FunASR字幕文件: {funasr_path}")

    # 读取并比较字幕内容
    try:
        if azure_path and azure_path.exists():
            with open(azure_path, 'r', encoding='utf-8') as f:
                azure_content = f.read()
            print(f"\nAzure字幕内容预览 (前500字符):")
            print(azure_content[:500])
            print("..." if len(azure_content) > 500 else "")
        else:
            print(f"Azure字幕文件不存在: {azure_path}")

    except Exception as e:
        print(f"读取Azure字幕失败: {e}")

    try:
        if funasr_path and funasr_path.exists():
            with open(funasr_path, 'r', encoding='utf-8') as f:
                funasr_content = f.read()
            print(f"\nFunASR字幕内容预览 (前500字符):")
            print(funasr_content[:500])
            print("..." if len(funasr_content) > 500 else "")
        else:
            print(f"FunASR字幕文件不存在: {funasr_path}")

    except Exception as e:
        print(f"读取FunASR字幕失败: {e}")

def test_audio_transcription():
    """测试纯音频转录功能对比"""
    print("\n=== 音频转录对比测试 ===")

    try:
        from audiocut_agent.tools.funasr_audio_tools import funasr_transcribe_audio

        audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"

        print("测试FunASR音频转录...")
        result = funasr_transcribe_audio(audio_path, "中文")

        print("FunASR音频转录成功！")
        if isinstance(result, dict) and "tool_return" in result:
            segments = result["tool_return"][0].get("segments", [])
            print(f"识别到 {len(segments)} 个片段:")
            for i, segment in enumerate(segments[:5]):  # 显示前5个
                print(f"  {i+1}. [{segment.get('start_time', 0):.2f}s-{segment.get('end_time', 0):.2f}s] {segment.get('text', '')}")
            if len(segments) > 5:
                print(f"  ... 还有 {len(segments)-5} 个片段")

        return result

    except Exception as e:
        print(f"FunASR音频转录测试失败: {e}")
        return None

def main():
    """主测试函数"""
    print("字幕生成接口对比测试")
    print("=" * 60)

    # 检查测试音频是否存在
    test_audio = current_dir / "models/funasr/paraformer_zh/example/asr_example.wav"
    if not test_audio.exists():
        print(f"测试音频不存在: {test_audio}")
        return

    print(f"使用测试音频: {test_audio}")
    print(f"音频大小: {test_audio.stat().st_size} 字节")

    # 测试两种字幕生成方法
    azure_result = test_azure_subtitle()
    funasr_result = test_funasr_subtitle()

    # 对比结果
    compare_subtitle_files(azure_result, funasr_result)

    # 测试纯转录功能
    transcription_result = test_audio_transcription()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"Azure接口: {'成功' if azure_result else '失败'}")
    print(f"FunASR字幕接口: {'成功' if funasr_result else '失败'}")
    print(f"FunASR转录接口: {'成功' if transcription_result else '失败'}")

    if azure_result and funasr_result:
        print("\n两种接口都工作正常，可以进行实际应用！")
    elif funasr_result:
        print("\nFunASR接口工作正常，可以作为主要的中文字幕生成方案！")
    else:
        print("\n需要检查配置和依赖")

if __name__ == "__main__":
    main()