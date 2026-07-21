"""
FunASR 音频处理工具
专门用于audiocut_agent中的中文语音识别和音频处理功能
"""

import os
import sys
import json
import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from pydub import AudioSegment
from langchain_core.tools import tool

# 添加项目根路径，以便导入新的ASR架构
current_dir = Path(__file__).parent.parent.parent
sys.path.append(str(current_dir))

try:
    from tools.asr_base import get_transcriber
    from tools.funasr_transcriber import FunASRTranscriber
    ASR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入新ASR架构: {e}")
    ASR_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_data_dir():
    """获取数据目录"""
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir

class FunASRAudioProcessor:
    """
    使用FunASR的音频处理器
    专门针对音频剪辑场景优化的中文语音识别
    """

    def __init__(self,
                 language: str = "zh-cn",
                 model_size: str = "large",
                 use_gpu: bool = True):
        """
        初始化FunASR音频处理器

        Args:
            language: 语言代码 ("zh-cn", "en")
            model_size: 模型大小
            use_gpu: 是否使用GPU
        """
        self.language = language
        self.model_size = model_size
        self.use_gpu = use_gpu

        if not ASR_AVAILABLE:
            raise ImportError("新ASR架构不可用，请确保已正确配置")

        logger.info(f"初始化FunASR音频处理器: 语言={language}, GPU={use_gpu}")

    def transcribe_audio_with_timestamps(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        使用FunASR转录音频并返回带时间戳的结果

        Args:
            audio_path: 音频文件路径

        Returns:
            List[Dict]: 转录结果，包含逐词时间戳
        """
        logger.info(f"🎤 FunASR音频转录: {audio_path}")

        try:
            # 获取FunASR转录器
            transcriber = get_transcriber(
                provider="funasr",
                language=self.language,
                model_size=self.model_size,
                use_gpu=self.use_gpu
            )

            # 执行转录
            segments = transcriber.file_to_text(audio_path)

            logger.info(f"✅ FunASR转录完成，共{len(segments)}个片段")
            return segments

        except Exception as e:
            logger.error(f"❌ FunASR转录失败: {e}")
            return []

    def align_script_with_funasr(self, script_data: Any, audio_path: str) -> List[Dict[str, Any]]:
        """
        使用FunASR将脚本与音频进行精确对齐

        Args:
            script_data: 脚本数据
            audio_path: 音频文件路径

        Returns:
            List[Dict]: 对齐后的脚本数据
        """
        logger.info(f"🔗 FunASR脚本对齐: {audio_path}")

        try:
            # 获取FunASR转录器
            transcriber = get_transcriber(
                provider="funasr",
                language=self.language,
                model_size=self.model_size,
                use_gpu=self.use_gpu
            )

            # 执行对齐
            aligned_result = transcriber.align_script_with_audio(script_data, audio_path)

            logger.info(f"✅ 脚本对齐完成，共{len(aligned_result)}个片段")
            return aligned_result

        except Exception as e:
            logger.error(f"❌ 脚本对齐失败: {e}")
            return []

    def extract_audio_segments(self, audio_path: str, segments: List[Dict]) -> List[str]:
        """
        根据时间戳提取音频片段

        Args:
            audio_path: 原始音频文件路径
            segments: 包含时间戳的片段列表

        Returns:
            List[str]: 提取的音频片段文件路径列表
        """
        logger.info(f"✂️ 提取音频片段: {len(segments)}个片段")

        try:
            # 加载原始音频
            audio = AudioSegment.from_file(audio_path)

            # 创建输出目录
            data_dir = get_data_dir()
            output_dir = os.path.join(data_dir, 'result_video', 'audio_segments')
            os.makedirs(output_dir, exist_ok=True)

            segment_paths = []
            base_name = os.path.splitext(os.path.basename(audio_path))[0]

            for i, segment in enumerate(segments):
                start_ms = int(segment.get('start_time', 0) * 1000)
                end_ms = int(segment.get('end_time', 0) * 1000)

                # 提取音频片段
                audio_segment = audio[start_ms:end_ms]

                # 保存片段
                segment_filename = f"{base_name}_segment_{i:03d}_{start_ms}_{end_ms}.wav"
                segment_path = os.path.join(output_dir, segment_filename)

                audio_segment.export(segment_path, format="wav")
                segment_paths.append(segment_path)

                logger.info(f"片段 {i+1}/{len(segments)}: {segment.get('text', '')} -> {segment_filename}")

            logger.info(f"✅ 音频片段提取完成，共{len(segment_paths)}个文件")
            return segment_paths

        except Exception as e:
            logger.error(f"❌ 音频片段提取失败: {e}")
            return []

    def analyze_audio_quality(self, audio_path: str) -> Dict[str, Any]:
        """
        分析音频质量和特征

        Args:
            audio_path: 音频文件路径

        Returns:
            Dict: 音频质量分析结果
        """
        logger.info(f"📊 音频质量分析: {audio_path}")

        try:
            audio = AudioSegment.from_file(audio_path)

            analysis = {
                "duration_seconds": len(audio) / 1000.0,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "frame_width": audio.frame_width,
                "max_possible_amplitude": audio.max_possible_amplitude,
                "rms": audio.rms,
                "dBFS": audio.dBFS,
                "file_size_mb": os.path.getsize(audio_path) / (1024 * 1024),
                "quality_score": self._calculate_quality_score(audio)
            }

            logger.info(f"✅ 音频分析完成: 时长{analysis['duration_seconds']:.1f}s, 质量分数{analysis['quality_score']:.1f}")
            return analysis

        except Exception as e:
            logger.error(f"❌ 音频分析失败: {e}")
            return {}

    def _calculate_quality_score(self, audio: AudioSegment) -> float:
        """计算音频质量分数"""
        score = 50.0  # 基础分数

        # 采样率评分
        if audio.frame_rate >= 44100:
            score += 20
        elif audio.frame_rate >= 22050:
            score += 15
        elif audio.frame_rate >= 16000:
            score += 10

        # 声道评分
        if audio.channels >= 2:
            score += 10
        elif audio.channels == 1:
            score += 5

        # 音量评分（避免过小或过大）
        if -20 <= audio.dBFS <= -3:
            score += 20
        elif -30 <= audio.dBFS <= 0:
            score += 10

        return min(100.0, score)


@tool
def funasr_transcribe_audio(audio_file: str, language: str = "中文") -> Dict[str, Any]:
    """
    使用FunASR转录音频文件

    Args:
        audio_file: 音频文件相对路径
        language: 语言设置，支持"中文"和"英文"

    Returns:
        Dict: 转录结果
    """
    logger.info(f"开始FunASR音频转录: {audio_file}")

    # 语言映射
    lang_mapping = {
        "中文": "zh-cn",
        "英文": "en",
        "zh-cn": "zh-cn",
        "en": "en"
    }

    language_code = lang_mapping.get(language, "zh-cn")

    # 构建完整路径
    audio_file_path = os.path.join(get_data_dir(), audio_file)

    try:
        # 创建处理器
        processor = FunASRAudioProcessor(language=language_code)

        # 执行转录
        segments = processor.transcribe_audio_with_timestamps(audio_file_path)

        if segments:
            return {
                "tool_return": [{
                    "segments": segments,
                    "total_segments": len(segments),
                    "provider": "FunASR",
                    "language": language,
                    "describe": f"使用FunASR转录的{language}音频结果，包含{len(segments)}个带时间戳的片段"
                }]
            }
        else:
            return {
                "tool_return": [{
                    "error": "FunASR转录失败",
                    "describe": "请检查音频文件和FunASR模型配置"
                }]
            }

    except Exception as e:
        logger.error(f"FunASR转录工具执行失败: {e}")
        return {
            "tool_return": [{
                "error": str(e),
                "describe": "FunASR转录工具执行异常"
            }]
        }


@tool
def funasr_align_script_audio(script_data: str, audio_file: str, language: str = "中文") -> Dict[str, Any]:
    """
    使用FunASR将脚本与音频进行精确对齐

    Args:
        script_data: 脚本数据（JSON格式字符串）
        audio_file: 音频文件相对路径
        language: 语言设置

    Returns:
        Dict: 对齐结果
    """
    logger.info(f"开始FunASR脚本对齐: {audio_file}")

    # 语言映射
    lang_mapping = {
        "中文": "zh-cn",
        "英文": "en"
    }

    language_code = lang_mapping.get(language, "zh-cn")

    # 构建完整路径
    audio_file_path = os.path.join(get_data_dir(), audio_file)

    try:
        # 解析脚本数据
        if isinstance(script_data, str):
            try:
                parsed_script = json.loads(script_data)
            except json.JSONDecodeError:
                parsed_script = [{"original_text": line} for line in script_data.split('\n') if line.strip()]
        else:
            parsed_script = script_data

        # 创建处理器
        processor = FunASRAudioProcessor(language=language_code)

        # 执行对齐
        aligned_result = processor.align_script_with_funasr(parsed_script, audio_file_path)

        if aligned_result:
            # 提取关键词和时长信息
            durations = [item.get('duration', 0) for item in aligned_result]
            keywords = []

            for item in aligned_result:
                search_keywords = item.get('search_keywords', [])
                if search_keywords:
                    import random
                    keyword = random.choice(search_keywords)
                    keywords.append(keyword)
                else:
                    text = item.get('original_text', '')
                    keywords.append(text[:20] if text else 'default')

            return {
                "tool_return": [{
                    "aligned_script": aligned_result,
                    "keywords": keywords,
                    "durations": durations,
                    "total_segments": len(aligned_result),
                    "provider": "FunASR",
                    "language": language,
                    "describe": f"使用FunASR对齐的{language}脚本，包含{len(aligned_result)}个时间戳片段"
                }]
            }
        else:
            return {
                "tool_return": [{
                    "error": "FunASR脚本对齐失败",
                    "describe": "请检查脚本格式和音频文件"
                }]
            }

    except Exception as e:
        logger.error(f"FunASR脚本对齐工具执行失败: {e}")
        return {
            "tool_return": [{
                "error": str(e),
                "describe": "FunASR脚本对齐工具执行异常"
            }]
        }


@tool
def funasr_extract_audio_segments(audio_file: str, segments_data: str, language: str = "中文") -> Dict[str, Any]:
    """
    使用FunASR识别结果提取音频片段

    Args:
        audio_file: 音频文件相对路径
        segments_data: 包含时间戳的片段数据（JSON格式字符串）
        language: 语言设置

    Returns:
        Dict: 提取结果
    """
    logger.info(f"开始提取音频片段: {audio_file}")

    # 构建完整路径
    audio_file_path = os.path.join(get_data_dir(), audio_file)

    try:
        # 解析片段数据
        if isinstance(segments_data, str):
            segments = json.loads(segments_data)
        else:
            segments = segments_data

        # 语言映射
        lang_mapping = {
            "中文": "zh-cn",
            "英文": "en"
        }

        language_code = lang_mapping.get(language, "zh-cn")

        # 创建处理器
        processor = FunASRAudioProcessor(language=language_code)

        # 提取音频片段
        segment_paths = processor.extract_audio_segments(audio_file_path, segments)

        if segment_paths:
            # 转换为相对路径
            data_dir = get_data_dir()
            relative_paths = [os.path.relpath(path, data_dir) for path in segment_paths]

            return {
                "tool_return": [{
                    "segment_files": relative_paths,
                    "total_segments": len(segment_paths),
                    "provider": "FunASR",
                    "describe": f"成功提取{len(segment_paths)}个音频片段文件"
                }]
            }
        else:
            return {
                "tool_return": [{
                    "error": "音频片段提取失败",
                    "describe": "请检查输入数据和音频文件"
                }]
            }

    except Exception as e:
        logger.error(f"音频片段提取工具执行失败: {e}")
        return {
            "tool_return": [{
                "error": str(e),
                "describe": "音频片段提取工具执行异常"
            }]
        }


@tool
def funasr_analyze_audio_quality(audio_file: str) -> Dict[str, Any]:
    """
    分析音频文件的质量和特征

    Args:
        audio_file: 音频文件相对路径

    Returns:
        Dict: 音频质量分析结果
    """
    logger.info(f"开始音频质量分析: {audio_file}")

    # 构建完整路径
    audio_file_path = os.path.join(get_data_dir(), audio_file)

    try:
        # 创建处理器
        processor = FunASRAudioProcessor()

        # 执行分析
        analysis = processor.analyze_audio_quality(audio_file_path)

        if analysis:
            return {
                "tool_return": [{
                    "analysis": analysis,
                    "recommendations": _get_quality_recommendations(analysis),
                    "describe": f"音频质量分析完成，质量分数: {analysis.get('quality_score', 0):.1f}/100"
                }]
            }
        else:
            return {
                "tool_return": [{
                    "error": "音频质量分析失败",
                    "describe": "请检查音频文件格式和路径"
                }]
            }

    except Exception as e:
        logger.error(f"音频质量分析工具执行失败: {e}")
        return {
            "tool_return": [{
                "error": str(e),
                "describe": "音频质量分析工具执行异常"
            }]
        }


def _get_quality_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """根据音频分析结果提供改进建议"""
    recommendations = []

    quality_score = analysis.get('quality_score', 0)
    sample_rate = analysis.get('sample_rate', 0)
    channels = analysis.get('channels', 0)
    dBFS = analysis.get('dBFS', 0)

    if quality_score < 60:
        recommendations.append("音频质量较低，建议重新录制或处理")

    if sample_rate < 16000:
        recommendations.append("采样率过低，建议使用16kHz以上的音频")

    if channels < 1:
        recommendations.append("声道数异常，请检查音频文件")

    if dBFS < -40:
        recommendations.append("音频音量过小，建议增加增益")
    elif dBFS > -3:
        recommendations.append("音频音量过大，可能存在削峰失真")

    if not recommendations:
        recommendations.append("音频质量良好，适合语音识别")

    return recommendations


@tool
def test_funasr_audio_system() -> Dict[str, Any]:
    """
    测试FunASR音频系统是否正常工作

    Returns:
        Dict: 测试结果
    """
    test_results = {
        "funasr_available": False,
        "asr_architecture": False,
        "models_status": {},
        "errors": []
    }

    try:
        # 1. 检查FunASR是否可用
        try:
            import funasr
            test_results["funasr_available"] = True
            logger.info("✅ FunASR库可用")
        except ImportError as e:
            test_results["errors"].append(f"FunASR库不可用: {e}")
            logger.error(f"❌ FunASR库不可用: {e}")

        # 2. 检查ASR架构
        if ASR_AVAILABLE:
            try:
                processor = FunASRAudioProcessor()
                test_results["asr_architecture"] = True
                logger.info("✅ ASR架构可用")
            except Exception as e:
                test_results["errors"].append(f"ASR架构测试失败: {e}")
                logger.error(f"❌ ASR架构测试失败: {e}")
        else:
            test_results["errors"].append("ASR架构不可用")

        # 3. 检查模型文件
        models_dir = current_dir / "models" / "funasr"
        if models_dir.exists():
            model_files = list(models_dir.iterdir())
            test_results["models_found"] = len(model_files)
            test_results["models_path"] = str(models_dir)
            logger.info(f"✅ 发现{len(model_files)}个模型文件")
        else:
            test_results["errors"].append(f"模型目录不存在: {models_dir}")
            logger.warning(f"⚠️ 模型目录不存在: {models_dir}")

    except Exception as e:
        test_results["errors"].append(f"系统测试异常: {e}")
        logger.error(f"❌ 系统测试异常: {e}")

    return {
        "tool_return": [{
            "test_results": test_results,
            "describe": "FunASR音频系统测试结果"
        }]
    }