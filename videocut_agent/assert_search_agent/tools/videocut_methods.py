import tempfile
from tqdm import tqdm
import concurrent.futures
import time
import json
from pathlib import Path
import random
import uuid
import shutil
import logging
import time 
import re
import os 
import requests
from urllib.parse import urlparse
from collections import namedtuple
import numpy as np
from typing import List, Dict, Any, Optional, Union
import pysubs2


# from langchain_core.tools import tool
from tools.video_ops_v2 import VideoOpsV2, AudioOpsV2,RemoveGreenScreen

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


class VideoCut:

    def __init__(self,video_path:str):
        self.video_path = video_path
        self.video_name = os.path.splitext(os.path.basename(video_path))[0]
        self.video_endswith = os.path.splitext(os.path.basename(video_path))[1]
        self.data_dir = get_data_dir()
        self.result_video_dir = os.path.join(self.data_dir,"result_video")
        self.add_subtitles_video_dir = os.path.join(self.result_video_dir,"add_subtitles_video")
        os.makedirs(self.add_subtitles_video_dir, exist_ok=True)
        
        self.add_bgm_video_dir = os.path.join(self.result_video_dir,"add_music_video")
        os.makedirs(self.add_bgm_video_dir, exist_ok=True)
    

    def add_hardsub_with_offset(self,subtitle_path:str,output_path:str = None, start_time = 0):
        """
        add_hardsub_with_offset 的 Docstring
        :param subtitle_path: 字幕文件夹路径
        :type subtitle_path: str
        :param output_path: 输出视频路径
        :type output_path: str
        :param start_time: 字幕开始的时间点（秒）。
                        例如 10.5，表示原字幕文件的 00:00:00 将对齐到视频的 00:00:10.5。
        """
        if output_path is None:
            output_path = os.path.join(self.add_subtitles_video_dir,f"{self.video_name}_{time.strftime('%Y%m%d%H%M%S')}.{self.video_endswith}")
        
        temp_sub_path = f"temp_subs_{uuid.uuid4().hex}.ass"
        try:
            logger.info(f"⏳ 正在处理字幕时间轴，偏移量: {start_time}秒")

            subs = pysubs2.load(subtitle_path)
            offset_ms = int(start_time * 1000)
            subs.shift(ms=offset_ms)
            subs.save(temp_sub_path, format="ass")

            logger.info(f"💾 临时字幕已生成: {temp_sub_path}")

            final_output = VideoOpsV2.add_hardsub(self.video_path, temp_sub_path, output_path)
            return final_output

        except Exception as e:
            logger.error(f"❌ 字幕处理或压制失败: {e}")
            raise e  

        finally:
            if os.path.exists(temp_sub_path):
                os.remove(temp_sub_path)
                logger.info(f"🗑️ 已清理临时字幕文件: {temp_sub_path}")
        
    
    def add_bg_music_with_offset(self,music_path:str,output_path:str = None, start_time = 0):
        """
        add_bg_music_with_offset 的 Docstring
        :param music_path: 背景音乐文件路径
        :type music_path: str
        :param output_path: 输出视频路径
        :type output_path: str
        :param start_time: 背景音乐开始的时间点（秒）。
                        例如 10.5，表示原背景音乐文件的 00:00:00 将对齐到视频的 00:00:10.5。
        """
        if output_path is None:
            output_path = os.path.join(self.add_subtitles_video_dir,f"{self.video_name}_{time.strftime('%Y%m%d%H%M%S')}.{self.video_endswith}")
        

###################################################################################################################################################
###################################################音频剪辑方法#####################################################################################

