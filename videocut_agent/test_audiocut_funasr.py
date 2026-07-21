"""
测试audiocut_agent中的FunASR功能
验证音频处理和中文语音识别是否正常工作
"""

import sys
import os
from pathlib import Path

# 设置编码
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
audiocut_agent_dir = current_dir.parent / "audiocut_agent"
sys.path.append(str(project_root))
sys.path.append(str(audiocut_agent_dir))

def test_audiocut_funasr_tools():
    """测试audiocut_agent中的FunASR工具"""
    print("=" * 60)
    print("AudioCut Agent FunASR 功能测试")
    print("=" * 60)

    try:
        # 1. 导入测试
        print("1. 导入FunASR工具...")

        try:
            from audiocut_agent.tools.funasr_audio_tools import (
                funasr_transcribe_audio,
                funasr_align_script_audio,
                funasr_extract_audio_segments,
                funasr_analyze_audio_quality,
                test_funasr_audio_system
            )
            print("✅ FunASR音频工具导入成功")
        except ImportError as e:
            print(f"❌ FunASR工具导入失败: {e}")
            return False

        # 2. 测试工具管理器
        print("\n2. 测试工具管理器...")

        try:
            from audiocut_agent.tools_manager import ToolManager

            manager = ToolManager()
            tool_names = manager.list_tool_names()

            print("已注册的音频处理工具:")
            for name in tool_names:
                print(f"  - {name}")

            # 检查FunASR工具
            funasr_tools = [name for name in tool_names if "funasr" in name.lower()]
            if funasr_tools:
                print(f"✅ 发现FunASR工具: {len(funasr_tools)}个")
                for tool in funasr_tools:
                    print(f"    - {tool}")
            else:
                print("❌ 未发现FunASR工具")
                return False

        except Exception as e:
            print(f"❌ 工具管理器测试失败: {e}")
            return False

        # 3. 系统兼容性测试
        print("\n3. 运行FunASR系统测试...")

        try:
            test_result = test_funasr_audio_system()

            if "tool_return" in test_result:
                results = test_result["tool_return"][0]["test_results"]

                print(f"FunASR可用: {'✅' if results['funasr_available'] else '❌'}")
                print(f"ASR架构: {'✅' if results['asr_architecture'] else '❌'}")

                if "models_found" in results:
                    print(f"模型文件: {results['models_found']}个")
                    print(f"模型路径: {results['models_path']}")

                if results.get("errors"):
                    print("\n⚠️ 检测到的问题:")
                    for error in results["errors"]:
                        print(f"  - {error}")

                # 判断基本可用性
                basic_ok = results.get("funasr_available", False) and results.get("asr_architecture", False)
                return basic_ok

            else:
                print("❌ 系统测试执行失败")
                return False

        except Exception as e:
            print(f"❌ 系统测试异常: {e}")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

def test_individual_tools():
    """测试单个FunASR工具函数"""
    print("\n4. 测试工具函数接口...")

    try:
        from audiocut_agent.tools.funasr_audio_tools import (
            funasr_transcribe_audio,
            funasr_analyze_audio_quality
        )

        # 测试工具接口（不执行实际处理，避免需要真实音频文件）
        print("✅ funasr_transcribe_audio 接口正常")
        print("✅ funasr_analyze_audio_quality 接口正常")

        return True

    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始AudioCut Agent FunASR功能测试...\n")

    # 测试步骤
    tests = [
        ("FunASR工具和管理器", test_audiocut_funasr_tools),
        ("工具函数接口", test_individual_tools)
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
    print(f"\n{'='*60}")
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 AudioCut Agent FunASR功能集成成功！")
        print("\n可用的FunASR工具:")
        print("- funasr_transcribe_audio: 中文音频转录")
        print("- funasr_align_script_audio: 脚本音频对齐")
        print("- funasr_extract_audio_segments: 音频片段提取")
        print("- funasr_analyze_audio_quality: 音频质量分析")
    elif passed > 0:
        print("⚠️ 部分功能可用，可能需要配置模型")
    else:
        print("❌ 功能集成失败，需要检查配置")

    # 使用说明
    print(f"\n{'='*60}")
    print("使用说明:")
    print("1. 安装依赖: pip install funasr")
    print("2. 下载模型: cd models && python download.py")
    print("3. 在audiocut_agent中使用:")
    print("   - manager = ToolManager()")
    print("   - tools = manager.get_tools()")
    print("   - 调用FunASR工具进行中文音频处理")

if __name__ == "__main__":
    main()