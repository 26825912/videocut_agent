"""
统一语音处理接口
提供语音识别(ASR)和语音合成(TTS)的统一调用接口
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceAPI:
    """
    统一语音处理API

    架构说明:
    - ASR (语音识别): 运行在 FunASR Docker 容器中，通过 HTTP 调用
    - TTS (语音合成): 运行在 GPT-SoVITS Docker 容器中，通过 HTTP 调用
    """

    def __init__(
        self,
        asr_api_url: str = "http://127.0.0.1:8001",
        tts_api_url: str = "http://127.0.0.1:9880"
    ):
        """
        初始化语音处理API

        Args:
            asr_api_url: FunASR服务地址
            tts_api_url: GPT-SoVITS服务地址
        """
        self.asr_api_url = asr_api_url
        self.tts_api_url = tts_api_url
        self._tts_loaded = False

    # ==================== 语音识别 (ASR) ====================

    def speech_to_text(
        self,
        audio_file: str,
        provider: str = "funasr",
        language: str = "zh"
    ) -> List[Dict[str, Any]]:
        """
        语音转文字 (ASR)

        运行环境: 通过 HTTP 调用 FunASR Docker 服务

        Args:
            audio_file: 音频文件路径（相对或绝对路径）
            provider: ASR提供商 (funasr, azure, whisperx)
            language: 语言代码 (zh, en, ja, ko)

        Returns:
            识别结果列表，格式:
            [
                {
                    "text": "识别的文本",
                    "start_time": 0.0,
                    "end_time": 2.5,
                    "duration": 2.5
                },
                ...
            ]

        示例:
            >>> api = VoiceAPI()
            >>> result = api.speech_to_text("audio.wav")
            >>> print(result[0]['text'])
        """
        try:
            import requests

            # 转换为绝对路径
            if not os.path.isabs(audio_file):
                data_dir = self._get_data_dir()
                audio_file = os.path.join(data_dir, audio_file)

            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"音频文件不存在: {audio_file}")

            logger.info(f"开始语音识别: {audio_file} (provider={provider})")

            # 调用 FunASR Docker 服务
            asr_url = self.asr_api_url.rstrip('/') + '/asr'

            with open(audio_file, 'rb') as f:
                files = {'file': (os.path.basename(audio_file), f, 'audio/wav')}
                data = {
                    'language': language,
                    'provider': provider
                }

                response = requests.post(asr_url, files=files, data=data, timeout=300)

            if response.status_code != 200:
                raise RuntimeError(f"ASR服务请求失败: {response.status_code} {response.text}")

            result_data = response.json()

            if not result_data.get('success'):
                raise RuntimeError(f"ASR识别失败: {result_data}")

            segments = result_data.get('segments', [])
            logger.info(f"识别完成，共 {len(segments)} 个片段")

            return segments

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "无法连接到 FunASR 服务！\n"
                "请确保 Docker 服务已启动:\n"
                "  cd videocut_agent/docker_services\n"
                "  docker-compose up -d funasr"
            )
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            raise

    # ==================== 语音合成 (TTS) ====================

    def text_to_speech(
        self,
        text: str,
        voice_name: str = "EnergeticMale1",
        speed: float = 1.0,
        volume: float = 0.0,
        output_file: Optional[str] = None,
        use_local: bool = True
    ) -> str:
        """
        文字转语音 (TTS)

        运行环境:
        - use_local=True: GPT-SoVITS Docker 容器 (通过HTTP调用)
        - use_local=False: Fish Audio API (需要API key)

        Args:
            text: 要合成的文本
            voice_name: 语音名称 (EnergeticMale1, EnergeticMale2, 小辉)
            speed: 语速 (0.5-2.0)
            volume: 音量 (-10到10)
            output_file: 输出文件路径（可选，为空则自动生成）
            use_local: 是否使用本地GPT-SoVITS (推荐)

        Returns:
            生成的音频文件相对路径

        示例:
            >>> api = VoiceAPI()
            >>> audio_path = api.text_to_speech("你好世界")
            >>> print(f"音频已保存: {audio_path}")
        """
        try:
            # 延迟导入
            if not self._tts_loaded:
                from tools.tts_tools import text_to_speech_tool
                self.text_to_speech_tool = text_to_speech_tool
                self._tts_loaded = True
                logger.info("TTS工具已加载")

            # 检查服务状态
            if use_local:
                if not self._check_tts_service():
                    raise RuntimeError(
                        "GPT-SoVITS服务未运行！\n"
                        "请先启动 Docker 服务:\n"
                        "  cd videocut_agent/docker_services\n"
                        "  docker-compose up -d gpt-sovits"
                    )

            logger.info(f"开始语音合成: {text[:50]}... (voice={voice_name}, use_local={use_local})")

            result = self.text_to_speech_tool.invoke({
                "text": text,
                "voice_name": voice_name,
                "speed": speed,
                "volume": volume,
                "use_local": use_local
            })

            logger.info(f"合成完成: {result}")
            return result

        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            raise

    # ==================== 工具方法 ====================

    def _check_tts_service(self) -> bool:
        """检查GPT-SoVITS服务是否运行"""
        try:
            import requests
            response = requests.get(self.tts_api_url, timeout=2)
            return response.status_code == 200
        except:
            return False

    def _check_asr_service(self) -> bool:
        """检查FunASR服务是否运行"""
        try:
            import requests
            response = requests.get(f"{self.asr_api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _get_data_dir(self) -> str:
        """获取数据目录"""
        current_dir = Path(__file__).parent.parent
        return str(current_dir / "data")

    def get_available_voices(self) -> List[str]:
        """
        获取可用的语音列表

        Returns:
            语音名称列表
        """
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "models"))
            from gpt_sovits_client import GPTSoVITSAdapter

            adapter = GPTSoVITSAdapter()
            return adapter.get_available_voices()
        except Exception as e:
            logger.warning(f"获取语音列表失败: {e}")
            return ["EnergeticMale1", "EnergeticMale2", "小辉"]


# ==================== 便捷函数 ====================

# 全局API实例
_api_instance = None

def get_voice_api() -> VoiceAPI:
    """获取语音API单例"""
    global _api_instance
    if _api_instance is None:
        _api_instance = VoiceAPI()
    return _api_instance


def asr(audio_file: str, provider: str = "funasr") -> List[Dict[str, Any]]:
    """
    快捷函数: 语音识别

    Args:
        audio_file: 音频文件路径
        provider: ASR提供商

    Returns:
        识别结果列表
    """
    api = get_voice_api()
    return api.speech_to_text(audio_file, provider=provider)


def tts(text: str, voice: str = "EnergeticMale1", speed: float = 1.0) -> str:
    """
    快捷函数: 语音合成

    Args:
        text: 要合成的文本
        voice: 语音名称
        speed: 语速

    Returns:
        音频文件路径
    """
    api = get_voice_api()
    return api.text_to_speech(text, voice_name=voice, speed=speed, use_local=True)


# ==================== 示例代码 ====================

if __name__ == "__main__":
    # 示例1: 语音识别
    print("=" * 60)
    print("示例1: 语音识别")
    print("=" * 60)

    api = VoiceAPI()

    # 假设有音频文件
    # result = api.speech_to_text("test_audio.wav")
    # for segment in result:
    #     print(f"[{segment['start_time']:.2f}s - {segment['end_time']:.2f}s] {segment['text']}")

    print("\n" + "=" * 60)
    print("示例2: 语音合成")
    print("=" * 60)

    # 检查服务状态
    if api._check_tts_service():
        print("✓ GPT-SoVITS服务正常")

        # 合成语音
        # audio_path = api.text_to_speech("这是一个测试", voice_name="EnergeticMale1")
        # print(f"音频已生成: {audio_path}")
    else:
        print("✗ GPT-SoVITS服务未运行")
        print("\n请先启动服务:")
        print("  运行: videocut_agent/models/start_gpt_sovits.bat")

    print("\n" + "=" * 60)
    print("示例3: 使用便捷函数")
    print("=" * 60)
    print("""
    # 语音识别
    result = asr("audio.wav")

    # 语音合成
    audio_path = tts("你好世界", voice="EnergeticMale1", speed=1.2)
    """)
