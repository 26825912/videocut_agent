"""
FunASR 转录器实现 - 集成本地模型管理
使用本地下载的模型权重，支持自动下载和管理
"""

import os
import json
import logging
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
from .asr_base import BaseTranscriber

# 添加models路径
current_dir = Path(__file__).parent
models_dir = current_dir.parent / "models"
sys.path.append(str(models_dir))

logger = logging.getLogger(__name__)

class FunASRTranscriber(BaseTranscriber):
    """
    FunASR转录器实现
    专为中文优化，支持逐词级别的精确时间戳
    集成本地模型管理系统
    """

    def __init__(self,
                 language: str = "zh-cn",
                 model_size: str = "large",
                 use_gpu: bool = True,
                 batch_size: int = 1,
                 auto_download: bool = True,
                 **kwargs):
        """
        初始化FunASR转录器

        Args:
            language: 语言代码 ("zh-cn", "en", 等)
            model_size: 模型大小 ("large", "base", 等)
            use_gpu: 是否使用GPU
            batch_size: 批处理大小
            auto_download: 是否自动下载缺失的模型
        """
        super().__init__(language, **kwargs)

        self.model_size = model_size
        self.use_gpu = use_gpu
        self.batch_size = batch_size
        self.auto_download = auto_download

        # 延迟加载模型和模型管理器
        self.model = None
        self.model_manager = None
        self._model_loaded = False

        logger.info(f"初始化 FunASR 转录器: 语言={language}, 模型={model_size}, GPU={use_gpu}")

    def _get_model_manager(self):
        """获取模型管理器实例"""
        if self.model_manager is None:
            try:
                from funasr_download import FunASRModelManager
                self.model_manager = FunASRModelManager()
            except ImportError as e:
                logger.error(f"无法导入模型管理器: {e}")
                # 创建一个简单的替代实现
                self.model_manager = self._create_simple_manager()
        return self.model_manager

    def _create_simple_manager(self):
        """创建简单的模型管理器替代"""
        class SimpleManager:
            def get_model_path_for_funasr(self, model_name):
                # 返回原始的HuggingFace模型ID
                model_ids = {
                    "paraformer_zh": "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                    "vad_zh": "damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                    "punc_zh": "damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                    "paraformer_en": "iic/speech_paraformer-large_asr_nat-en-16k-common-vocab10020"
                }
                return model_ids.get(model_name)

            def is_model_downloaded(self, model_name):
                return False

            def download_required_models(self):
                logger.warning("模型管理器不可用，将使用在线模型")
                return True

        return SimpleManager()

    def _ensure_models_available(self):
        """确保必需的模型可用"""
        manager = self._get_model_manager()

        # 检查必需模型是否已下载
        required_models = ["paraformer_zh", "vad_zh"]
        missing_models = []

        for model_name in required_models:
            if not manager.is_model_downloaded(model_name):
                missing_models.append(model_name)

        # 如果有缺失的模型且允许自动下载
        if missing_models and self.auto_download:
            logger.info(f"检测到缺失的模型: {missing_models}，开始自动下载...")

            try:
                success = manager.download_required_models()
                if not success:
                    logger.warning("模型下载失败，将使用在线模型")
            except Exception as e:
                logger.warning(f"自动下载模型失败: {e}，将使用在线模型")

    def _load_model(self):
        """延迟加载FunASR模型"""
        if self._model_loaded:
            return

        try:
            from funasr import AutoModel

            # 确保模型可用
            self._ensure_models_available()

            logger.info("加载 FunASR 模型...")

            # 获取模型管理器
            manager = self._get_model_manager()

            # 根据语言选择模型路径
            if self.language.lower() in ["zh-cn", "zh"]:
                asr_model_path = manager.get_model_path_for_funasr("paraformer_zh")
                vad_model_path = manager.get_model_path_for_funasr("vad_zh")
                punc_model_path = manager.get_model_path_for_funasr("punc_zh")
            else:
                # 英文模型
                asr_model_path = manager.get_model_path_for_funasr("paraformer_en")
                vad_model_path = manager.get_model_path_for_funasr("vad_zh")  # VAD模型通用
                punc_model_path = None  # 英文暂不使用标点恢复

            # 创建模型参数
            model_kwargs = {
                "model": asr_model_path,
                "device": "cuda" if self.use_gpu else "cpu"
            }

            # 添加VAD模型（如果可用）
            if vad_model_path:
                model_kwargs["vad_model"] = vad_model_path

            # 添加标点恢复模型（如果可用）
            if punc_model_path:
                model_kwargs["punc_model"] = punc_model_path

            logger.info(f"使用模型路径: ASR={asr_model_path}")
            logger.info(f"使用模型路径: VAD={vad_model_path}")
            if punc_model_path:
                logger.info(f"使用模型路径: PUNC={punc_model_path}")

            self.model = AutoModel(**model_kwargs)
            self._model_loaded = True

            logger.info("FunASR 模型加载成功")

        except ImportError:
            raise ImportError(
                "FunASR 未安装。请运行以下命令安装:\n"
                "pip install funasr\n"
                "或者参考官方文档: https://github.com/alibaba-damo-academy/FunASR"
            )
        except Exception as e:
            logger.error(f"FunASR 模型加载失败: {e}")
            logger.info("尝试手动下载模型:")
            logger.info("cd videocut_agent/models && python funasr_download.py --required")
            raise

    def file_to_text(self, audio_file_path: str) -> List[Dict[str, Any]]:
        """
        使用FunASR将音频文件转换为带时间戳的文本

        Args:
            audio_file_path: 音频文件路径

        Returns:
            List[Dict]: 格式为 [{"text": str, "start_time": float, "end_time": float, "duration": float}]
        """
        # 预处理音频
        standard_wav_path = self.convert_to_standard_wav(audio_file_path)
        if not standard_wav_path:
            return []

        try:
            # 加载模型
            self._load_model()

            logger.info("开始 FunASR 转录...")

            # FunASR识别参数
            generation_kwargs = {
                "return_raw_text": True,
                "is_final": True,
                "sentence_timestamp": True,  # 句级时间戳
                "word_timestamp": True,      # 词级时间戳
                "batch_size": self.batch_size
            }

            # 执行识别
            result = self.model.generate(
                input=standard_wav_path,
                **generation_kwargs
            )

            # 解析结果
            segments = []

            if result and len(result) > 0:
                # FunASR返回格式处理
                for item in result:
                    text = item.get('text', '')
                    timestamps = item.get('timestamp', [])

                    if timestamps and isinstance(timestamps, list):
                        # FunASR返回格式: timestamp=[[start_ms, end_ms], ...] 每个字符一个
                        # text是完整文本，timestamp中每个元素对应text中的一个字符
                        if len(timestamps) > 0 and isinstance(timestamps[0], (list, tuple)) and len(timestamps[0]) == 2:
                            # 标准格式: [[start_ms, end_ms], ...] 逐字符时间戳
                            # 将字符级时间戳合并为句子级
                            if timestamps and text.strip():
                                # 使用整个句子的开始和结束时间
                                start_time = float(timestamps[0][0]) / 1000.0
                                end_time = float(timestamps[-1][1]) / 1000.0

                                segments.append({
                                    "text": text.strip(),
                                    "start_time": round(start_time, 2),
                                    "end_time": round(end_time, 2),
                                    "duration": round(end_time - start_time, 2)
                                })
                        elif len(timestamps) > 0 and len(timestamps[0]) >= 3:
                            # 旧格式: [start_ms, end_ms, word_text]
                            for word_info in timestamps:
                                start_time = float(word_info[0]) / 1000.0
                                end_time = float(word_info[1]) / 1000.0
                                word_text = str(word_info[2]).strip()
                                if word_text:
                                    segments.append({
                                        "text": word_text,
                                        "start_time": round(start_time, 2),
                                        "end_time": round(end_time, 2),
                                        "duration": round(end_time - start_time, 2)
                                    })
                    else:
                        # 如果没有词级时间戳，使用句级
                        sentence_start = item.get('sentence_start', 0) / 1000.0 if item.get('sentence_start') else 0
                        sentence_end = item.get('sentence_end', 0) / 1000.0 if item.get('sentence_end') else 0

                        if sentence_end == 0 and text:
                            # 估算时长（每字符约0.15秒）
                            estimated_duration = len(text) * 0.15
                            sentence_end = sentence_start + estimated_duration

                        segments.append({
                            "text": text,
                            "start_time": round(sentence_start, 2),
                            "end_time": round(sentence_end, 2),
                            "duration": round(sentence_end - sentence_start, 2)
                        })

            logger.info(f"FunASR 转录完成，识别到 {len(segments)} 个文本片段")
            return segments

        except Exception as e:
            logger.error(f"FunASR 转录失败: {e}")
            return []
        finally:
            # 清理临时文件
            try:
                if os.path.exists(standard_wav_path):
                    os.remove(standard_wav_path)
            except:
                pass

    def align_script_with_audio(self, script_json: Any, audio_path: str) -> List[Dict[str, Any]]:
        """
        将脚本与音频进行时间对齐
        使用与原版相同的对齐算法，但底层使用FunASR
        """
        # 数据格式处理（与原版相同）
        if isinstance(script_json, str):
            try:
                script_json = json.loads(script_json)
            except json.JSONDecodeError:
                script_json = [{"original_text": line} for line in script_json.split('\n') if line.strip()]

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
            logger.warning("音频时长获取失败，使用默认值")
            real_duration = 10.0

        # 获取FunASR识别结果
        raw_segments = self.file_to_text(audio_path)

        if not raw_segments:
            logger.warning("FunASR 未识别到内容，使用估算模式")
            return self._fallback_estimation(script_json, total_duration=real_duration)

        # 使用贪婪匹配算法（与原版相同逻辑）
        total_audio_duration = max(raw_segments[-1]['end_time'], real_duration)

        raw_idx = 0
        total_raw = len(raw_segments)

        for item in script_json:
            target_text = item.get('original_text', '')
            if not target_text:
                continue

            if raw_idx >= total_raw:
                item['start_time'] = total_audio_duration
                item['end_time'] = total_audio_duration
                item['duration'] = 0
                continue

            current_start = raw_segments[raw_idx]['start_time']
            current_accumulated_text = ""

            while raw_idx < total_raw:
                seg = raw_segments[raw_idx]
                current_accumulated_text += " " + seg['text']

                clean_accum = self._clean_text(current_accumulated_text)
                clean_target = self._clean_text(target_text)

                if not clean_target:
                    break

                # 相似度计算
                import difflib
                matcher = difflib.SequenceMatcher(None, clean_accum, clean_target)
                ratio = matcher.ratio()

                len_ratio = len(clean_accum) / (len(clean_target) + 1)
                raw_idx += 1

                if ratio > 0.65 or len_ratio > 1.2:
                    break

            # 记录时间
            last_seg_idx = raw_idx - 1
            if last_seg_idx < 0:
                last_seg_idx = 0

            if last_seg_idx < len(raw_segments):
                current_end = raw_segments[last_seg_idx]['end_time']
            else:
                current_end = raw_segments[-1]['end_time']

            item['start_time'] = round(current_start, 2)
            item['end_time'] = round(current_end, 2)
            item['duration'] = round(current_end - current_start, 2)

        return self._fix_zero_durations(script_json, total_audio_duration)

    def _clean_text(self, text: str) -> str:
        """清洗文本用于匹配"""
        # 中文文本清洗：保留中文、英文、数字
        import re
        return re.sub(r'[^\w\u4e00-\u9fff]', '', text).lower()

    def _fix_zero_durations(self, script_json: List[Dict], total_duration: float) -> List[Dict]:
        """修复零时长片段（与原版逻辑相同）"""
        has_issue = False
        for item in script_json:
            if item.get('duration', 0) < 0.1:
                has_issue = True
                break

        if not has_issue:
            return script_json

        logger.info("使用字数比例重新分配时间")

        # 计算总字符数（中文每个字符权重相同）
        total_chars = sum([len(item['original_text']) for item in script_json])
        current_time_pointer = 0.0

        for item in script_json:
            char_count = len(item['original_text'])
            weight = char_count / total_chars if total_chars > 0 else 0
            estimated_duration = total_duration * weight

            item['start_time'] = round(current_time_pointer, 2)
            item['duration'] = round(estimated_duration, 2)
            item['end_time'] = round(current_time_pointer + estimated_duration, 2)

            current_time_pointer += estimated_duration

        return script_json

    def _fallback_estimation(self, script_json: List[Dict], total_duration: float) -> List[Dict]:
        """纯估算模式"""
        return self._fix_zero_durations(script_json, total_duration)

    @staticmethod
    def is_available() -> bool:
        """检查FunASR是否可用"""
        try:
            import funasr
            return True
        except ImportError:
            return False

    @staticmethod
    def get_installation_instructions() -> str:
        """获取安装说明"""
        return (
            "安装 FunASR:\n"
            "pip install funasr\n\n"
            "下载模型:\n"
            "cd videocut_agent/models\n"
            "python funasr_download.py --required\n\n"
            "详细文档: https://github.com/alibaba-damo-academy/FunASR"
        )

    def check_model_status(self) -> Dict[str, Any]:
        """检查模型状态"""
        try:
            manager = self._get_model_manager()
            models = manager.list_models()

            status = {
                "funasr_available": self.is_available(),
                "models": models,
                "auto_download": self.auto_download
            }

            return status
        except Exception as e:
            return {"error": str(e)}