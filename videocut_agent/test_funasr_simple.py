"""
简化的FunASR工具测试
避免复杂依赖，直接测试核心功能
"""

import sys
import os
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_basic_imports():
    """测试基础导入"""
    print("=== 基础导入测试 ===")

    results = {}

    # 1. 测试ASR架构
    try:
        from tools.asr_base import get_transcriber, ASRFactory
        results['asr_base'] = True
        print("✓ ASR基础架构可用")

        # 测试提供商检测
        providers = ASRFactory.get_available_providers()
        results['providers'] = providers
        print(f"✓ 可用提供商: {providers}")

    except Exception as e:
        results['asr_base'] = False
        print(f"✗ ASR架构失败: {e}")

    # 2. 测试FunASR转录器类
    try:
        from tools.funasr_transcriber import FunASRTranscriber
        results['funasr_class'] = True
        print("✓ FunASR转录器类可用")
    except Exception as e:
        results['funasr_class'] = False
        print(f"✗ FunASR转录器类失败: {e}")

    return results

def test_tool_creation():
    """测试工具创建"""
    print("\n=== 工具创建测试 ===")

    # 测试subtitle工具
    try:
        sys.path.append('subtitle_agent/tools')
        # 直接导入工具函数，不通过tools_manager
        from funasr_subtitle_tools import funasr_audio2ass_tool
        print("✓ subtitle FunASR工具函数可用")

        # 测试工具是否可调用
        tool_info = {
            'name': funasr_audio2ass_tool.name,
            'description': funasr_audio2ass_tool.description
        }
        print(f"  工具名称: {tool_info['name']}")
        return True

    except Exception as e:
        print(f"✗ subtitle工具创建失败: {e}")
        return False

def test_audio_tools():
    """测试音频工具"""
    print("\n=== 音频工具测试 ===")

    try:
        sys.path.append('audiocut_agent/tools')
        from funasr_audio_tools import funasr_transcribe_audio
        print("✓ audiocut FunASR工具函数可用")

        tool_info = {
            'name': funasr_transcribe_audio.name,
            'description': funasr_transcribe_audio.description
        }
        print(f"  工具名称: {tool_info['name']}")
        return True

    except Exception as e:
        print(f"✗ audiocut工具创建失败: {e}")
        return False

def test_model_directory():
    """测试模型目录"""
    print("\n=== 模型目录测试 ===")

    models_dir = Path("models/funasr")

    if models_dir.exists():
        files = list(models_dir.iterdir())
        print(f"✓ 模型目录存在: {models_dir}")
        print(f"✓ 包含 {len(files)} 个文件/文件夹")

        # 显示前几个文件
        for i, f in enumerate(files[:3]):
            print(f"  - {f.name}")

        return True
    else:
        print(f"✗ 模型目录不存在: {models_dir}")
        return False

def main():
    """主测试函数"""
    print("FunASR工具简化测试")
    print("=" * 50)

    results = {}

    # 运行测试
    results['imports'] = test_basic_imports()
    results['subtitle_tools'] = test_tool_creation()
    results['audio_tools'] = test_audio_tools()
    results['models'] = test_model_directory()

    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")

    score = 0
    total = 4

    if results['imports'].get('asr_base'):
        print("✓ ASR架构基础功能正常")
        score += 1
    else:
        print("✗ ASR架构基础功能异常")

    if results['subtitle_tools']:
        print("✓ subtitle_agent FunASR工具可用")
        score += 1
    else:
        print("✗ subtitle_agent FunASR工具不可用")

    if results['audio_tools']:
        print("✓ audiocut_agent FunASR工具可用")
        score += 1
    else:
        print("✗ audiocut_agent FunASR工具不可用")

    if results['models']:
        print("✓ 模型目录配置正确")
        score += 1
    else:
        print("✗ 模型目录需要配置")

    print(f"\n总分: {score}/{total}")

    # 建议
    if score >= 3:
        print("🎉 FunASR工具集成基本成功！")
        print("主要功能已可用，可以进行实际测试")
    elif score >= 2:
        print("⚠️ FunASR工具部分可用")
        print("需要解决依赖问题和模型配置")
    else:
        print("❌ FunASR工具集成需要修复")
        print("建议检查依赖和配置")

    # 使用说明
    print(f"\n使用说明:")
    print("1. 安装完整依赖: pip install funasr[all]")
    print("2. 下载模型: cd models && python download.py")
    print("3. 直接调用工具函数进行测试")

    return results

if __name__ == "__main__":
    main()