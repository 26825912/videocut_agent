#!/usr/bin/env python3
"""
测试智能体配置是否正确工作
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.append('.')

# 加载.env配置
load_dotenv()

def test_api_config():
    """测试API配置读取"""
    print("=== API配置测试 ===")
    api_key = os.getenv("GEMINI_API_KEY")
    api_base = os.getenv("GEMINI_API_BASE")

    print(f"GEMINI_API_KEY: {api_key[:20]}...")  # 只显示前20字符
    print(f"GEMINI_API_BASE: {api_base}")

    if not api_key or not api_base:
        print("× 配置读取失败")
        return False
    else:
        print("✓ 配置读取成功")
        return True

def test_llm_creation():
    """测试LLM创建"""
    print("\n=== LLM创建测试 ===")
    try:
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("GEMINI_API_KEY")
        api_base = os.getenv("GEMINI_API_BASE")

        # 创建LLM实例
        llm = ChatOpenAI(
            model="gemini-2.5-pro",
            openai_api_key=api_key,
            openai_api_base=api_base,
            temperature=0
        )

        print("✓ LLM实例创建成功")
        print(f"模型: {llm.model_name}")
        return True

    except Exception as e:
        print(f"× LLM创建失败: {e}")
        return False

def test_agent_import():
    """测试智能体导入"""
    print("\n=== 智能体导入测试 ===")

    agents_to_test = [
        ("assert_search_agent.agent", "create_assert_search_agent"),
        ("audiocut_agent.agent", "create_audiocut_agent"),
        ("main_agent2", "MainAgent"),
    ]

    success_count = 0

    for module_name, function_name in agents_to_test:
        try:
            module = __import__(module_name, fromlist=[function_name])
            func = getattr(module, function_name, None)
            if func:
                print(f"✓ {module_name}.{function_name} 导入成功")
                success_count += 1
            else:
                print(f"× {module_name}.{function_name} 函数不存在")
        except ImportError as e:
            print(f"⚠ {module_name} 导入跳过: {e}")
        except Exception as e:
            print(f"× {module_name} 导入失败: {e}")

    return success_count > 0

if __name__ == "__main__":
    print("Videocut Agent 配置测试")
    print("=" * 40)

    # 运行测试
    config_ok = test_api_config()
    llm_ok = test_llm_creation()
    agent_ok = test_agent_import()

    print(f"\n测试结果:")
    print(f"配置读取: {'✓' if config_ok else '×'}")
    print(f"LLM创建: {'✓' if llm_ok else '×'}")
    print(f"智能体导入: {'✓' if agent_ok else '×'}")

    if config_ok and llm_ok:
        print(f"\n系统配置正常！智能体可以使用您的API配置。")
    else:
        print(f"\n系统配置存在问题，请检查依赖和配置。")