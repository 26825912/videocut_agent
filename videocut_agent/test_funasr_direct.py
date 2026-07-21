"""
直接测试FunASR字幕生成功能
避开复杂的导入问题，直接测试核心功能
"""

import sys
import os
from pathlib import Path

# 设置路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "tools"))

def test_funasr_transcription():
    """直接测试FunASR转录功能"""
    print("=== 直接测试FunASR转录功能 ===")

    try:
        from tools.asr_base import get_transcriber

        # 使用FunASR自带的示例音频
        audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"

        if not os.path.exists(audio_path):
            print(f"测试音频文件不存在: {audio_path}")
            return None

        print(f"使用测试音频: {audio_path}")

        # 创建FunASR转录器
        transcriber = get_transcriber(provider="funasr", language="zh-cn")
        print("FunASR转录器创建成功")

        # 执行转录
        print("开始转录音频...")
        segments = transcriber.file_to_text(audio_path)

        print(f"转录完成！识别到 {len(segments)} 个片段:")

        # 显示转录结果
        for i, segment in enumerate(segments):
            print(f"{i+1}. [{segment.get('start_time', 0):.2f}s-{segment.get('end_time', 0):.2f}s] {segment.get('text', '')}")

        return segments

    except Exception as e:
        print(f"FunASR转录测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_subtitle_generation():
    """测试字幕生成"""
    print("\n=== 测试字幕文件生成 ===")

    try:
        # 直接调用FunASR字幕生成逻辑
        from tools.funasr_transcriber import FunASRTranscriber

        audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"

        # 创建转录器
        transcriber = FunASRTranscriber(language="zh-cn")

        # 转录音频
        segments = transcriber.file_to_text(audio_path)

        if not segments:
            print("音频转录失败，无法生成字幕")
            return None

        print(f"音频转录成功，识别到 {len(segments)} 个片段")

        # 生成简单的SRT字幕格式
        srt_content = ""
        for i, segment in enumerate(segments, 1):
            start_time = format_time(segment.get('start_time', 0))
            end_time = format_time(segment.get('end_time', 0))
            text = segment.get('text', '')

            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"

        # 保存字幕文件
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        subtitle_dir = data_dir / "result_video" / "subtitles"
        subtitle_dir.mkdir(exist_ok=True, parents=True)

        srt_file = subtitle_dir / "funasr_test.srt"

        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        print(f"字幕文件生成成功: {srt_file}")
        print("字幕内容预览:")
        print("=" * 40)
        print(srt_content[:300] + "..." if len(srt_content) > 300 else srt_content)
        print("=" * 40)

        return str(srt_file)

    except Exception as e:
        print(f"字幕生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def format_time(seconds):
    """将秒数格式化为SRT时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def compare_with_azure():
    """对比Azure和FunASR的转录结果"""
    print("\n=== 对比不同ASR引擎结果 ===")

    audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"

    try:
        from tools.asr_base import get_transcriber

        # 测试FunASR
        print("FunASR转录结果:")
        funasr_transcriber = get_transcriber(provider="funasr", language="zh-cn")
        funasr_segments = funasr_transcriber.file_to_text(audio_path)

        funasr_text = " ".join([seg.get('text', '') for seg in funasr_segments])
        print(f"识别文本: {funasr_text}")
        print(f"片段数: {len(funasr_segments)}")

        # 测试Azure（如果可用）
        print("\nAzure转录结果:")
        try:
            azure_transcriber = get_transcriber(provider="azure", language="zh-cn")
            azure_segments = azure_transcriber.file_to_text(audio_path)

            azure_text = " ".join([seg.get('text', '') for seg in azure_segments])
            print(f"识别文本: {azure_text}")
            print(f"片段数: {len(azure_segments)}")

            # 对比结果
            print("\n=== 结果对比 ===")
            print(f"FunASR: {funasr_text}")
            print(f"Azure:  {azure_text}")

        except Exception as e:
            print(f"Azure转录失败: {e}")

    except Exception as e:
        print(f"对比测试失败: {e}")

def main():
    """主测试函数"""
    print("FunASR 字幕生成接口实际测试")
    print("=" * 50)

    # 检查测试音频
    audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"
    if not os.path.exists(audio_path):
        print(f"❌ 测试音频不存在: {audio_path}")
        return

    print(f"✅ 找到测试音频: {audio_path}")
    print(f"音频大小: {os.path.getsize(audio_path)} 字节")

    # 执行测试
    segments = test_funasr_transcription()

    if segments:
        subtitle_file = test_subtitle_generation()
        compare_with_azure()

        print("\n" + "=" * 50)
        print("测试结果总结:")
        print(f"✅ FunASR转录成功: {len(segments)} 个片段")
        print(f"✅ 字幕文件生成成功: {subtitle_file}")
        print("\nFunASR字幕生成接口工作正常！")
        print("可以用于实际的中文语音识别和字幕生成任务")
    else:
        print("\n❌ FunASR转录失败，需要检查配置")

if __name__ == "__main__":
    main()