class AudioCutMethods:

    @staticmethod
    def clip_audio(input_path, start_time, duration,save_file = None):
        """
        裁剪音频片段
        :param input_path: 输入音频文件路径
        :param start_time: 裁剪开始时间（秒）
        :param duration: 裁剪时长（秒）
        :param save_file: 存储在result_video模块下的文件名
        """
        data_dir = get_data_dir()
        audio_name= os.path.splitext(os.path.basename(input_path))[0]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_audio")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_audio")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"{audio_name}_clip_{time.strftime('%Y%m%d%H%M%S')}.wav")
        logger.info(f"⏳ 正在裁剪音频: {input_path} -> {output_path}，开始时间: {start_time}秒，时长: {duration}秒")
        AudioOpsV2.clip_audio(input_path, start_time, duration, output_path)
        logger.info(f"✅ 音频裁剪完成: {output_path}")
        relative_path = os.path.relpath(output_path,start=data_dir)
        return relative_path
        
    
    @staticmethod
    def concate_audios(audio_files,save_file = None):
        """
        合并多个音频文件
        :param audio_files: 输入音频文件路径列表
        :param output_file: 输出合并后的音频文件路径
        :param save_file: 存储在result_video模块下的文件名
        """
        data_dir = get_data_dir()
        audio_name= os.path.splitext(os.path.basename(audio_files[0]))[0]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_audio")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_audio")

        os.makedirs(os.path.dirname(output_dir), exist_ok=True)
        output_file = os.path.join(output_dir,f"{audio_name}_concate_{time.strftime('%Y%m%d%H%M%S')}.wav")

        logger.info(f"⏳ 正在合并音频: {audio_files} -> {output_file}")
        AudioOpsV2.concatenate_audio_files(audio_files, output_file)
        logger.info(f"✅ 音频合并完成: {output_file}")
        relative_path = os.path.relpath(output_file,start=data_dir)
        return relative_path
        

    @staticmethod
    def adjust_audio_volume(input_path, save_file = None, volume_factor = 1.0):
        """
        调整音频音量
        :param input_path: 输入音频文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param volume_factor: 音量调整因子（例如 0.5 表示音量减半，2.0 表示音量加倍）
        """

        data_dir = get_data_dir()
        audio_name= os.path.splitext(os.path.basename(input_path))[0]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_audio")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_audio")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"{audio_name}_ad_volume_{time.strftime('%Y%m%d%H%M%S')}.wav")

        logger.info(f"⏳ 正在调整音频音量: {input_path} -> {output_path}，音量因子: {volume_factor}")
        AudioOpsV2.adjust_audio_volume(input_path, output_path, volume_factor)
        logger.info(f"✅ 音频音量调整完成: {output_path}")
        relative_path = os.path.relpath(output_path,start=data_dir)
        return relative_path


