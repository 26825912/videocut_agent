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

from .video_ops_v2 import VideoOpsV2, AudioOpsV2,RemoveGreenScreen

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
    inputs:
        input_path: 输入音频文件路径
        start_time: 裁剪开始时间（秒）
        duration: 裁剪时长（秒）
    return:
        relative_path: 裁剪后的音频相对路径
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "裁剪后的音频相对路径"
        }]
    }
    

@tool
def concate_audios(audio_files,
                # save_file = None
                ):
    """
    合并多个音频文件
    inputs:
        audio_files: 输入音频文件路径列表
    return:
        relative_path: 合并后的音频相对路径
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "合并后的音频相对路径"
        }]
    }
    

@tool
def adjust_audio_volume(input_path, 
                        # save_file = None, 
                        volume_factor = 1.0):
    """
    调整音频音量
    inputs:
        input_path: 输入音频文件路径
        volume_factor: 音量调整因子范围[0.1,5]
    return:
        relative_path: 调整音量后得音频相对路径
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "调整音量后得音频相对路径"
        }]
    }


######################################################################################################################################
###################################################音频剪辑方法########################################################################


@tool
def add_audio_to_video(video_path, 
                    audio_path, 
                    # save_file = None, 
                    start_time = 0, 
                    end_time = None, 
                    video_volume=1.0, 
                    new_audio_volume=1.0):
    """
    音频添加到视频中
    可以指定在视频的那个时间点，将音频添加到视频中。
    input:
        video_path: 视频文件路径
        audio_path: 音频文件路径
        start_time: 音频开始的时间点（秒）。
                    例如 10.5
        end_time: 音频结束的时间点（秒）。
                    例如 20.0
        video_volume: 视频音量（0.0 到 1.0 之间的浮点数），默认值为 1.0。
        new_audio_volume: 新音频音量（默认为1.0）
    return:
        relative_path: 添加音频后的视频相对路径
    """ 
    save_file = None
    data_dir = get_data_dir()
    video_path = os.path.join(data_dir,video_path)
    audio_path = os.path.join(data_dir,audio_path)
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "添加音频后的视频相对路径"
        }]
    }


@tool
def add_hardsub_with_offset(video_path, 
                            subtitle_path, 
                            # save_file = None, 
                            start_time = 0):
    """
    可以将字幕文件写入视频文件中，可以指定字幕开始播放时间点。
    input:
        video_path: 视频文件路径
        subtitle_path: 字幕文件路径
        start_time: 字幕开始的时间点（秒）。
                    例如 10.5秒
    return:
        relative_path: 添加字幕后的视频相对路径
    """
    
    # 生成一个唯一的临时字幕文件名，防止文件名冲突
    save_file = None
    temp_sub_path = f"temp_subs_{uuid.uuid4().hex}.ass"
    data_dir = get_data_dir()
    video_path = os.path.join(data_dir,video_path)
    subtitle_path = os.path.join(data_dir,subtitle_path)
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

        # final_output = VideoOpsV2.add_hardsub(video_path, temp_sub_path, output_path)
        final_output = VideoOpsV2.add_hardsub_v2(video_path, temp_sub_path, output_path)
        relative_path = os.path.relpath(final_output,start=data_dir)
        return {
            "tool_return":[{
                "relative_path": relative_path,
                "describe": "添加字幕后的视频相对路径"
            }]
        }

    except Exception as e:
        logger.error(f"❌ 字幕处理或压制失败: {e}")
        raise e  # 向上抛出异常以便外层捕获

    finally:
        if os.path.exists(temp_sub_path):
            os.remove(temp_sub_path)
            logger.info(f"🗑️ 已清理临时字幕文件: {temp_sub_path}")


@tool
def adjust_video_volume(video_path, 
                        # save_file = None, 
                        volume=1.0):
    """
    调整视频音量。
    
    input:
        video_path: 视频文件路径
        volume: 音量调整值范围[0.1,5]
    return:
        relative_path: 调整音量后的视频相对路径
    """
    save_file = None
    data_dir = get_data_dir()
    video_path = os.path.join(data_dir,video_path)
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "调整音量后的视频相对路径"
        }]
    }


@tool
def resize_and_cut_video(input_path, 
                        new_width, 
                        new_height,
                        # save_file = None, 
                        crop=False):
    """
    保持原比例缩放视频，并裁剪到指定尺寸。
    input:
        input_path: 输入视频文件路径
        new_width: 目标宽度
        new_height: 目标高度
        crop: 是否裁剪视频，默认值为 False。
    return:
        relative_path: 调整尺寸后的视频相对路径
    """ 
    save_file = None
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir,input_path)
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "调整尺寸后的视频相对路径"
        }]
    }


