"""
更新后的 ASR 工具函数 - 使用新的可切换架构
保持与原有接口的完全兼容性，同时支持多种ASR提供商的切换
"""

import os
import logging
import random
from typing import List, Dict, Any
from langchain_core.tools import tool

# 导入新的ASR架构
from .asr_base import get_transcriber, ASRFactory, ASRConfig

logger = logging.getLogger(__name__)


def get_data_dir():
    """获取数据目录"""
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir


@tool
def asr_audio_file(audio_file_path: str, provider: str = None):
    """
    将音频文件转换为文本 - 支持多种ASR提供商

    Args:
        audio_file_path: 音频文件路径
        provider: 指定ASR提供商 (funasr, azure, whisperx 等)，不指定则使用配置中的默认值

    Returns:
        识别结果列表，格式: [{"text": str, "start_time": float, "end_time": float, "duration": float}]
    """
    try:
        # 获取转录器实例
        transcriber = get_transcriber(provider=provider)

        logger.info(f"使用 {transcriber.__class__.__name__} 进行语音识别")

        # 执行转录
        result = transcriber.file_to_text(audio_file_path)

        logger.info(f"识别完成，共 {len(result)} 个片段")
        return result

    except Exception as e:
        logger.error(f"语音识别失败: {e}")

        # 尝试使用备用提供商
        try:
            config = ASRConfig()
            fallback_provider = config.get_fallback_provider()

            if fallback_provider != provider:
                logger.info(f"尝试使用备用提供商: {fallback_provider}")
                fallback_transcriber = get_transcriber(provider=fallback_provider)
                return fallback_transcriber.file_to_text(audio_file_path)
        except Exception as fallback_error:
            logger.error(f"备用提供商也失败: {fallback_error}")

        return []


@tool
def get_script_text_time(json_data: Any, audio_path: str, provider: str = None):
    """
    将视频脚本中的关键词和对应的音频时间进行对齐，保证每一个关键词对应正确的视频素播放时间

    Args:
        json_data: 解码后的dify输出数据，里面包含了视频脚本original_text和对应的检索关键词search_keywords
        audio_path: 音频文件路径
        provider: 指定ASR提供商 (funasr, azure, whisperx 等)

    Returns:
        tuple: (keywords, durations)
        - keywords: 包含检索关键词的列表
        - durations: 每一个关键词对应检索视频素材的时长列表，用于后续视频检索的时候使用
    """
    try:
        # 处理音频路径
        if not os.path.isabs(audio_path):
            audio_path = os.path.join(get_data_dir(), audio_path)

        # 获取转录器实例
        transcriber = get_transcriber(provider=provider)

        logger.info(f"使用 {transcriber.__class__.__name__} 进行脚本对齐")

        # 执行脚本与音频对齐
        script_json = transcriber.align_script_with_audio(json_data, audio_path)

        # 提取时长和关键词
        durations = [item['duration'] for item in script_json]
        keywords = []

        for item in script_json:
            search_keywords = item.get('search_keywords', [])
            if search_keywords:
                # 随机选择一个关键词
                keyword = random.choice(search_keywords)
                keywords.append(keyword)
            else:
                # 如果没有关键词，使用原文本的一部分
                text = item.get('original_text', '')
                keywords.append(text[:20] if text else 'default')

        logger.info(f"对齐完成，共 {len(keywords)} 个关键词")
        return keywords, durations

    except Exception as e:
        logger.error(f"脚本对齐失败: {e}")

        # 尝试使用备用提供商
        try:
            config = ASRConfig()
            fallback_provider = config.get_fallback_provider()

            if fallback_provider != provider:
                logger.info(f"尝试使用备用提供商: {fallback_provider}")
                fallback_transcriber = get_transcriber(provider=fallback_provider)
                script_json = fallback_transcriber.align_script_with_audio(json_data, audio_path)

                durations = [item['duration'] for item in script_json]
                keywords = [random.choice(item.get('search_keywords', ['default'])) for item in script_json]
                return keywords, durations

        except Exception as fallback_error:
            logger.error(f"备用提供商也失败: {fallback_error}")

        # 最后的兜底返回
        return [], []


