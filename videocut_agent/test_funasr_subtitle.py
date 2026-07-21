"""
FunASR字幕系统测试脚本
测试subtitle_agent中的FunASR功能是否可以正常使用
"""

import sys
import os
from pathlib import Path

# 设置编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
subtitle_agent_dir = current_dir.parent / "subtitle_agent"
sys.path.append(str(project_root))
sys.path.append(str(subtitle_agent_dir))

def test_funasr_subtitle_system():
    """测试FunASR字幕系统"""
    print("=" * 50)
    print("FunASR 字幕系统测试")
    print("=" * 50)

    try:
        # 1. 导入测试
        print("1. 导入模块测试...")

        try:
            from subtitle_agent.tools.funasr_subtitle_tools import (
                test_funasr_subtitle_system,
                funasr_audio2ass_tool,
                funasr_video2ass_tool
            )
            print("✅ FunASR工具导入成功")
        except ImportError as e:
            print(f"❌ FunASR工具导入失败: {e}")
            return False

        # 2. 运行系统测试工具
        print("\n2. 运行FunASR系统检查...")
        test_result = test_funasr_subtitle_system()

        if "tool_return" in test_result:
            results = test_result["tool_return"][0]["test_results"]

            print(f"FunASR可用: {'✅' if results['funasr_available'] else '❌'}")
            print(f"转录器测试: {'✅' if results['test_transcriber'] else '❌'}")

            if "models_found" in results:
                print(f"发现模型文件: {results['models_found']}个")
                print(f"模型路径: {results['models_path']}")

            if results.get("errors"):
                print("\n错误信息:")
                for error in results["errors"]:
                    print(f"  ❌ {error}")

            return results.get("funasr_available", False)
        else:
            print("❌ 系统测试失败")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

def test_tools_manager():
    """测试工具管理器"""
    print("\n3. 测试工具管理器...")

    try:
        from subtitle_agent.tools_manager import ToolManager

        manager = ToolManager()
        tool_names = manager.list_tool_names()

        print("已注册的工具:")
        for name in tool_names:
            print(f"  - {name}")

        # 检查FunASR工具是否已注册
        funasr_tools = [name for name in tool_names if "funasr" in name.lower()]
        if funasr_tools:
            print(f"✅ 发现FunASR工具: {funasr_tools}")
            return True
        else:
            print("❌ 未发现FunASR工具")
            return False

    except Exception as e:
        print(f"❌ 工具管理器测试失败: {e}")
        return False

def test_with_sample_audio():
    """使用示例音频进行实际测试（如果存在的话）"""
    print("\n4. 寻找测试音频文件...")

    # 可能的音频文件位置
    data_dir = project_root / "data"
    possible_paths = [
        data_dir / "test_audio.wav",
        data_dir / "test_audio.mp3",
        data_dir / "sample.wav",
        data_dir / "sample.mp3"
    ]

    # 检查是否有现有的音频文件
    for audio_dir in [data_dir, data_dir / "result_video", data_dir / "test"]:
        if audio_dir.exists():
            for audio_file in audio_dir.rglob("*"):
                if audio_file.suffix.lower() in ['.wav', '.mp3', '.m4a', '.flac']:
                    print(f"发现音频文件: {audio_file}")

                    try:
                        # 尝试使用FunASR处理
                        from subtitle_agent.tools.funasr_subtitle_tools import funasr_audio2ass_tool

                        # 计算相对路径
                        relative_path = audio_file.relative_to(data_dir)
                        print(f"尝试处理: {relative_path}")

                        result = funasr_audio2ass_tool(str(relative_path), "中文")

                        if "tool_return" in result and "ass_file" in result["tool_return"][0]:
                            print(f"✅ 字幕生成成功: {result['tool_return'][0]['ass_file']}")
                            return True
                        else:
                            print(f"❌ 字幕生成失败: {result}")
                            return False

                    except Exception as e:
                        print(f"❌ 音频处理失败: {e}")
                        return False

    print("未找到测试音频文件，跳过实际处理测试")
    return True

def main():
    """主测试函数"""
    print("开始FunASR字幕系统完整测试...\n")

    # 测试步骤
    tests = [
        ("FunASR系统检查", test_funasr_subtitle_system),
        ("工具管理器测试", test_tools_manager),
        ("示例音频测试", test_with_sample_audio)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")

    # 测试结果总结
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！FunASR字幕系统可以正常使用")
    elif passed > 0:
        print("⚠️ 部分测试通过，系统可能需要配置")
    else:
        print("❌ 所有测试失败，需要检查配置")

    # 提供使用建议
    print(f"\n{'='*50}")
    print("使用说明:")
    print("1. 确保已安装FunASR: pip install funasr")
    print("2. 下载模型: cd models && python download.py")
    print("3. 使用工具:")
    print("   - funasr_audio2ass_tool(audio_path, '中文')")
    print("   - funasr_video2ass_tool(video_path, '中文')")

if __name__ == "__main__":
    main()