@tool
def clip_video(video_path: str, 
            # save_file: str = None, 
            duration: float = 1, 
            start_time: float = 0):
    """
    根据时间去剪切视频
    input:
        video_path: 视频文件相对路径
        duration: 剪切时长（秒）
        start_time: 剪切开始时间（秒）
    return:
        relative_path: 剪切后的视频相对路径
    """ 
    save_file = None
    data_dir = get_data_dir()
    video_path = os.path.join(data_dir,video_path)
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "剪切后的视频相对路径"
        }]
    }


@tool
def merge_videos(video_paths: List[str], 
                # save_file: str = None
                ):
    """
    将多个视频拼接成一个视频
    input:
        video_paths: 视频文件路径列表
    return:
        relative_path: 合并后的视频相对路径
    """ 
    save_file = None
    data_dir = get_data_dir()
    video_paths = [os.path.join(data_dir,video_path) for video_path in video_paths]
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "合并后的视频相对路径"
        }]
    }


@tool
def insert_video_at_time(input_video_path: str, 
                        insert_video_path: str, 
                        # save_file: str = None, 
                        insert_time: float = 0):
    """
    在指定时间插入视频
    
    input:
        input_video_path: 输入视频文件路径
        insert_video_path: 插入视频文件路径
        insert_time: 插入时间（秒）
    return:
        relative_path: 插入视频后的视频相对路径
    """ 
    save_file = None
    data_dir = get_data_dir()
    input_video_path = os.path.join(data_dir,input_video_path)
    insert_video_path = os.path.join(data_dir,insert_video_path)
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "插入视频后的视频相对路径"
        }]
    }


@tool
def image_to_video(
                black_img_path,
                # save_file,
                duration):
    """
    根据图片和时长生成一段视频

    input:
        black_img_path: 图片文件路径
        duration: 视频时长（秒）
    return:
        relative_path: 图片转换成视频后的相对路径
    """
    save_file = None
    data_dir = get_data_dir()
    black_img_path = os.path.join(data_dir,black_img_path)
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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "图片转换成视频后的相对路径"
        }]
    }


@tool
def image_to_video_v2(black_img_paths: List[str], 
                    # save_file: str, 
                    durations: List[float]) -> List[str]:
    """
    批量将图片转换为视频片段
    input:
        black_img_paths: 图片相对路径列表
        durations: 对应每张图片的视频时长列表 (秒)
    return:
        relative_path: 图片转换成视频后的相对路径列表
    """
    save_file = None
    data_dir = get_data_dir()
    generated_video_paths = []

    # 1. 准备输出目录 (所有生成的视频都放在同一个目录下)
    if save_file is None:
        result_video_dir = os.path.join(data_dir, "result_video", "clip_video")
    else:
        result_video_dir = os.path.join(data_dir, "result_video", save_file, "clip_video")
    
    os.makedirs(result_video_dir, exist_ok=True)

    # 校验列表长度是否一致，打印警告
    if len(black_img_paths) != len(durations):
        print(f"WARNING: 图片数量 ({len(black_img_paths)}) 与 时长数量 ({len(durations)}) 不一致，将按较短的列表进行处理。")

    # 2. 遍历图片和时长进行处理
    # 使用 zip 同时遍历两个列表，enumerate 获取索引用于生成唯一文件名
    for idx, (img_rel_path, duration) in enumerate(zip(black_img_paths, durations)):
        try:
            # 构建绝对路径
            full_img_path = os.path.join(data_dir, img_rel_path)
            
            # 检查图片是否存在
            if not os.path.exists(full_img_path):
                print(f"ERROR: 图片文件不存在: {full_img_path}，跳过该项。")
                continue

            # 构建输出文件名
            # 使用 splitext 获取文件名，加入 idx 和 uuid 防止循环过快导致的时间戳重名覆盖
            original_name = os.path.splitext(os.path.basename(full_img_path))[0]
            timestamp = time.strftime('%Y%m%d%H%M%S')
            
            # 文件名格式: 原文件名_索引_时间戳.mp4
            video_filename = f"{original_name}_{idx}_{timestamp}_{str(uuid.uuid4())[:4]}.mp4"
            bs_output_video_path = os.path.join(result_video_dir, video_filename)

            print(f"INFO: 正在生成第 {idx+1} 个视频片段，时长: {duration}s, 源图片: {original_name}")

            # 3. 调用底层的单张图片转视频方法
            VideoOpsV2.image_to_video(full_img_path, bs_output_video_path, duration)

            # 4. 获取相对路径并添加到结果列表
            if os.path.exists(bs_output_video_path):
                relative_path = os.path.relpath(bs_output_video_path, start=data_dir)
                generated_video_paths.append(relative_path)
            else:
                print(f"ERROR: 视频生成失败，文件未创建: {bs_output_video_path}")

        except Exception as e:
            print(f"ERROR: 处理图片 {img_rel_path} 时发生异常: {e}")
            continue

    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "图片转换成视频后的相对路径"
        } for relative_path in generated_video_paths]
    }


