"""
ASR (Automatic Speech Recognition) 抽象基类和工厂类
支持多种语音识别引擎的统一接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ASRProvider(Enum):
    """ASR 提供商枚举"""
    FUNASR = "funasr"
    AZURE = "azure"
    WHISPERX = "whisperx"
    OPENAI = "openai"
    TENCENT = "tencent"

class BaseTranscriber(ABC):
    """
    ASR转录器抽象基类
    定义统一的语音识别接口，支持多种实现
    """

    def __init__(self, language: str = "zh-cn", **kwargs):
        """
        初始化转录器

        Args:
            language: 语言代码 ("zh-cn", "en-us", "ja", 等)
            **kwargs: 各实现特定的参数
        """
        self.language = language
        self.config = kwargs

    @abstractmethod
    def file_to_text(self, audio_file_path: str) -> List[Dict[str, Any]]:
        """
        将音频文件转换为带时间戳的文本

        Args:
            audio_file_path: 音频文件路径

        Returns:
            List[Dict]: 格式为 [{"text": str, "start_time": float, "end_time": float, "duration": float}]
        """
        pass

    @abstractmethod
    def align_script_with_audio(self, script_json: Any, audio_path: str) -> List[Dict[str, Any]]:
        """
        将脚本与音频进行时间对齐

        Args:
            script_json: 脚本数据
            audio_path: 音频文件路径

        Returns:
            List[Dict]: 对齐后的脚本，包含时间戳信息
        """
        pass

    def convert_to_standard_wav(self, input_path: str) -> Optional[str]:
        """
        音频格式标准化 (可选重写)

        Args:
            input_path: 输入音频路径

        Returns:
            Optional[str]: 标准化后的WAV文件路径，失败返回None
        """
        from pydub import AudioSegment

        logger.info(f"预处理音频: {input_path}")
        filename_only = os.path.splitext(os.path.basename(input_path))[0]

        # 获取数据目录
        data_dir = self._get_data_dir()
        temp_dir = os.path.join(data_dir, 'result_video', 'clip_audio')
        os.makedirs(temp_dir, exist_ok=True)

        output_wav_path = os.path.join(temp_dir, f"{self.__class__.__name__}_decode_{filename_only}.wav")

        try:
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            audio.export(output_wav_path, format="wav", codec="pcm_s16le")
            return output_wav_path
        except Exception as e:
            logger.error(f"音频转码失败: {e}")
            return None

    def _get_data_dir(self) -> str:
        """获取数据目录"""
        data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(data_dir, 'data')

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            from pydub import AudioSegment
            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return 0.0
            audio = AudioSegment.from_file(audio_path)
            return audio.duration_seconds
        except Exception as e:
            logger.error(f"获取音频时长失败: {e}")
            return 0.0


class ASRConfig:
    """ASR配置管理类"""

    DEFAULT_CONFIG = {
        "provider": "funasr",  # 默认使用 FunASR
        "fallback_provider": "azure",  # 备用提供商
        "language": "zh-cn",
        "providers": {
            "funasr": {
                "model_size": "large",
                "use_gpu": True,
                "batch_size": 1
            },
            "azure": {
                "subscription_key": None,  # 从环境变量获取
                "service_region": "eastasia",
                "request_word_level_timestamps": True
            },
            "whisperx": {
                "model_size": "base",
                "device": "auto",
                "compute_type": "float32"
            },
            "openai": {
                "api_key": None,  # 从环境变量获取
                "model": "whisper-1"
            },
            "tencent": {
                "secret_id": None,
                "secret_key": None,
                "region": "ap-beijing"
            }
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，默认使用项目根目录下的 asr_config.json
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, 'asr_config.json')

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合并默认配置和用户配置
                config = self.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
            else:
                logger.info(f"配置文件不存在，使用默认配置: {self.config_path}")
                self._save_default_config()
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"配置加载失败: {e}，使用默认配置")
            return self.DEFAULT_CONFIG.copy()

    def _save_default_config(self):
        """保存默认配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            logger.info(f"已创建默认配置文件: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def get_provider(self) -> str:
        """获取当前提供商"""
        return self.config.get("provider", "funasr")

    def get_fallback_provider(self) -> str:
        """获取备用提供商"""
        return self.config.get("fallback_provider", "azure")

    def get_language(self) -> str:
        """获取语言设置"""
        return self.config.get("language", "zh-cn")

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取指定提供商的配置"""
        return self.config.get("providers", {}).get(provider, {})

    def set_provider(self, provider: str):
        """设置当前提供商"""
        if provider in ASRProvider.__members__.values() or provider in [e.value for e in ASRProvider]:
            self.config["provider"] = provider
            self._save_config()
        else:
            raise ValueError(f"不支持的提供商: {provider}")

    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")


class ASRFactory:
    """ASR工厂类，负责创建不同的转录器实例"""

    _transcribers = {}  # 转录器类注册表

    @classmethod
    def register_transcriber(cls, provider: str, transcriber_class: type):
        """
        注册转录器类

        Args:
            provider: 提供商名称
            transcriber_class: 转录器类
        """
        cls._transcribers[provider] = transcriber_class
        logger.info(f"注册转录器: {provider} -> {transcriber_class.__name__}")

    @classmethod
    def create_transcriber(cls, provider: Optional[str] = None, config: Optional[ASRConfig] = None, **kwargs) -> BaseTranscriber:
        """
        创建转录器实例

        Args:
            provider: 指定提供商，不指定则使用配置中的默认值
            config: ASR配置实例，不指定则创建新的
            **kwargs: 额外参数

        Returns:
            BaseTranscriber: 转录器实例
        """
        if config is None:
            config = ASRConfig()

        if provider is None:
            provider = config.get_provider()

        if provider not in cls._transcribers:
            logger.warning(f"提供商 {provider} 未注册，尝试动态导入")
            cls._try_import_transcriber(provider)

        if provider not in cls._transcribers:
            # 尝试使用备用提供商
            fallback_provider = config.get_fallback_provider()
            logger.warning(f"提供商 {provider} 不可用，尝试使用备用提供商: {fallback_provider}")

            if fallback_provider not in cls._transcribers:
                cls._try_import_transcriber(fallback_provider)

            if fallback_provider in cls._transcribers:
                provider = fallback_provider
            else:
                raise ValueError(f"提供商 {provider} 和备用提供商 {fallback_provider} 都不可用")

        transcriber_class = cls._transcribers[provider]
        provider_config = config.get_provider_config(provider)

        # 合并配置
        merged_kwargs = {
            "language": config.get_language(),
            **provider_config,
            **kwargs
        }

        logger.info(f"创建转录器: {provider} ({transcriber_class.__name__})")
        return transcriber_class(**merged_kwargs)

    @classmethod
    def _try_import_transcriber(cls, provider: str):
        """尝试动态导入转录器"""
        try:
            if provider == "funasr":
                from .funasr_transcriber import FunASRTranscriber
                cls.register_transcriber("funasr", FunASRTranscriber)
            elif provider == "azure":
                from .azure_transcriber import AzureTranscriber
                cls.register_transcriber("azure", AzureTranscriber)
            elif provider == "whisperx":
                from .whisperx_transcriber import WhisperXTranscriber
                cls.register_transcriber("whisperx", WhisperXTranscriber)
            elif provider == "openai":
                from .openai_transcriber import OpenAITranscriber
                cls.register_transcriber("openai", OpenAITranscriber)
            elif provider == "tencent":
                from .tencent_transcriber import TencentTranscriber
                cls.register_transcriber("tencent", TencentTranscriber)
        except ImportError as e:
            logger.warning(f"导入 {provider} 转录器失败: {e}")

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """获取可用的提供商列表"""
        # 尝试导入所有已知的提供商
        for provider in ["funasr", "azure", "whisperx", "openai", "tencent"]:
            if provider not in cls._transcribers:
                cls._try_import_transcriber(provider)

        return list(cls._transcribers.keys())

    @classmethod
    def switch_provider(cls, provider: str, config_path: Optional[str] = None):
        """
        切换默认提供商

        Args:
            provider: 新的提供商
            config_path: 配置文件路径
        """
        config = ASRConfig(config_path)
        config.set_provider(provider)
        logger.info(f"已切换默认提供商为: {provider}")


# 便捷函数
def get_transcriber(provider: Optional[str] = None, **kwargs) -> BaseTranscriber:
    """
    获取转录器实例的便捷函数

    Args:
        provider: 指定提供商
        **kwargs: 额外参数

    Returns:
        BaseTranscriber: 转录器实例
    """
    return ASRFactory.create_transcriber(provider=provider, **kwargs)


def switch_asr_provider(provider: str):
    """
    切换ASR提供商的便捷函数

    Args:
        provider: 新的提供商名称
    """
    ASRFactory.switch_provider(provider)


def list_asr_providers() -> List[str]:
    """
    列出所有可用的ASR提供商

    Returns:
        List[str]: 提供商列表
    """
    return ASRFactory.get_available_providers()