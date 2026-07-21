"""
FunASR 字幕生成工具
专门用于中文语音识别和字幕生成，集成FunASR开源模型
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
import pysubs2
from pysubs2 import SSAEvent
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

from .subtitle_v2_tools import StyleManager, get_data_dir
# 直接导入VideoFormat，避免循环导入
import sys
from pathlib import Path
tools_dir = Path(__file__).parent.parent.parent / "tools"
sys.path.append(str(tools_dir))

try:
    from video_formats import VideoFormat
except ImportError:
    # 如果video_formats不可用，使用简单的替代
    class VideoFormat:
        Width = 720
        Height = 1280

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class FunASRSubtitleGenerator:
    """
    使用FunASR的字幕生成器
    专门针对中文优化，支持逐词级别的精确时间戳
    """

    def __init__(self,
                 language: str = "zh-cn",
                 model_size: str = "large",
                 use_gpu: bool = True):
        """
        初始化FunASR字幕生成器

        Args:
            language: 语言代码 ("zh-cn", "en")
            model_size: 模型大小
            use_gpu: 是否使用GPU
        """
        self.language = language
        self.model_size = model_size
        self.use_gpu = use_gpu

        # 检查ASR架构是否可用
        if not ASR_AVAILABLE:
            raise ImportError("新ASR架构不可用，请确保已正确配置")

        logger.info(f"初始化FunASR字幕生成器: 语言={language}, GPU={use_gpu}")

    def preprocess_audio(self, input_path: str) -> Optional[str]:
        """
        音频预处理，转换为标准格式

        Args:
            input_path: 输入音频路径

        Returns:
            str: 预处理后的WAV文件路径
        """
        logger.info(f"🔄 预处理音频: {input_path}")

        try:
            filename_only = os.path.splitext(os.path.basename(input_path))[0]
            temp_wav = f"temp_funasr_{filename_only}.wav"

            audio = AudioSegment.from_file(input_path)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(temp_wav, format="wav")

            logger.info(f"✅ 音频预处理完成: {temp_wav}")
            return temp_wav

        except Exception as e:
            logger.error(f"❌ 音频预处理失败: {e}")
            return None

    def recognize_audio_with_funasr(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        使用FunASR识别音频

        Args:
            audio_path: 音频文件路径

        Returns:
            List[Dict]: 识别结果，包含逐词时间戳
        """
        logger.info(f"🎤 FunASR语音识别: {audio_path}")

        try:
            # 获取FunASR转录器
            transcriber = get_transcriber(
                provider="funasr",
                language=self.language,
                model_size=self.model_size,
                use_gpu=self.use_gpu
            )

            # 执行识别
            segments = transcriber.file_to_text(audio_path)

            # 转换为字幕生成所需的格式
            words_data = []
            for segment in segments:
                # FunASR返回的格式已经包含精确时间戳
                words_data.append({
                    "word": segment["text"],
                    "start_ticks": int(segment["start_time"] * 10000000),  # 转换为ticks
                    "end_ticks": int(segment["end_time"] * 10000000)
                })

            logger.info(f"✅ FunASR识别完成，共{len(words_data)}个片段")
            return words_data

        except Exception as e:
            logger.error(f"❌ FunASR识别失败: {e}")
            return []

    def generate_chinese_ass(self, words_data: List[Dict], output_file: str):
        """
        生成中文ASS字幕文件

        Args:
            words_data: 识别结果数据
            output_file: 输出文件路径
        """
        logger.info(f"🎬 生成中文ASS字幕: {output_file}")

        # 中文字幕参数配置
        MAX_CHARS = 20           # 中文字幕一行最多20个字符
        MAX_PAUSE_TICKS = 5000000  # 0.5秒停顿判断换行
        SPLIT_PUNCTUATIONS = ("，", "。", "？", "！", "；", "：")  # 中文标点

        # 创建字幕文件
        subs = pysubs2.SSAFile()
        subs.info['Title'] = 'FunASR Generated Chinese Subtitles'
        subs.info['ScriptType'] = 'v4.00+'
        subs.info['PlayResX'] = str(VideoFormat.Width)
        subs.info['PlayResY'] = str(VideoFormat.Height)
        subs.info['WrapStyle'] = '0'
        subs.info['ScaledBorderAndShadow'] = 'yes'
        subs.info['YCbCr Matrix'] = 'None'

        # 加载中文字体样式
        try:
            data_dir = get_data_dir()
            subtitle_style_path = os.path.join(data_dir, 'paraments_info', 'subtitle', 'frontstyle.json')
            styles = StyleManager.load_from_file(subtitle_style_path)
            subs.styles[styles.name] = styles
        except Exception as e:
            logger.warning(f"加载字体样式失败，使用默认样式: {e}")
            # 使用默认中文样式
            default_style = pysubs2.SSAStyle()
            default_style.name = "Default"
            default_style.fontname = "Microsoft YaHei"
            default_style.fontsize = 32
            default_style.alignment = 2  # 底部居中
            subs.styles["Default"] = default_style

        current_line_words = []

        for i, word in enumerate(words_data):
            word_text = word['word']

            # 处理超长单词（FunASR可能返回整句）
            if len(word_text) > MAX_CHARS:
                # 保存之前的缓存
                if current_line_words:
                    self._add_chinese_event(subs, current_line_words)
                    current_line_words = []
                # 超长内容按标点切分
                self._split_long_text(subs, word, MAX_CHARS)
                continue

            # 判断是否需要换行
            need_new_line = False

            if current_line_words:
                prev_word = current_line_words[-1]

                # 停顿检测
                if (word['start_ticks'] - prev_word['end_ticks']) > MAX_PAUSE_TICKS:
                    need_new_line = True

                # 长度检测（中文不需要空格）
                current_len = sum(len(w['word']) for w in current_line_words)
                if current_len + len(word_text) > MAX_CHARS:
                    need_new_line = True

            # 执行换行
            if need_new_line:
                self._add_chinese_event(subs, current_line_words)
                current_line_words = []

            # 加入当前词
            current_line_words.append(word)

            # 标点符号断句
            if word_text.endswith(SPLIT_PUNCTUATIONS):
                self._add_chinese_event(subs, current_line_words)
                current_line_words = []

        # 处理残留
        if current_line_words:
            self._add_chinese_event(subs, current_line_words)

        # 保存字幕文件
        self._save_formatted_ass(subs, output_file)
        logger.info(f"🎉 中文字幕生成完成: {output_file}")

    def _add_chinese_event(self, subs: pysubs2.SSAFile, word_list: List[Dict]):
        """添加中文字幕事件"""
        if not word_list:
            return

        start_ms = int(word_list[0]['start_ticks'] / 10000)
        end_ms = int(word_list[-1]['end_ticks'] / 10000)

        # 中文直接连接，不使用空格
        text = "".join([w['word'] for w in word_list])

        event = SSAEvent(start=start_ms, end=end_ms, text=text)
        event.style = "Default"
        subs.events.append(event)

    def _split_long_text(self, subs: pysubs2.SSAFile, word_data: Dict, max_chars: int):
        """切分超长文本"""
        text = word_data['word']
        start_ticks = word_data['start_ticks']
        end_ticks = word_data['end_ticks']
        duration = end_ticks - start_ticks

        # 按标点符号或长度切分
        chunks = []
        current_chunk = ""

        for char in text:
            current_chunk += char

            # 遇到标点或达到最大长度时切分
            if char in "，。？！；：" or len(current_chunk) >= max_chars:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = ""

        # 处理剩余部分
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # 为每个chunk分配时间
        for i, chunk in enumerate(chunks):
            chunk_start = start_ticks + int(i * duration / len(chunks))
            chunk_end = start_ticks + int((i + 1) * duration / len(chunks))

            start_ms = int(chunk_start / 10000)
            end_ms = int(chunk_end / 10000)

            event = SSAEvent(start=start_ms, end=end_ms, text=chunk)
            event.style = "Default"
            subs.events.append(event)

    def _save_formatted_ass(self, subs: pysubs2.SSAFile, output_file: str):
        """保存格式化的ASS文件"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # 生成ASS内容并格式化
            ass_content = subs.to_string(format_="ass")

            # 格式化修复
            if "[V4+ Styles]" in ass_content:
                ass_content = ass_content.replace("[V4+ Styles]", "\n[V4+ Styles]")
            if "[Events]" in ass_content:
                ass_content = ass_content.replace("[Events]", "\n[Events]")

            # 写入文件
            with open(output_file, "w", encoding="utf-8-sig") as f:
                f.write(ass_content)

        except Exception as e:
            logger.error(f"保存ASS文件失败: {e}")
            raise

def funasr_audio_to_ass(audio_file: str,
                        language: str = "zh-cn",
                        save_file: str = None) -> Optional[str]:
    """
    使用FunASR将音频转换为ASS字幕文件

    Args:
        audio_file: 音频文件路径
        language: 语言设置 ("zh-cn", "en")
        save_file: 保存目录名称

    Returns:
        str: 字幕文件相对路径
    """
    data_dir = get_data_dir()
    base_name = os.path.splitext(os.path.basename(audio_file))[0]

    # 确定保存路径
    if not save_file:
        save_dir = os.path.join(data_dir, 'result_video', 'subtitles')
    else:
        save_dir = os.path.join(data_dir, 'result_video', save_file, 'subtitles')

    os.makedirs(save_dir, exist_ok=True)
    output_ass = os.path.join(save_dir, f"funasr_{uuid.uuid4()}.ass")

    # 创建FunASR生成器
    generator = FunASRSubtitleGenerator(language=language)

    # 预处理音频
    temp_wav = generator.preprocess_audio(audio_file)

    try:
        if temp_wav:
            # FunASR语音识别
            words_data = generator.recognize_audio_with_funasr(temp_wav)

            if words_data:
                # 生成字幕
                generator.generate_chinese_ass(words_data, output_ass)

                # 返回相对路径
                relative_path = os.path.relpath(output_ass, data_dir)
                logger.info(f"✅ FunASR字幕生成成功: {relative_path}")
                return relative_path
            else:
                logger.warning("FunASR识别结果为空")
                return None

    except Exception as e:
        logger.error(f"FunASR字幕生成失败: {e}")
        return None

    finally:
        # 清理临时文件
        if temp_wav and os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

def funasr_video_to_ass(video_file: str,
                        language: str = "zh-cn",
                        save_file: str = None) -> Optional[str]:
    """
    使用FunASR将视频转换为ASS字幕文件

    Args:
        video_file: 视频文件路径
        language: 语言设置
        save_file: 保存目录名称

    Returns:
        str: 字幕文件相对路径
    """
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    temp_audio_path = f"temp_funasr_{base_name}.wav"

    try:
        logger.info(f"从视频提取音频: {video_file}")

        # 提取音频
        audio = AudioSegment.from_file(video_file)
        audio.export(temp_audio_path, format="wav")

        logger.info(f"音频提取完成: {temp_audio_path}")

        # 调用音频转字幕
        ass_file = funasr_audio_to_ass(temp_audio_path, language, save_file)

        return ass_file

    except Exception as e:
        logger.error(f"FunASR视频转字幕失败: {e}")
        return None

    finally:
        # 清理临时音频文件
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.info(f"临时音频文件已清理: {temp_audio_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


@tool
def funasr_audio2ass_tool(audio_file: str, language: str = "中文") -> Dict[str, Any]:
    """
    FunASR音频转字幕工具 - 专为中文语音识别优化

    Args:
        audio_file: 音频文件相对路径
        language: 语言设置，支持"中文"和"英文"，默认中文

    Returns:
        Dict: 包含字幕文件路径的结果
    """
    logger.info(f"开始FunASR音频转字幕: {audio_file}")

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

    # 执行转换
    ass_file = funasr_audio_to_ass(audio_file_path, language_code)

    if ass_file:
        return {
            "tool_return": [{
                "ass_file": ass_file,
                "provider": "FunASR",
                "language": language,
                "describe": f"使用FunASR生成的{language}字幕文件相对路径"
            }]
        }
    else:
        return {
            "tool_return": [{
                "error": "FunASR字幕生成失败",
                "describe": "请检查音频文件和FunASR模型是否正确配置"
            }]
        }


@tool
def funasr_video2ass_tool(video_file: str, language: str = "中文") -> Dict[str, Any]:
    """
    FunASR视频转字幕工具 - 专为中文语音识别优化

    Args:
        video_file: 视频文件相对路径
        language: 语言设置，支持"中文"和"英文"，默认中文

    Returns:
        Dict: 包含字幕文件路径的结果
    """
    logger.info(f"开始FunASR视频转字幕: {video_file}")

    # 语言映射
    lang_mapping = {
        "中文": "zh-cn",
        "英文": "en",
        "zh-cn": "zh-cn",
        "en": "en"
    }

    language_code = lang_mapping.get(language, "zh-cn")

    # 构建完整路径
    video_file_path = os.path.join(get_data_dir(), video_file)

    # 执行转换
    ass_file = funasr_video_to_ass(video_file_path, language_code)

    if ass_file:
        return {
            "tool_return": [{
                "ass_file": ass_file,
                "provider": "FunASR",
                "language": language,
                "describe": f"使用FunASR生成的{language}字幕文件相对路径"
            }]
        }
    else:
        return {
            "tool_return": [{
                "error": "FunASR字幕生成失败",
                "describe": "请检查视频文件和FunASR模型是否正确配置"
            }]
        }


@tool
def test_funasr_subtitle_system() -> Dict[str, Any]:
    """
    测试FunASR字幕系统是否正常工作

    Returns:
        Dict: 测试结果
    """
    test_results = {
        "funasr_available": False,
        "models_status": {},
        "test_transcriber": False,
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
                # 检查模型状态
                transcriber = get_transcriber(provider="funasr")
                if hasattr(transcriber, 'check_model_status'):
                    test_results["models_status"] = transcriber.check_model_status()

                test_results["test_transcriber"] = True
                logger.info("✅ FunASR转录器创建成功")

            except Exception as e:
                test_results["errors"].append(f"FunASR转录器测试失败: {e}")
                logger.error(f"❌ FunASR转录器测试失败: {e}")
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
            "describe": "FunASR字幕系统测试结果"
        }]
    }