@tool
def format_video(input_path: str, 
                # save_file: str = None, 
                is_alpha: bool = False):
    """
    规范化输入视频
    
    input:
        input_path: 输入视频文件路径
        is_alpha: 是否属于透明视频，默认值为 False。
    return:
        relative_path: 规范化后的视频相对路径
    """
    save_file = None
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir,input_path)
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

    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "格式化后的视频相对路径"
        }]
    }

################################################################################################################################
####################################################################去除绿幕填充素材##############################################



@tool
def remove_green_screen(input_video_path: str, 
                        # save_file: str = None, 
                        is_dilation: bool = True, 
                        tolerance: int = 45):
    """
    去除视频中的绿幕，将视频转换成.mov格式的透明视频
    
    input:
        input_video_path: 输入视频文件路径
        is_dilation: 是否进行膨胀操作，默认值为 True。
        tolerance: 容差值，默认值为 45。
    return:
        relative_path: 去除绿幕后的视频相对路径
        relative_nopv_path: 去除绿幕后的背景索引视频相对路径
    """
    save_file = None
    data_dir = get_data_dir()
    input_video_path = os.path.join(data_dir,input_video_path)

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
    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "去除绿幕后的视频相对路径"
        },{
            "relative_path": relative_nopv_path,
            "describe": "去除绿幕后的背景索引视频相对路径"
        }]
    }
    

@tool
def fill_video(fill_video,
            foreground_path, 
            bg_index_path,
            # save_file,
            fully_fill = True,need_audio = False):
    """
    在透明格式（.mov）的视频上填充素材视频
    input:
        fill_video: 素材视频路径
        foreground_path: 前景视频路径（.mov）格式
        bg_index_path: 背景索引视频路径（.npy文件）
        fully_fill: 是否完全填充，默认值为 True。
        need_audio: 是否需要音频，默认值为 False。
    return:
        relative_path: 填充后的视频相对路径
    """
    save_file = None
    data_dir = get_data_dir()
    fill_video = os.path.join(data_dir,fill_video)
    foreground_path = os.path.join(data_dir,foreground_path)
    bg_index_path = os.path.join(data_dir,bg_index_path)
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

    return {
        "tool_return":[{
            "relative_path": relative_path,
            "describe": "填充后的视频相对路径"
        }]
    }


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
    # final_output = VideoCutMethods.add_hardsub_with_offset(video_path, subtitle_path, save_file,start_time)
    # final_output = VideoCutMethods.add_audio_to_video(video_path, audio_path, save_file, start_time, end_time, video_volume=0.1, new_audio_volume=2)
    # final_output = VideoCutMethods.adjust_video_volume(video_path, save_file, 0.1)
    # final_output = VideoCutMethods.clip_video(video_path, save_file, duration=1, start_time=start_time)
    # final_output = VideoCutMethods.resize_and_cut_video(video_path, 240, 240,save_file=save_file,crop=False)
    # final_output = VideoCutMethods.merge_videos([video_path,video_path2],save_file= save_file)
    # final_output = VideoCutMethods.insert_video_at_time(video_path, insert_video_path=video_path2, save_file=save_file, insert_time=start_time)
    # final_output = VideoCutMethods.format_video(video_path,save_file)
    # final_output = VideoCutMethods.image_to_video(image_image_path,save_file,3)
    # print(f"✅ 最终输出视频: {final_output}")

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
    image_image_path = 'images/de432d77-798d-4975-a7dd-186587697e7a.jpg'
    image_image_path2 = 'images/10a11361-8562-4177-bccd-d71dee2c23ea.jpg'
    generated_video_paths = image_to_video_v2([image_image_path,image_image_path2],save_file,[2,5])
    print(generated_video_paths)

