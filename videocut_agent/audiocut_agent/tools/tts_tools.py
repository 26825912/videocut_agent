import json
import os
import base64
import requests
import msgpack
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
# import librosa
import soundfile as sf
import numpy as np
import io 
import logging
import time
import uuid
from tools.videocut_methods import AudioCutMethods
import uuid
from tools.utils import get_data_dir
import sys
from pathlib import Path

from langchain_core.tools import tool

from django.conf import settings

# 添加models目录到路径以导入gpt_sovits_client
models_dir = Path(__file__).parent.parent.parent / "models"
sys.path.insert(0, str(models_dir))
from gpt_sovits_client import GPTSoVITSAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir

#加载.env文件中的参数配置
from dotenv import load_dotenv
load_dotenv()

TTS_API_URL = os.getenv("TTS_API_URL", "http://10.2.42.21:8000/v1/tts")
TTS_API_TOKEN = os.getenv("TTS_API_TOKEN", "be058c61e46e4bc6811c63fab7dd4a74")
voice_map_json = os.path.join(get_data_dir(), 'clone_voice', 'voice_mapping.json')
voice_data_dir = os.path.join(get_data_dir(), 'clone_voice')

class TTSClient:
    """Text-to-Speech client for Fish Audio API"""
    
    def __init__(self, api_url: str = TTS_API_URL, auth_token: str = TTS_API_TOKEN):
        """
        Initialize TTS client
        
        Args:
            api_url: The TTS API endpoint URL (optional, defaults from env)
            auth_token: Bearer authentication token
        """
        # 优先使用传入参数，其次使用全局Django settings，最后使用合理默认值
        self.api_url = api_url #or getattr(settings, 'TTS_API_URL', 'https://api.fish.audio/v1/tts')
        self.auth_token = auth_token #or getattr(settings, 'TTS_API_TOKEN', '')
        self.voice_mapping_path = voice_map_json#Path(__file__).parent.parent / "data" / "clone_voice" / "voice_mapping.json"
        self.voice_data_dir = voice_data_dir#Path(__file__).parent.parent / "data" / "clone_voice"
        
    def load_voice_mapping(self) -> Dict[str, Any]:
        """Load voice mapping configuration from JSON file"""
        try:
            with open(self.voice_mapping_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Voice mapping file not found: {self.voice_mapping_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in voice mapping file: {e}")
    
    def load_audio_file(self, audio_filename: str) -> bytes:
        """Load audio file as bytes"""
        audio_path = os.path.join(self.voice_data_dir, audio_filename)
        try:
            with open(audio_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    def create_reference_audio(self, voice_name: str) -> Dict[str, Any]:
        """
        Create reference audio object for the specified voice
        
        Args:
            voice_name: Name of the voice from voice_mapping.json
            
        Returns:
            Reference audio object for MessagePack serialization
        """
        voice_mapping = self.load_voice_mapping()
        
        if voice_name not in voice_mapping:
            available_voices = list(voice_mapping.keys())
            raise ValueError(f"Voice '{voice_name}' not found. Available voices: {available_voices}")
        
        voice_config = voice_mapping[voice_name]
        audio_data = self.load_audio_file(voice_config["audio"])
        
        return {
            "audio": audio_data,
            "text": voice_config["text"]
        }
    
    def text_to_speech(
        self,
        text: str,
        voice_name: str,
        model: str = "s1",
        temperature: float = 0.1,
        top_p: float = 0.7,
        chunk_length: int = 200,
        normalize: bool = True,
        format: str = "mp3",
        sample_rate: Optional[int] = None,
        mp3_bitrate: int = 128,
        opus_bitrate: int = 32,
        latency: str = "normal",
        speed: float = 1.0,
        volume: float = 0.0
    ) -> bytes:
        """
        Convert text to speech using the Fish Audio API
        
        Args:
            text: Text to be converted to speech
            voice_name: Name of the voice from voice_mapping.json
            model: TTS model to use (speech-1.5, speech-1.6, s1)
            temperature: Controls randomness (0-1)
            top_p: Controls diversity (0-1)
            chunk_length: Chunk length (100-300)
            normalize: Whether to normalize speech
            format: Audio format (wav, pcm, mp3, opus)
            sample_rate: Sample rate for audio
            mp3_bitrate: MP3 bitrate (64, 128, 192)
            opus_bitrate: Opus bitrate (-1000, 24, 32, 48, 64)
            latency: Latency mode (normal, balanced)
            speed: Speech speed (0.5-2.0, default 1.0)
            volume: Speech volume (-10 to 10, default 0)
            
        Returns:
            Audio data as bytes
        """
        # Create reference audio
        reference_audio = self.create_reference_audio(voice_name)
        
        # Prepare request data
        request_data = {
            "text": text,
            "temperature": temperature,
            "top_p": top_p,
            "references": [reference_audio],
            "chunk_length": chunk_length,
            "normalize": normalize,
            "format": format,
            "mp3_bitrate": mp3_bitrate,
            "opus_bitrate": opus_bitrate,
            "latency": latency,
            "prosody": {
                "speed": speed,
                "volume": volume
            }
        }
        
        if sample_rate is not None:
            request_data["sample_rate"] = sample_rate
        
        # Serialize with MessagePack
        serialized_data = msgpack.packb(request_data)
        
        # Prepare headers
        headers = {
            "Content-Type": "application/msgpack",
            "model": model
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Make API request
        try:
            logger.info(f"TTS API请求开始")
            logger.info(f"请求URL: {self.api_url}")
            # 避免打印敏感信息
            _headers_safe = dict(headers)
            if 'Authorization' in _headers_safe:
                _headers_safe['Authorization'] = '***MASKED***'
            logger.info(f"请求头: {_headers_safe}")
            logger.info(f"请求参数: text='{text}', voice_name='{voice_name}', speed={speed}, volume={volume}, model='{model}', temperature={temperature}, top_p={top_p}, chunk_length={chunk_length}, normalize={normalize}, format='{format}', latency='{latency}'")
            
            response = requests.post(
                self.api_url,
                data=serialized_data,
                headers=headers,
                timeout=3000
            )
            response.raise_for_status()
            logger.info(f"TTS API响应成功: {response.status_code}, 音频大小: {len(response.content)} bytes")
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS API请求失败: {e}")
            raise RuntimeError(f"TTS API request failed: {e}")
    
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
        Simple text-to-speech conversion with default parameters
        
        Args:
            text: Text to convert to speech
            voice_name: Voice name from voice_mapping.json
            output_path: Optional path to save the generated audio
            speed: Speech speed (0.5-2.0, default 1.0)
            volume: Speech volume (-10 to 10, default 0)
            
        Returns:
            Audio data as bytes
        """
        assert output_path, "output_path 为空！"
        new_text = text + '.'
        audio_data = self.text_to_speech(new_text, voice_name, speed=speed, volume=volume)
        if silence_duration > 0:
            # y, sr = librosa.load(io.BytesIO(audio_data), sr=None)
            y, sr = sf.read(io.BytesIO(audio_data))
            silence_samples = int(silence_duration * sr)
            
            # 根据音频维度创建静音段
            if y.ndim == 1: 
                silence = np.zeros(silence_samples, dtype=y.dtype)
            else:  
                silence = np.zeros((silence_samples, y.shape[1]), dtype=y.dtype)
            combined_audio = np.concatenate([y, silence])
            
            try:
                with io.BytesIO(audio_data) as f:
                    info = sf.info(f)
                    subtype = info.subtype
                sf.write(output_path, combined_audio, sr, format=info.format, subtype=subtype)
                logger.info(f"Audio saved to: {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to save audio to {output_path}. Using default WAV format. Error: {e}")
                raise e
            
        else:
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            print(f"Audio saved to: {output_path}")
        
        return audio_data
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voice names"""
        voice_mapping = self.load_voice_mapping()
        return list(voice_mapping.keys())
    

def split_text_smartly(text: str, max_words: int = 65) -> List[str]:
    """
    辅助函数：将长文本按单词数和标点符号智能拆分
    """
    words = text.split()
    
    # 如果总单词数没超过限制，直接返回
    if len(words) <= max_words:
        return [text]
    
    # 寻找最佳分割点（从 max_words 往前倒推寻找标点）
    # 优先级：句子结束符 > 从句分隔符 > 强制空格分割
    split_index = max_words
    found_split_point = False
    
    # 1. 优先找句子结束符 (. ? ! 等)
    sentence_endings = ['.', '?', '!', '。', '？', '！']
    for i in range(max_words - 1, -1, -1):
        # 检查单词的最后一个字符是否是标点
        if any(words[i].endswith(p) for p in sentence_endings):
            split_index = i + 1
            found_split_point = True
            break
            
    # 2. 如果没找到，找逗号分号等
    if not found_split_point:
        clause_separators = [',', ';', ':', '，', '；', '：']
        for i in range(max_words - 1, -1, -1):
            if any(words[i].endswith(p) for p in clause_separators):
                split_index = i + 1
                found_split_point = True
                break
    
    # 3. 如果完全没有标点，强制在 max_words 处截断（split_index 保持默认值）
    part1 = " ".join(words[:split_index])
    remaining_text = " ".join(words[split_index:])
    
    # 如果剩余部分为空（防止死循环），返回当前部分
    if not remaining_text.strip():
        return [part1]
        
    return [part1] + split_text_smartly(remaining_text, max_words)


@tool
def text_to_speech_tool(json_file: str,
                        voice_name: str = "EnergeticMale1",
                        speed: float = 1.0,
                        volume: float = 0.0,
                        # save_file: str = None,
                        silence_duration: float = 0.0,
                        use_local: bool = False) -> bytes:
    """
    语音合成工具，可以将文本合成语音
    Args:
        json_file: 文案文件相对路径
        voice_name: 语音名称,有效的语音名称: ['EnergeticMale1', 'EnergeticMale2', '小辉']
        speed: 语音速度
        volume: 语音音量
        silence_duration: 静音时长,默认0.0
        use_local: 是否使用本地GPT-SoVITS模型,默认False使用Fish Audio API
    Returns:
        最终音频文件的相对路径
    """
    data_dir = get_data_dir()
    print(json_file)
    save_file = None
    if not save_file:
        final_output_dir = os.path.join(data_dir, 'result_video', 'clip_audio')
        os.makedirs(final_output_dir, exist_ok=True)
        final_output_filename = f"{uuid.uuid4()}.mp3"
        final_output_path = os.path.join(final_output_dir, final_output_filename)
    else:
        final_output_dir = os.path.join(data_dir, 'result_video', save_file, 'clip_audio')
        os.makedirs(final_output_dir, exist_ok=True)
        final_output_filename = f"{uuid.uuid4()}.mp3"
        final_output_path = os.path.join(final_output_dir, final_output_filename)
    
    json_file_path = os.path.join(data_dir, json_file)
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        text = data['full_script']
    # 使用递归函数将文本拆分成片段列表
    text_segments = split_text_smartly(text, max_words=40)
    
    logger.info(f" 文本长度过长，已拆分为 {len(text_segments)} 个片段进行合成。")

    # --- 如果不需要拆分 (只有一段)，直接调用原逻辑 ---
    if len(text_segments) == 1:
        if use_local:
            # 使用本地GPT-SoVITS
            gpt_sovits_client = GPTSoVITSAdapter()
            gpt_sovits_client.text_to_speech_simple(text,
                                                    voice_name,
                                                    speed,
                                                    volume,
                                                    final_output_path,
                                                    silence_duration)
        else:
            # 使用Fish Audio API
            tts_client = TTSClient()
            tts_client.text_to_speech_simple(text,
                                            voice_name,
                                            speed,
                                            volume,
                                            final_output_path,
                                            silence_duration)
        return os.path.relpath(final_output_path, data_dir)

    temp_audio_files = []
    if use_local:
        tts_client = GPTSoVITSAdapter()
    else:
        tts_client = TTSClient()
    
    try:
        for idx, segment in enumerate(text_segments):
            # 为每个片段生成一个临时文件路径
            temp_filename = f"temp_{uuid.uuid4()}_{idx}.mp3"
            temp_path = os.path.join(final_output_dir, temp_filename)
            
            logger.info(f" 正在合成第 {idx+1}/{len(text_segments)} 段 ({len(segment.split())} words)...")
            
            tts_client.text_to_speech_simple(segment, 
                                            voice_name, 
                                            speed, 
                                            volume, 
                                            temp_path, 
                                            silence_duration)
            
            if os.path.exists(temp_path):
                temp_audio_files.append(temp_path)
            else:
                raise Exception(f"Segment {idx} synthesis failed: File not found.")
            
        logger.info("所有片段合成完毕，开始合并音频...")
        relative_path = AudioCutMethods.concate_audios(temp_audio_files, save_file)
        return {
            "tool_return":[{
                "relative_path": relative_path,
                "describe": "语音合成结果的相对路径，该结果用于生成字幕文件，并加载到视频中"
            }]
        }
                
    except Exception as e:
        logger.error(f"长文本合成过程中出错: {e}")
        raise e
    

    finally:
        for temp_file in temp_audio_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"WARNING: 无法删除临时文件 {temp_file}: {e}")
    

# Example usage
if __name__ == "__main__":
    # # Initialize TTS client
    # tts_client = TTSClient()
    
    # # Get available voices
    # print("Available voices:", tts_client.get_available_voices())
    
    # # Example text-to-speech conversion
    # try:
    #     text = "Moreover."
    #     voice_name = "EnergeticMale1"
        
    #     print(f"Converting text to speech using voice: {voice_name}")
    #     audio_data = tts_client.text_to_speech_simple(
    #         text=text,
    #         voice_name=voice_name,
    #         output_path="../data/output_audio/output_speech3.mp3"
    #     )
    #     print(f"Generated audio size: {len(audio_data)} bytes")
        
    # except Exception as e:
    #     print(f"Error: {e}")
    save_file = '测试12.18'
    text = """Stop scrolling. guangzhou by car, let’s roll. keys, playlist, windows down. sunrise on baiyun mountain, city waking slow. dim sum melts, rice rolls glide, tea keeps pouring. canton tower in the mirror, pearl river ahead. cruise shamian’s shade, old trees, soft light. glide to huacheng square. Neon ready. shangxiajiu hums. claypot rice , laughter. night breeze, bridges glowing, city feels alive. guangzhou isn’t a stop.."""
    print(len(text.split(' ')))
    output_path = text_to_speech_tool(text)
    print(output_path)