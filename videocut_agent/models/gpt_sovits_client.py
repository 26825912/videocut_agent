"""
GPT-SoVITS本地推理客户端
支持通过API调用本地部署的GPT-SoVITS服务进行语音合成
"""

import os
import requests
import logging
from typing import Optional, List
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class GPTSoVITSClient:
    """GPT-SoVITS本地推理客户端"""

    def __init__(self, api_url: str = "http://127.0.0.1:9880", reference_audio_dir: Optional[str] = None):
        """
        初始化GPT-SoVITS客户端

        Args:
            api_url: GPT-SoVITS API服务地址，默认 http://127.0.0.1:9880
            reference_audio_dir: 参考音频文件目录
        """
        self.api_url = api_url.rstrip('/')
        self.reference_audio_dir = reference_audio_dir or self._get_default_reference_dir()

    def _get_default_reference_dir(self) -> str:
        """获取默认参考音频目录"""
        # 指向data/clone_voice目录
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "data" / "clone_voice")

    def text_to_speech(
        self,
        text: str,
        ref_audio_path: str,
        prompt_text: str = "",
        prompt_lang: str = "zh",
        text_lang: str = "zh",
        speed_factor: float = 1.0,
        temperature: float = 1.0,
        top_k: int = 15,
        top_p: float = 1.0,
        output_path: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        文本转语音

        Args:
            text: 要合成的文本
            ref_audio_path: 参考音频路径（绝对路径或相对于reference_audio_dir）
            prompt_text: 参考音频对应的文本
            prompt_lang: 参考音频的语言 (zh, en, ja, ko等)
            text_lang: 要合成文本的语言
            speed_factor: 语速因子 (0.5-2.0)
            temperature: 采样温度
            top_k: top_k采样
            top_p: top_p采样
            output_path: 输出文件路径（可选）
            **kwargs: 其他参数

        Returns:
            bytes: 音频数据
        """
        # 处理参考音频路径
        if not os.path.isabs(ref_audio_path):
            ref_audio_path = os.path.join(self.reference_audio_dir, ref_audio_path)

        if not os.path.exists(ref_audio_path):
            raise FileNotFoundError(f"参考音频文件不存在: {ref_audio_path}")

        # 准备请求数据
        request_data = {
            "text": text,
            "text_lang": text_lang,
            "ref_audio_path": ref_audio_path,
            "prompt_text": prompt_text,
            "prompt_lang": prompt_lang,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "speed_factor": speed_factor,
            "text_split_method": kwargs.get("text_split_method", "cut5"),
            "batch_size": kwargs.get("batch_size", 1),
            "streaming_mode": False,
        }

        # 添加其他可选参数
        for key in ["aux_ref_audio_paths", "batch_threshold", "split_bucket",
                    "fragment_interval", "seed", "parallel_infer", "repetition_penalty"]:
            if key in kwargs:
                request_data[key] = kwargs[key]

        # 发送请求
        try:
            logger.info(f"GPT-SoVITS API请求开始")
            logger.info(f"请求URL: {self.api_url}/tts")
            logger.info(f"文本: '{text[:50]}...', 参考音频: {os.path.basename(ref_audio_path)}, 语速: {speed_factor}")

            response = requests.post(
                f"{self.api_url}/tts",
                json=request_data,
                timeout=300
            )
            response.raise_for_status()

            audio_data = response.content
            logger.info(f"GPT-SoVITS API响应成功，音频大小: {len(audio_data)} bytes")

            # 保存到文件
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"音频已保存到: {output_path}")

            return audio_data

        except requests.exceptions.RequestException as e:
            logger.error(f"GPT-SoVITS API请求失败: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"错误详情: {e.response.text}")
            raise RuntimeError(f"GPT-SoVITS API请求失败: {e}")

    def check_service(self) -> bool:
        """
        检查GPT-SoVITS服务是否运行

        Returns:
            bool: 服务是否可用
        """
        try:
            response = requests.get(f"{self.api_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"GPT-SoVITS服务不可用: {e}")
            return False


# 兼容性接口：模拟Fish Audio API的接口
class GPTSoVITSAdapter:
    """
    适配器类，提供与Fish Audio API兼容的接口
    用于无缝替换现有的Fish Audio TTS客户端
    """

    def __init__(self, api_url: str = "http://127.0.0.1:9880", voice_mapping_path: Optional[str] = None):
        """
        初始化适配器

        Args:
            api_url: GPT-SoVITS API地址
            voice_mapping_path: 语音映射配置文件路径
        """
        self.client = GPTSoVITSClient(api_url)
        self.voice_mapping_path = voice_mapping_path or self._get_default_voice_mapping()
        self.voice_mapping = self._load_voice_mapping()

    def _get_default_voice_mapping(self) -> str:
        """获取默认voice mapping路径"""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "data" / "clone_voice" / "voice_mapping_gpt_sovits.json")

    def _load_voice_mapping(self) -> dict:
        """加载语音映射配置"""
        import json
        try:
            if os.path.exists(self.voice_mapping_path):
                with open(self.voice_mapping_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"语音映射文件不存在: {self.voice_mapping_path}")
                return {}
        except Exception as e:
            logger.error(f"加载语音映射失败: {e}")
            return {}

    def text_to_speech_simple(
        self,
        text: str,
        voice_name: str,
        speed: float = 1.0,
        volume: float = 0.0,
        output_path: Optional[str] = None,
        silence_duration: float = 0.0
    ) -> bytes:
        """
        简单的文本转语音接口（兼容Fish Audio接口）

        Args:
            text: 要合成的文本
            voice_name: 语音名称（从voice_mapping中查找）
            speed: 语速 (0.5-2.0)
            volume: 音量（GPT-SoVITS不直接支持，忽略此参数）
            output_path: 输出路径
            silence_duration: 静音时长（需要后处理添加）

        Returns:
            bytes: 音频数据
        """
        # 从映射中获取参考音频和提示文本
        if voice_name not in self.voice_mapping:
            available = list(self.voice_mapping.keys())
            raise ValueError(f"语音 '{voice_name}' 不存在。可用语音: {available}")

        voice_config = self.voice_mapping[voice_name]
        ref_audio = voice_config["audio"]
        prompt_text = voice_config.get("text", "")
        prompt_lang = voice_config.get("lang", "zh")

        # 调用GPT-SoVITS
        audio_data = self.client.text_to_speech(
            text=text,
            ref_audio_path=ref_audio,
            prompt_text=prompt_text,
            prompt_lang=prompt_lang,
            text_lang=prompt_lang,
            speed_factor=speed,
            output_path=output_path
        )

        # 如果需要添加静音段
        if silence_duration > 0 and output_path:
            self._add_silence(output_path, silence_duration)

        return audio_data

    def _add_silence(self, audio_path: str, silence_duration: float):
        """在音频末尾添加静音"""
        try:
            import soundfile as sf
            import numpy as np

            # 读取音频
            audio, sr = sf.read(audio_path)

            # 创建静音段
            silence_samples = int(silence_duration * sr)
            if audio.ndim == 1:
                silence = np.zeros(silence_samples, dtype=audio.dtype)
            else:
                silence = np.zeros((silence_samples, audio.shape[1]), dtype=audio.dtype)

            # 合并音频
            combined = np.concatenate([audio, silence])

            # 保存
            sf.write(audio_path, combined, sr)
            logger.info(f"已添加 {silence_duration}s 静音")

        except Exception as e:
            logger.warning(f"添加静音失败: {e}")

    def get_available_voices(self) -> List[str]:
        """获取可用的语音列表"""
        return list(self.voice_mapping.keys())
