"""
Azure 转录器实现 - 适配新架构
基于微软Azure认知服务的语音识别，保持原有功能的同时适配统一接口
"""

import azure.cognitiveservices.speech as speechsdk
import os
import time
import logging
import json
import difflib
from typing import List, Dict, Any
from .asr_base import BaseTranscriber

logger = logging.getLogger(__name__)

class AzureTranscriber(BaseTranscriber):
    """
    Azure认知服务转录器实现
    保持原有Azure实现的所有功能，同时适配统一的ASR接口
    """

    def __init__(self,
                 language: str = "zh-cn",
                 subscription_key: str = None,
                 service_region: str = "eastasia",
                 request_word_level_timestamps: bool = True,
                 **kwargs):
        """
        初始化Azure转录器

        Args:
            language: 语言代码 ("zh-cn", "en-us", 等)
            subscription_key: Azure订阅密钥
            service_region: Azure服务区域
            request_word_level_timestamps: 是否请求词级时间戳
        """
        super().__init__(language, **kwargs)

        # Azure配置
        self.subscription_key = subscription_key or os.getenv("AZURE_SERVICE_KEY")
        self.service_region = service_region or os.getenv("AZURE_SERVICE_REGION", "eastasia")
        self.request_word_level_timestamps = request_word_level_timestamps

        if not self.subscription_key:
            raise ValueError("Azure subscription key is required. Set AZURE_SERVICE_KEY environment variable or pass subscription_key parameter.")

        # 语言映射
        self.language_mapping = {
            "zh-cn": "zh-CN",
            "zh": "zh-CN",
            "en": "en-US",
            "en-us": "en-US",
            "ja": "ja-JP",
            "ko": "ko-KR"
        }

        # 配置Azure Speech SDK
        azure_language = self.language_mapping.get(language.lower(), language)
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.subscription_key,
            region=self.service_region
        )
        self.speech_config.speech_recognition_language = azure_language

        if self.request_word_level_timestamps:
            self.speech_config.request_word_level_timestamps()

        logger.info(f"初始化 Azure 转录器: 语言={azure_language}, 区域={self.service_region}")

    def file_to_text(self, audio_file_path: str) -> List[Dict[str, Any]]:
        """
        使用Azure将音频文件转换为带时间戳的文本

        Args:
            audio_file_path: 音频文件路径

        Returns:
            List[Dict]: 格式为 [{"text": str, "start_time": float, "end_time": float, "duration": float}]
        """
        standard_wav_path = self.convert_to_standard_wav(audio_file_path)
        if not standard_wav_path:
            return []

        audio_config = speechsdk.AudioConfig(filename=standard_wav_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        results = []
        done = False

        def stop_cb(evt):
            nonlocal done
            done = True

        def recognized_cb(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # 1秒 = 10,000,000 ticks
                start_seconds = evt.result.offset / 10000000
                duration_seconds = evt.result.duration / 10000000
                end_seconds = start_seconds + duration_seconds

                logger.info(f"Azure识别片段: {evt.result.text} ({start_seconds:.2f}s - {end_seconds:.2f}s)")

                results.append({
                    "text": evt.result.text,
                    "start_time": round(start_seconds, 2),
                    "duration": round(duration_seconds, 2),
                    "end_time": round(end_seconds, 2)
                })

        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        speech_recognizer.start_continuous_recognition()
        while not done:
            time.sleep(0.1)
        speech_recognizer.stop_continuous_recognition()

        try:
            os.remove(standard_wav_path)
        except:
            pass

        logger.info(f"Azure转录完成，识别到 {len(results)} 个文本片段")
        return results

    def align_script_with_audio(self, script_json: Any, audio_path: str) -> List[Dict[str, Any]]:
        """
        将脚本与音频进行时间对齐
        使用原有的贪婪匹配算法
        """
        # 数据格式处理（与原版相同）
        if isinstance(script_json, str):
            try:
                script_json = json.loads(script_json)
            except json.JSONDecodeError:
                script_json = [{"original_text": line} for line in script_json.split('\n') if line.strip()]

        # 确保 script_json 里的 item 都是字典
        validated_script = []
        for item in script_json:
            if isinstance(item, str):
                validated_script.append({"original_text": item})
            elif isinstance(item, dict):
                validated_script.append(item)
        script_json = validated_script

        # 获取音频真实时长
        real_duration = self._get_audio_duration(audio_path)
        if real_duration <= 0:
            logger.warning("音频时长获取失败，将使用默认兜底时长 10s")
            real_duration = 10.0

        # 1. 获取语音识别的原始片段
        raw_segments = self.file_to_text(audio_path)

        # 如果完全没识别到 (ASR失败)，直接使用真实时长进行估算
        if not raw_segments:
            logger.warning("Azure ASR未识别到内容，使用全时长估算模式")
            return self._fallback_estimation(script_json, total_duration=real_duration)

        # 获取音频总时长 (取 ASR 结束时间 和 物理文件时长 的较大值)
        total_audio_duration = max(raw_segments[-1]['end_time'], real_duration)

        # === 第一阶段：尝试贪婪匹配 ===
        raw_idx = 0
        total_raw = len(raw_segments)

        for item in script_json:
            # 容错获取 text
            target_text = item.get('original_text', '')
            if not target_text: continue

            # 如果音频片段用完了
            if raw_idx >= total_raw:
                item['start_time'] = total_audio_duration
                item['end_time'] = total_audio_duration
                item['duration'] = 0
                continue

            current_start = raw_segments[raw_idx]['start_time']
            current_accumulated_text = ""

            # 开始匹配循环
            while raw_idx < total_raw:
                seg = raw_segments[raw_idx]
                current_accumulated_text += " " + seg['text']

                clean_accum = self._clean_text(current_accumulated_text)
                clean_target = self._clean_text(target_text)

                # 如果目标文本为空，直接跳过
                if not clean_target:
                    break

                # 计算相似度
                matcher = difflib.SequenceMatcher(None, clean_accum, clean_target)
                ratio = matcher.ratio()

                # 核心修正：增加长度惩罚
                len_ratio = len(clean_accum) / (len(clean_target) + 1) # +1防止除零

                raw_idx += 1 # 移动指针

                # 停止条件：相似度够高 OR 长度已经超了
                if ratio > 0.65 or len_ratio > 1.2:
                    break

            # 记录时间
            last_seg_idx = raw_idx - 1
            if last_seg_idx < 0: last_seg_idx = 0

            # 这里要注意，如果 raw_idx 跑得太快，可能会导致 index out of range
            if last_seg_idx < len(raw_segments):
                current_end = raw_segments[last_seg_idx]['end_time']
            else:
                current_end = raw_segments[-1]['end_time']

            item['start_time'] = round(current_start, 2)
            item['end_time'] = round(current_end, 2)
            item['duration'] = round(current_end - current_start, 2)

        # === 第二阶段：兜底修复 (Fix Zero Durations) ===
        return self._fix_zero_durations(script_json, total_audio_duration)

    def _clean_text(self, text: str) -> str:
        """清洗文本用于匹配"""
        return "".join([c for c in text if c.isalnum()]).lower()

    def _fix_zero_durations(self, script_json: List[Dict], total_duration: float) -> List[Dict]:
        """
        如果发现有 duration 为 0 的片段，或者第一段过长，
        则根据字符数比例重新分配时间。
        """
        # 1. 检查是否存在异常 (duration <= 0.1)
        has_issue = False
        for item in script_json:
            if item.get('duration', 0) < 0.1:
                has_issue = True
                break

        # 2. 如果没有问题，直接返回
        if not has_issue:
            return script_json

        # 3. 如果有问题，启动重新计算逻辑
        logger.info("正在使用字数比例进行时间重分配...")

        # 计算所有句子的总字符数
        total_chars = sum([len(item['original_text']) for item in script_json])

        current_time_pointer = 0.0

        for i, item in enumerate(script_json):
            char_count = len(item['original_text'])

            # 权重的计算：当前句字数 / 总字数
            weight = char_count / total_chars if total_chars > 0 else 0

            # 估算时长 = 总音频时长 * 权重
            estimated_duration = total_duration * weight

            # 修正时间戳
            item['start_time'] = round(current_time_pointer, 2)
            item['duration'] = round(estimated_duration, 2)
            item['end_time'] = round(current_time_pointer + estimated_duration, 2)

            # 移动指针
            current_time_pointer += estimated_duration

        return script_json

    def _fallback_estimation(self, script_json: List[Dict], total_duration: float) -> List[Dict]:
        """纯估算逻辑，同 _fix_zero_durations"""
        return self._fix_zero_durations(script_json, total_duration)

    @staticmethod
    def is_available() -> bool:
        """检查Azure SDK是否可用"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            return True
        except ImportError:
            return False

    @staticmethod
    def get_installation_instructions() -> str:
        """获取安装说明"""
        return (
            "安装 Azure Speech SDK:\n"
            "pip install azure-cognitiveservices-speech\n\n"
            "设置环境变量:\n"
            "export AZURE_SERVICE_KEY='your_key_here'\n"
            "export AZURE_SERVICE_REGION='your_region_here'\n\n"
            "详细文档: https://docs.microsoft.com/azure/cognitive-services/speech-service/"
        )