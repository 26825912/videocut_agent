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
from langchain_core.tools import tool

from .audio_ops_v2 import AudioOpsV2

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


###################################################################################################################################################
###################################################音频剪辑方法#####################################################################################



@tool
def clip_audio(input_path, 
            start_time, 
            duration,
            # save_file = None
            ):
    """
    裁剪音频片段
    :param input_path: 输入音频文件路径
    :param start_time: 裁剪开始时间（秒）
    :param duration: 裁剪时长（秒）
    :return:
    :param relative_path: 裁剪后的音频相对路径
    """
    save_file = None
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir,input_path)
        
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
    

@tool
def concate_audios(audio_files,
                # save_file = None
                ):
    """
    合并多个音频文件
    :param audio_files: 输入音频文件路径列表
    :param output_file: 输出合并后的音频文件路径
    :return:
    :param relative_path: 合并后的音频相对路径
    """
    save_file = None
    data_dir = get_data_dir()
    audio_files = [os.path.join(data_dir,file) for file in audio_files]
        
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
    

@tool
def adjust_audio_volume(input_path, 
                        # save_file = None, 
                        volume_factor = 1.0):
    """
    调整音频音量
    :param input_path: 输入音频文件路径
    :param volume_factor: 音量调整因子（例如 0.5 表示音量减半，2.0 表示音量加倍）
    :return:
    :param relative_path: 调整音量后得音频相对路径
    """
    
    save_file = None
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir,input_path)
        
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



if __name__ == '__main__':

    #############################################字幕编辑测试###############################################
    video_path = r"/video_cut_test/test.mp4"
    video_path2 = r"/video_cut_test/test2.mp4"
    subtitle_path = r"/video_cut_test/test.ass"
    output_path = r"/video_cut_test/test_hardsub.mp4"
    audio_path = r"/avatar/test_data/demo2_audio.wav"
    image_image_path = r"/test_img/1.jpg"
    start_time = 2
    end_time = None
    save_file = "测试"

    ##################################################音频编辑测试############################################
    # audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo3_audio.wav"
    # audio_path2 = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_audio.wav"
    # out_put_audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\test_avatar_adjust.wav"
    # AudioCutMethods.adjust_audio_volume(audio_path, save_file, 100)
    # AudioCutMethods.concate_audios([audio_path, audio_path2], save_file)