######################################################################################################################################
###################################################音频剪辑方法########################################################################
class VideoCutMethods:

    @staticmethod
    def add_audio_to_video(video_path, audio_path, save_file = None, start_time = 0, end_time = None, video_volume=1.0, new_audio_volume=1.0):
        """
        将音频添加到视频中，指定开始时间和结束时间，同时可以调整视频中已存在音频和加入的音频音量。
        
        :param video_path: 视频文件路径
        :param audio_path: 音频文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param start_time: 音频开始的时间点（秒）。
                        例如 10.5，表示原音频文件的 00:00:00 将对齐到视频的 00:00:10.5。
        :param end_time: 音频结束的时间点（秒）。
                        例如 20.0，表示原音频文件的 00:00:10.0 将对齐到视频的 00:00:20.0。
        :param video_volume: 视频音量（0.0 到 1.0 之间的浮点数），默认值为 1.0。
        :param new_audio_volume: 新音频音量（默认为1.0）
        """ 
        data_dir = get_data_dir()
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_endswith = os.path.splitext(os.path.basename(video_path))[1]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"{video_name}_ad_audio{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        
        if end_time is None:
            end_time = VideoOpsV2.get_video_info(video_path)['duration']

        logger.info(f"⏳ 正在将音频添加到视频: {video_path} + {audio_path} -> {output_path}，开始时间: {start_time}秒，结束时间: {end_time}秒，视频音量: {video_volume}，新音频音量: {new_audio_volume}")  
        VideoOpsV2.add_audio_segment_to_video(video_path, audio_path, output_path, start_time, end_time, video_volume, new_audio_volume)
        logger.info(f"✅ 音频已成功添加到视频: {output_path}")
        relative_path = os.path.relpath(output_path,start=data_dir)
        return relative_path

    
    @staticmethod
    def add_hardsub_with_offset(video_path, subtitle_path, save_file = None, start_time = 0):
        """
        将字幕加载到视频，并指定字幕在视频中开始显示的时间。
        
        :param video_path: 视频文件路径
        :param subtitle_path: 字幕文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param start_time: 字幕开始的时间点（秒）。
                        例如 10.5，表示原字幕文件的 00:00:00 将对齐到视频的 00:00:10.5。
        :return: 输出视频路径
        """
        
        # 生成一个唯一的临时字幕文件名，防止文件名冲突
        temp_sub_path = f"temp_subs_{uuid.uuid4().hex}.ass"
        data_dir = get_data_dir()
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_endswith = os.path.splitext(os.path.basename(video_path))[1]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"{video_name}_ad_subtitles_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        
        try:
            logger.info(f"⏳ 正在处理字幕时间轴，偏移量: {start_time}秒")

            subs = pysubs2.load(subtitle_path)
            offset_ms = int(start_time * 1000)
            subs.shift(ms=offset_ms)
            subs.save(temp_sub_path, format="ass")

            logger.info(f"💾 临时字幕已生成: {temp_sub_path}")

            final_output = VideoOpsV2.add_hardsub(video_path, temp_sub_path, output_path)
            relative_path = os.path.relpath(final_output,start=data_dir)
            return relative_path

        except Exception as e:
            logger.error(f"❌ 字幕处理或压制失败: {e}")
            raise e  # 向上抛出异常以便外层捕获

        finally:
            if os.path.exists(temp_sub_path):
                os.remove(temp_sub_path)
                logger.info(f"🗑️ 已清理临时字幕文件: {temp_sub_path}")
    
    
    @staticmethod
    def adjust_video_volume(video_path, save_file = None, volume=1.0):
        """
        调整视频音量。
        
        :param video_path: 视频文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param volume: 音量调整值（0.0 到 1.0 之间的浮点数），默认值为 1.0。
        """
        data_dir = get_data_dir()
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_endswith = os.path.splitext(os.path.basename(video_path))[1]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"{video_name}_ad_volume_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        logger.info(f"⏳ 正在调整视频音量: {video_path} -> {output_path}，音量: {volume}")
        VideoOpsV2.adjust_volume_in_video(video_path, output_path, volume)
        logger.info(f"✅ 视频音量已调整: {output_path}，音量: {volume}")
        relative_path = os.path.relpath(output_path,start=data_dir)
        return relative_path
    

    @staticmethod
    def resize_and_cut_video(input_path, new_width, new_height,save_file = None, crop=False):
        """
        保持原比例缩放视频，并裁剪到指定尺寸。
        
        :param input_path: 输入视频文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param new_width: 目标宽度
        :param new_height: 目标高度
        :param crop: 是否裁剪视频，默认值为 False。
        """ 
        data_dir = get_data_dir()
        video_name = os.path.splitext(os.path.basename(input_path))[0]
        video_endswith = os.path.splitext(os.path.basename(input_path))[1]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"{video_name}_resize_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        logger.info(f"⏳ 正在调整视频尺寸: {input_path} -> {output_path}，目标尺寸: {new_width}x{new_height}")
        VideoOpsV2.resize_and_cut_video(input_path, output_path, new_width, new_height,crop=crop)
        logger.info(f"✅ 视频尺寸已调整: {output_path}，目标尺寸: {new_width}x{new_height}")
        relative_path = os.path.relpath(output_path,start=data_dir)
        return relative_path
    

    @staticmethod
    def clip_video(video_path: str, save_file: str = None, duration: float = 1, start_time: float = 0):
        """
        根据时间去剪切视频
        
        :param video_path: 视频文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param duration: 剪切时长（秒）
        :param start_time: 剪切开始时间（秒）
        """ 
        data_dir = get_data_dir()
        if save_file is None:
            result_video_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            result_video_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(result_video_dir, exist_ok=True)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_endswith = os.path.splitext(os.path.basename(video_path))[1]
        clip_path = os.path.join(result_video_dir,f"{video_name}_clip_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        logger.info(f"⏳ 正在剪切视频: {video_path} -> {clip_path}，时长: {duration}秒，开始时间: {start_time}秒")  
        VideoOpsV2.clip_video(video_path, clip_path, duration, start_time)
        logger.info(f"✅ 视频剪切完成: {clip_path}")
        relative_path = os.path.relpath(clip_path,start=data_dir)
        return relative_path
    

    @staticmethod
    def merge_videos(video_paths: List[str], save_file: str = None,):
        """
        合并多个视频文件为一个视频文件。
        
        :param video_paths: 视频文件路径列表
        :param save_file: 存储在result_video模块下的文件名
        """ 
        data_dir = get_data_dir()
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"merged_{time.strftime('%Y%m%d%H%M%S')}.mp4")
        logger.info(f"⏳ 正在合并视频: {video_paths} -> {output_path}")
        VideoOpsV2.merge_videos(video_paths, output_path)
        logger.info(f"✅ 视频已合并: {output_path}")
        relative_path = os.path.relpath(output_path,start=data_dir)
        return relative_path
    
    
    @staticmethod
    def insert_video_at_time(input_video_path: str, insert_video_path: str, save_file: str = None, insert_time: float = 0):
        """
        在指定时间插入视频
        
        :param video_paths: 视频文件路径列表
        :param save_file: 存储在result_video模块下的文件名
        :param insert_time: 插入时间（秒）
        """ 
        data_dir = get_data_dir()
        video_name = os.path.splitext(os.path.basename(input_video_path))[0]
        video_endswith = os.path.splitext(os.path.basename(input_video_path))[1]
        if save_file is None:
            output_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            output_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir,f"{video_name}_insert_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        logger.info(f"⏳ 正在插入视频: {insert_video_path} -> {output_path}，插入时间: {insert_time}秒")
        VideoOpsV2.insert_video_at_time(input_video_path, insert_video_path, output_path, insert_time)
        logger.info(f"✅ 视频已插入: {output_path}，插入时间: {insert_time}秒")
        relative_path = os.path.relpath(output_path,start=data_dir)
        return relative_path
    

    @staticmethod
    def image_to_video(black_img_path,save_file,duration):
        """根据图片和时长生成一段视频"""
        data_dir = get_data_dir()
        if save_file is None:
            result_video_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            result_video_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(result_video_dir, exist_ok=True)
        video_name = os.path.splitext(os.path.basename(black_img_path))[0]
        video_endswith = os.path.splitext(os.path.basename(black_img_path))[1]
        bs_output_video_path = os.path.join(result_video_dir,f"{video_name}_img2video_{time.strftime('%Y%m%d%H%M%S')}.mp4")
        VideoOpsV2.image_to_video(black_img_path,bs_output_video_path,duration)
        relative_path = os.path.relpath(bs_output_video_path,start=data_dir)
        return relative_path
    

    @staticmethod
    def format_video(input_path: str, save_file: str = None, is_alpha: bool = False):
        """
        规范化输入视频
        
        :param input_path: 输入视频文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param is_alpha: 是否属于透明视频，默认值为 False。
        """
        data_dir = get_data_dir()
        if save_file is None:
            result_video_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            result_video_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(result_video_dir, exist_ok=True)
        video_name = os.path.splitext(os.path.basename(input_path))[0]
        video_endswith = os.path.splitext(os.path.basename(input_path))[1]
        output_path = os.path.join(result_video_dir,f"{video_name}_format_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        VideoOpsV2.format_video(input_path,output_path,is_alpha=is_alpha)
        logger.info(f"✅ 视频已格式化: {output_path}")
        relative_path = os.path.relpath(output_path,start=data_dir)

        return relative_path

################################################################################################################################
####################################################################去除绿幕填充素材##############################################

class ChromaKeyCompositor:

    @staticmethod
    def remove_green_screen(input_video_path: str, save_file: str = None, is_dilation: bool = True, tolerance: int = 45):
        """
        去除绿幕
        
        :param input_video_path: 输入视频文件路径
        :param save_file: 存储在result_video模块下的文件名
        :param is_dilation: 是否进行膨胀操作，默认值为 True。
        :param tolerance: 容差值，默认值为 45。
        """
        data_dir = get_data_dir()

        video_name = os.path.splitext(os.path.basename(input_video_path))[0]
        video_endswith = os.path.splitext(os.path.basename(input_video_path))[1]
        if save_file is None:
            result_video_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            result_video_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(result_video_dir, exist_ok=True)
        output_video_path = os.path.join(result_video_dir,f"{video_name}_remove_green_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")

        nopv_path,bg_index = RemoveGreenScreen.remove_dynamic_greenscreen2(input_video_path,output_video_path,is_dilation,tolerance)
        logger.info(f"✅ 视频已去除绿幕: {nopv_path,bg_index }")
        relative_path = os.path.relpath(nopv_path,start=data_dir)
        relative_nopv_path = os.path.relpath(bg_index,start=data_dir)
        return relative_path,relative_nopv_path 
        

    @staticmethod
    def fill_video(fill_video,foreground_path, bg_index_path,save_file,
                                    fully_fill = True,need_audio = False):
        """
        在透明格式的视频上填充素材视频
        :param fill_video: 素材视频路径
        :param foreground_path: 前景视频路径（.mov）格式
        :param bg_index: 背景索引视频路径（.npy文件）
        :param save_file: 存储在result_video模块下的文件名
        :param fully_fill: 是否完全填充，默认值为 True。
        :param need_audio: 是否需要音频，默认值为 False。
        """
        data_dir = get_data_dir()
        if save_file is None:
            result_video_dir = os.path.join(data_dir,"result_video","clip_video")
        else:
            result_video_dir = os.path.join(data_dir,"result_video",save_file,"clip_video")
        os.makedirs(result_video_dir, exist_ok=True)
        video_name = os.path.splitext(os.path.basename(fill_video))[0]
        video_endswith = os.path.splitext(os.path.basename(fill_video))[1]
        output_video_path = os.path.join(result_video_dir,f"{video_name}_fill_{time.strftime('%Y%m%d%H%M%S')}.{video_endswith}")
        bg_index = np.load(bg_index_path)
        RemoveGreenScreen.fill_transparent_background(fill_video,foreground_path, bg_index,output_video_path,
                                    fully_fill = fully_fill,need_audio = need_audio)
        logger.info(f"✅ 视频已填充: {output_video_path}")
        relative_path = os.path.relpath(output_video_path,start=data_dir)

        return relative_path


if __name__ == '__main__':

    #############################################字幕编辑测试###############################################
    video_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test.mp4"
    video_path2 = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test2.mp4"
    subtitle_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test.ass"
    output_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test_hardsub.mp4"
    audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_audio.wav"
    image_image_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\test_img\1.jpg"
    start_time = 2
    end_time = None
    save_file = "测试"
    # final_output = VideoCutMethods.add_hardsub_with_offset(video_path, subtitle_path, save_file,start_time)
    # final_output = VideoCutMethods.add_audio_to_video(video_path, audio_path, save_file, start_time, end_time, video_volume=0.1, new_audio_volume=2)
    # final_output = VideoCutMethods.adjust_video_volume(video_path, save_file, 0.1)
    # final_output = VideoCutMethods.clip_video(video_path, save_file, duration=1, start_time=start_time)
    # final_output = VideoCutMethods.resize_and_cut_video(video_path, 240, 240,save_file=save_file,crop=False)
    # final_output = VideoCutMethods.merge_videos([video_path,video_path2],save_file= save_file)
    # final_output = VideoCutMethods.insert_video_at_time(video_path, insert_video_path=video_path2, save_file=save_file, insert_time=start_time)
    # final_output = VideoCutMethods.format_video(video_path,save_file)
    final_output = VideoCutMethods.image_to_video(image_image_path,save_file,3)
    print(f"✅ 最终输出视频: {final_output}")

    ##################################################音频编辑测试############################################
    # audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo3_audio.wav"
    # audio_path2 = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_audio.wav"
    # out_put_audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\test_avatar_adjust.wav"
    # AudioCutMethods.adjust_audio_volume(audio_path, save_file, 100)
    # AudioCutMethods.concate_audios([audio_path, audio_path2], save_file)

    #######################################################去除绿幕测试##############################################
    # gs_video_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo3_video_rmbg.mp4"
    # rmd_bgpath, index_path = ChromaKeyCompositor.remove_green_screen(gs_video_path, save_file)
    # data_dir = get_data_dir()
    # rmd_bgpath = os.path.join(data_dir,rmd_bgpath)
    # index_path = os.path.join(data_dir,index_path)
    # print('rmd_bgpath',rmd_bgpath,'index_path',index_path)
    # ChromaKeyCompositor.fill_video(video_path2,rmd_bgpath,index_path,save_file,True,False)