@tool
def switch_asr_provider(provider: str):
    """
    切换ASR提供商

    Args:
        provider: 新的提供商名称 (funasr, azure, whisperx, openai, tencent)

    Returns:
        str: 切换结果信息
    """
    try:
        from .asr_base import switch_asr_provider as base_switch

        # 获取可用提供商
        available_providers = ASRFactory.get_available_providers()

        if provider not in available_providers:
            return f"提供商 '{provider}' 不可用。可用的提供商: {', '.join(available_providers)}"

        # 执行切换
        base_switch(provider)

        return f"已成功切换到 ASR 提供商: {provider}"

    except Exception as e:
        logger.error(f"切换ASR提供商失败: {e}")
        return f"切换失败: {str(e)}"


@tool
def list_asr_providers():
    """
    列出所有可用的ASR提供商

    Returns:
        dict: 提供商信息，包括当前使用的和可用的提供商
    """
    try:
        config = ASRConfig()
        available_providers = ASRFactory.get_available_providers()

        current_provider = config.get_provider()
        fallback_provider = config.get_fallback_provider()

        # 检查每个提供商的状态
        provider_status = {}
        for provider in available_providers:
            try:
                transcriber = get_transcriber(provider=provider)
                provider_status[provider] = {
                    "available": True,
                    "class": transcriber.__class__.__name__
                }
            except Exception as e:
                provider_status[provider] = {
                    "available": False,
                    "error": str(e)
                }

        return {
            "current_provider": current_provider,
            "fallback_provider": fallback_provider,
            "available_providers": available_providers,
            "provider_status": provider_status,
            "language": config.get_language()
        }

    except Exception as e:
        logger.error(f"获取提供商列表失败: {e}")
        return {"error": str(e)}


@tool
def test_asr_provider(provider: str = None, test_audio_path: str = None):
    """
    测试指定的ASR提供商

    Args:
        provider: 要测试的提供商，不指定则测试当前默认提供商
        test_audio_path: 测试音频文件路径，不指定则使用项目中的示例音频

    Returns:
        dict: 测试结果
    """
    try:
        # 获取测试音频路径
        if not test_audio_path:
            # 寻找项目中的音频文件作为测试
            data_dir = get_data_dir()
            audio_extensions = ['.wav', '.mp3', '.m4a', '.flac']

            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in audio_extensions):
                        test_audio_path = os.path.join(root, file)
                        break
                if test_audio_path:
                    break

            if not test_audio_path:
                return {"error": "未找到测试音频文件，请指定 test_audio_path 参数"}

        if not os.path.exists(test_audio_path):
            return {"error": f"测试音频文件不存在: {test_audio_path}"}

        # 获取转录器
        transcriber = get_transcriber(provider=provider)
        provider_name = transcriber.__class__.__name__

        logger.info(f"测试 {provider_name}...")

        # 记录开始时间
        import time
        start_time = time.time()

        # 执行转录
        result = transcriber.file_to_text(test_audio_path)

        # 计算耗时
        elapsed_time = time.time() - start_time

        # 分析结果
        total_duration = sum(item.get('duration', 0) for item in result)
        total_text = ' '.join(item.get('text', '') for item in result)

        return {
            "provider": provider_name,
            "success": True,
            "audio_file": test_audio_path,
            "processing_time": round(elapsed_time, 2),
            "segments_count": len(result),
            "total_duration": round(total_duration, 2),
            "text_preview": total_text[:200] + "..." if len(total_text) > 200 else total_text,
            "first_few_segments": result[:3]  # 显示前几个片段作为示例
        }

    except Exception as e:
        logger.error(f"测试ASR提供商失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# 为了保持向后兼容，保留一个旧的类名映射
class AzureTranscriber:
    """向后兼容的类，重定向到新架构"""
    def __new__(cls, *args, **kwargs):
        logger.warning("AzureTranscriber 已废弃，请使用 get_transcriber(provider='azure')")
        return get_transcriber(provider='azure', **kwargs)


if __name__ == "__main__":
    # 测试代码
    print("ASR系统状态:")
    status = list_asr_providers()
    print(f"当前提供商: {status.get('current_provider')}")
    print(f"可用提供商: {', '.join(status.get('available_providers', []))}")

    # 如果有音频文件，可以进行测试
    # result = test_asr_provider()
    # print("测试结果:", result)