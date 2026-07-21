import azure.cognitiveservices.speech as speechsdk
import os
import time
from pydub import AudioSegment
import logging
import json
import time
import uuid
import requests
import os
import logging
import difflib 
from typing import List
import random
from datetime import datetime
from langchain_core.tools import tool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

MAX_THREADS = 3


AZURE_SERVICE_REGION = os.getenv("AZURE_SERVICE_REGION","eastasia")
AZURE_SERVICE_KEY = os.getenv("AZURE_SERVICE_KEY")

def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir

class AzureTranscriber:
    def __init__(self, subscription_key = AZURE_SERVICE_KEY, service_region = AZURE_SERVICE_REGION, lang="en-US"): 
        # 注意：你的文案是英文，这里 lang 建议改为 "en-US"
        self.speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)
        self.speech_config.speech_recognition_language = lang
        # 请求 Azure 输出详细的时间戳信息
        self.speech_config.request_word_level_timestamps() 

    def convert_to_standard_wav(self, input_path):
        """保持原有的音频预处理逻辑不变"""
        logger.info(f"正在预处理音频: {input_path}")
        filename_only = os.path.splitext(os.path.basename(input_path))[0]
        data_dir = get_data_dir()
        temp_dir = os.path.join(data_dir,'result_video','clip_audio')
        os.makedirs(temp_dir, exist_ok=True)
        output_wav_path = os.path.join(temp_dir,f"Azure_decode_{filename_only}.wav")
        
        try:
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            audio.export(output_wav_path, format="wav", codec="pcm_s16le")
            return output_wav_path
        except Exception as e:
            logger.error(f"转码失败: {e}")
            return None

    def file_to_text(self, audio_file_path):
        """
        核心修改点：
        1. 将时间戳转换为秒 (seconds)
        2. 返回更纯净的列表供算法使用
        """
        standard_wav_path = self.convert_to_standard_wav(audio_file_path)
        if not standard_wav_path:
            return []

        audio_config = speechsdk.AudioConfig(filename=standard_wav_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)

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
                
                logger.info(f"识别片段: {evt.result.text} ({start_seconds:.2f}s - {end_seconds:.2f}s)")
                
                results.append({
                    "text": evt.result.text,
                    "start_time": start_seconds,
                    "duration": duration_seconds,
                    "end_time": end_seconds
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
            
        return results

    def _get_audio_duration(self, audio_path):
        """
        获取音频文件的真实物理时长（秒）
        """
        try:
            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return 0.0
            
            # 使用 pydub 读取音频时长
            audio = AudioSegment.from_file(audio_path)
            return audio.duration_seconds
        except Exception as e:
            logger.error(f"无法获取音频时长: {e}")
            # 如果获取失败，返回一个默认值或者抛出异常
            return 0.0


    def align_script_with_audio(self, script_json, audio_path):
        """
        增强版对齐算法：包含贪婪匹配 + 比例估算兜底
        """
        # --- 修复 1: 处理传入数据可能是字符串或非标准JSON的情况 (解决 TypeError) ---
        if isinstance(script_json, str):
            try:
                script_json = json.loads(script_json)
            except json.JSONDecodeError:
                # 如果是纯文本，尝试按行分割
                script_json = [{"original_text": line} for line in script_json.split('\n') if line.strip()]

        # 确保 script_json 里的 item 都是字典
        validated_script = []
        for item in script_json:
            if isinstance(item, str):
                validated_script.append({"original_text": item})
            elif isinstance(item, dict):
                validated_script.append(item)
        script_json = validated_script
        # -----------------------------------------------------------------------

        # --- 修复 2: 获取音频真实时长 (解决 total_duration=10.0 问题) ---
        real_duration = self._get_audio_duration(audio_path)
        if real_duration <= 0:
            logger.warning("音频时长获取失败，将使用默认兜底时长 10s (可能会导致声画不同步)")
            real_duration = 10.0 # 仅作为最后的无奈之举

        # 1. 获取语音识别的原始片段
        raw_segments = self.file_to_text(audio_path)
        
        # 如果完全没识别到 (ASR失败)，直接使用真实时长进行估算
        if not raw_segments:
            logger.warning("ASR未识别到内容，使用全时长估算模式")
            return self._fallback_estimation(script_json, total_duration=real_duration)

        # 获取音频总时长 (取 ASR 结束时间 和 物理文件时长 的较大值)
        # 有时候 ASR 可能会丢掉最后几秒的静音，所以最好用 real_duration
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
        # 传入真实时长
        return self._fix_zero_durations(script_json, total_audio_duration)
    

    def _fix_zero_durations(self, script_json, total_duration):
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
        logger.info("正在使用字数比例进行...")
        
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

    def _clean_text(self, text):
        return "".join([c for c in text if c.isalnum()]).lower()
    
    def _fallback_estimation(self, script_json, total_duration):
        # 纯估算逻辑，同 _fix_zero_durations
        return self._fix_zero_durations(script_json, total_duration)


@tool
def asr_audio_file(audio_file_path):
    """
    将音频文件转换为文本
    :param audio_file_path: 音频文件路径
    :return: 识别结果列表
    """
    transcriber = AzureTranscriber()
    return transcriber.file_to_text(audio_file_path)


def save_json_to_file(data):
    """
    将JSON数据保存到文件
    input:
        data: 要保存的JSON数据
        filename: 文件名（可选，不提供则自动生成）
        directory: 目录路径（可选，不提供则使用默认目录）
    return:
        保存的文件路径
    """
    data_dir = get_data_dir()
    directory = os.path.join(data_dir, 'videoscript_json')
    
    # 创建目录（如果不存在）
    os.makedirs(directory, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{timestamp}.json"
    
    file_path = os.path.join(directory, filename)
    
    # 写入JSON文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    logger.info(f"JSON数据已保存到: {file_path}")
    relative_path = os.path.relpath(file_path, data_dir)
    return relative_path



@tool
def get_script_text_time(json_file: str, audio_path: str, language: str = 'en-US'):
    """
    用于生成检索关键词和时间长度
    input:
        json_file: 文案文件相对路劲
        audio_path: 视频文案对应的语音文件
        language: 根据文案语言来判断，英语：'en-US',中文：'zh-CN'
    return: 
        返回一个包含关键词和时间长度的列表
    """
    data_dir = get_data_dir()
    json_file_path = os.path.join(data_dir, json_file)
    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_all_date = json.load(f)
        json_data = json_all_date['parsed_result']

    audio_path = os.path.join(data_dir,audio_path)
    transcriber = AzureTranscriber(lang=language)
    script_json = transcriber.align_script_with_audio(json_data,audio_path)
    durations = [item['duration'] for item in script_json]
    keywords = [random.choice(item['search_keywords']) for item in script_json]
    
    # new_json_data = {
    #     "keywords": keywords,
    #     "durations": durations,
    # }
    # new_json_data_path = save_json_to_file(new_json_data)
    # relative_path = os.path.relpath(new_json_data_path, data_dir)
    new_json_data = []
    for key,dura in zip(keywords,durations):
        new_json_data.append({
            "keyword": key,
            "duration": dura,
        })
    # return new_json_data
    return {
            "tool_return":[{
                "keywards_with_duration": new_json_data,
                "describe": """素材检索的关键词列表，和时间列表，用于后续视频检索的时候使用，
                列表中的每一个元素都是一个字典，字典中包含关键词列表和时间长度，一个时间长度对应一个关键词列表，以防止有的关键词检索不到素材"""
            }]
        }



def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir


if __name__ == "__main__":
    audio_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\seo_video_generate\data\result_video\测试12.18\audio_result\01d043ff-05eb-4f2c-96ee-898ae1f5cf98.mp3"
    json_data = [{'index': 0, 'original_text': 'Struggling to wake up early? Let me fix that.', 'search_keywords': ['tired person in bed', 'sunlight through curtains', 'alarm clock ringing', 'person rubbing eyes', 'morning bedroom scene'], 'shot_type': 'Medium Shot'}, {'index': 1, 'original_text': 'Step one: STOP snoozing your alarm—seriously.', 'search_keywords': ['hand reaching for alarm clock', 'person hitting snooze button', 'frustrated face in bed', 'early morning light'], 'shot_type': 'Close-up'}, {'index': 2, 'original_text': 'Step two: Prep something exciting for the morning. Coffee? A playlist? Pancakes?', 'search_keywords': ['coffee brewing in kitchen', 'stack of pancakes with syrup', 'headphones on table', 'person smiling with breakfast', 'playlist on smartphone'], 'shot_type': 'Wide Shot'}, {'index': 3, 'original_text': 'And step three: Go to bed like you actually care about tomorrow.', 'search_keywords': ['person setting alarm on phone', 'cozy bedroom with dim light', 'person reading in bed', 'glass of water on nightstand', 'peaceful sleeping face'], 'shot_type': 'Medium Shot'}, {'index': 4, 'original_text': "Early mornings don't suck—bad habits do. Change yours!", 'search_keywords': ['happy person stretching in morning light', 'motivational sunrise', 'person jogging at sunrise', 'energetic morning routine', 'bright room with sunlight'], 'shot_type': 'Timelapse'}]
    content = """Struggling to wake up early? Let me fix that. Step one: STOP snoozing your alarm—seriously. Step two: Prep something exciting for the morning. Coffee? A playlist? Pancakes? And step three: Go to bed like you actually care about tomorrow. Early mornings don't suck—bad habits do. Change yours!"""
    # transcriber = AzureTranscriber()
    # script_json = transcriber.align_script_with_audio(json_data,audio_path)
    script_json,durations = get_script_text_time(json_data,audio_path)
    print('script_json',script_json,'durations',durations)

