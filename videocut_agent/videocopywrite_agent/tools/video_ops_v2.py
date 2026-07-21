import os
import cv2
import time
import json
import numpy as np
import subprocess
import shlex
from moviepy.editor import VideoFileClip
from sklearn.cluster import KMeans
from skimage.morphology import disk, dilation
import imageio
from ffmpeg_normalize import FFmpegNormalize
from PIL import Image
import tempfile
import platform
import re
import shutil
import ffmpeg
import cv2
import logging
import math
from tqdm import tqdm
import tempfile
import sys
from collections import namedtuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def detect_gpu():
    system = platform.system() 
    gpu_info = []
    
    if system == "Windows":
        # 使用WMIC命令获取显卡信息
        try:
            output = subprocess.check_output(
                "wmic path win32_VideoController get name",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            gpu_info = output.strip().split('\n')[1:]
        except:
            pass
            
    elif system == "Linux":
        # 使用lspci命令获取显卡信息
        try:
            output = subprocess.check_output(
                "lspci | grep -i 'vga\\|3d'",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            gpu_info = output.splitlines()
        except:
            pass
            
    elif system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(
                "system_profiler SPDisplaysDataType | grep -i 'chipset model'",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            gpu_info = output.splitlines()
        except:
            pass


    results = {"NVIDIA": False, "Intel": False,"Apple": False, "AMD": False}
    results["System"] = system

    for info in gpu_info:
        info = info.strip().lower()
        if not info:
            continue
            
        if "nvidia" in info:
            results["NVIDIA"] = True
        elif "intel" in info:
            results["Intel"] = True
        elif "apple" in info:
            results["Apple"] = True
        elif "amd" in info:
            results["AMD"] = True

    return results


class VideoFormat:
    Width =  780
    Height = 1280
    Fps = 30
    bit_rate ='12000000'     # 12Mbps
    crf='23'                # 恒定质量系数（18-28）
    preset='medium'        # 编码速度预设
    vcodec='libx264'
    pix_fmt='yuv420p'       # 像素格式（必须yuv420p兼容移动设备）
    round='up'              # 向上取整


class AudioFormat:
    aac = True  # 是否使用AAC编码
    codec = 'aac'  # 音频编码格式
    bit_rate = '122000'  # 128kbps
    sample_rate = 44100  # 44.1kHz
    channels = 2  # 双声道  


class NvidiaVideoFormat:
    try:
        result = detect_gpu()
        if result['NVIDIA'] and result["System"] in ["Windows","Linux"]:
            logger.info(f"检测到{result['System']} 操作系统和NVIDIA GPU,使用NVENC编码")
            pix_fmt='yuv420p' 
            hwaccel='cuda'
            vcodec='h264_nvenc'
            preset='p3'
            rc='vbr'
            qd='23'
            async_depth=4  
        elif result['Intel'] and result["System"] in ["Windows","Linux"]:
            logger.info(f"检测到{result['System']} 操作系统和Intel GPU,使用QSV编码")
            pix_fmt='nv12' #'yuv420p'#'nv12' 
            hwaccel='qsv'
            vcodec='h264_qsv'
            preset='fast'
            rc='vbr'
            global_quality='23'
            async_depth=4
        elif result['Intel'] and result["System"] == "Darwin":
            logger.info(f"检测到{result['System']} 操作系统和Intel GPU,使用VideoToolbox编码")
            pix_fmt='nv12'
            hwaccel='videotoolbox'
            vcodec='h264_videotoolbox'
            preset='fast'
            rc='vbr'
            quality='23'
        elif result['Apple'] and result["System"] == "Darwin":
            logger.info(f"检测到{result['System']} 操作系统和Apple GPU,使用VideoToolbox编码")
            pix_fmt='nv12'
            hwaccel='videotoolbox'
            vcodec='h264_videotoolbox'
            preset='fast'
            rc='vbr'
            quality='100'
        elif result['AMD'] and result["System"] in ["Windows","Linux"]:
            logger.info(f"检测到{result['System']} 操作系统和AMD GPU,使用AMF编码")
            pix_fmt='nv12'
            hwaccel='amf'
            vcodec='h264_amf'
            preset='balanced'    # 编码预设（balanced/speed/quality）
            rc='vbr_peak'
            quality='23'         # 质量优先模式（speed/balanced/quality）
            # bitrate='12M'
        

    except Exception as e:
        logger.error(f"检测GPU失败,请检测GPU是否支持NVENC或HQENC: {e}")
        # 如果检测失败，使用默认设置
        raise 

class AudioOpsV2:

    @staticmethod
    def get_audio_duration(file_path):
        """
        使用 ffmpeg-python 获取音频文件的时长（以秒为单位）。
        Args:
            file_path (str): 音频文件的路径。
        Returns:
            float: 文件时长，如果出错则返回 None。
        """
        try:
            probe_output = ffmpeg.probe(file_path)
            duration = float(probe_output['format']['duration'])
            return duration
            
        except ffmpeg.Error as e:
            logger.error(f"处理文件时出错: {e.stderr.decode('utf8')}")
            return None
        except KeyError:
            logger.error("无法从文件信息中找到时长。")
            return None
    

    @staticmethod
    def concatenate_audio_files(input_files, output_file):
        """
        使用 ffmpeg-python 实现的快速拼接 (Stream Copy)。
        无需重编码，速度极快。
        """
        list_filename = 'inputs.txt'
        try:
            with open(list_filename, 'w', encoding='utf-8') as f:
                for path in input_files:
                    abs_path = os.path.abspath(path).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")

            (
                ffmpeg
                .input(list_filename, format='concat', safe=0)
                .output(output_file, c='copy')
                .overwrite_output() # 对应 -y 参数，允许覆盖
                .run(quiet=True)
            )
            logger.info(f"拼接成功: {output_file}")

        except ffmpeg.Error as e:
            logger.error("FFmpeg 执行错误:", e)
        except Exception as e:
            logger.error(f"发生错误: {e}")
        finally:
            # 3. 清理临时文件
            if os.path.exists(list_filename):
                os.remove(list_filename)
        

    @staticmethod
    def normalize_music_volume(input_audio_path,out_put_audio):
        """
        预处理音乐文件：将其响度统一为 -14 LUFS，并生成一个临时文件
        """
        logger.info(f"⏳ 正在标准化音频: {input_audio_path} -> {out_put_audio}")
        
        # 初始化标准化器
        normalizer = FFmpegNormalize(
            target_level=-14,   # 目标 LUFS
            print_stats=False,
            true_peak=-1.0,     # 峰值限制
        )
        
        # 执行标准化
        normalizer.add_media_file(input_audio_path, out_put_audio)
        normalizer.run_normalization()
        logger.info(f"✅ 音频标准化完成: {out_put_audio}")
        return out_put_audio
    

    @staticmethod
    def adjust_audio_volume(input_path, output_path, volume_factor=1.0):
        """
        调整音频音量并防止失真 (使用限制器)
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        try:
            stream = ffmpeg.input(input_path)
            
            # 1. 先调整音量
            stream = stream.filter('volume', volume_factor)
            stream = stream.filter('alimiter', limit=1.0, level_in=1.0, level_out=1.0)
            
            stream = ffmpeg.output(stream, output_path)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"音量调整完成 (已启用防失真): {output_path}")
            return output_path

        except ffmpeg.Error as e:
            logger.error("FFmpeg 执行出错:", file=sys.stderr)
            if e.stderr:
                logger.error(e.stderr.decode('utf8'), file=sys.stderr)
            raise e
        except Exception as e:
            logger.error(f"发生未知错误: {e}", file=sys.stderr)
            raise e
    

    @staticmethod
    def clip_audio(input_path, start_time, duration, output_path):
        """
        裁剪音频片段
        
        :param input_path: 输入音频文件的路径 (str)
        :param start_time: 裁剪开始时间，单位秒 (float or int)
        :param duration: 裁剪持续时长，单位秒 (float or int)
        :param output_path: 保存路径 (str)
        :return: 裁剪后的音频保存路径 (str)
        """
        
        # 1. 检查输入文件是否存在
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        
        # 2. 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        try:
            stream = ffmpeg.input(input_path, ss=start_time, t=duration)
            stream = ffmpeg.output(stream, output_path, acodec='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"音频裁剪成功: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            # 如果出错，打印 FFmpeg 的错误日志
            logger.error("FFmpeg 执行出错:", file=sys.stderr)
            if e.stderr:
                logger.error(e.stderr.decode('utf8'), file=sys.stderr)
            raise e
        except Exception as e:
            logger.error(f"发生未知错误: {e}", file=sys.stderr)
            raise e
    


class VideoOpsV2:
    
    @staticmethod
    def get_video_info(video_path):
        """获取视频信息"""
        if not video_path :
                logger.error('get_video_info输入路径为空请检查调用之前的部分')
                raise ValueError('get_video_info输入路径为空请检查调用之前的部分')
        try:
            result = ffmpeg.probe(video_path)
            video_info={
                'duration':float(result['format']['duration']),
                'bit_rate':int(result['format']['bit_rate']),
                'size':int(result['format']['size']),
                'width':result['streams'][0]['width'],
                'height':result['streams'][0]['height'],
                'fps':result['streams'][0]['avg_frame_rate'],
            }
            logger.info(f'获取视频信息成功:{video_info}')
            return video_info
        except Exception as e:
            logger.error(f'获取视频信息失败,使用opencv重新获取:{str(e)}')
            #使用opencv获取
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f'获取视频信息失败,使用opencv重新获取,视频路径:{video_path}')
                exit()
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
            cap.release()
            video_info={
                'duration':duration,
                'width':width,
                'height':height,
                'fps':fps,
            }
            logger.info(f'使用opencv重新获取视频信息成功:{video_info}')
            return video_info

    
    ######################################################################################################
    ###################################################规范化视频格式#######################################
    @staticmethod
    def format_video(input_path,
                    format_output_path,
                    is_alpha=False,
                    pad_or_crop='crop',
                    force_original_aspect_ratio='increase'
                    ):
        '''简单格式化视频（仅处理视频）
        params:
            input_path: 输入视频文件的路径 (str)
            format_output_path: 格式化后的视频保存路径 (str)
            is_alpha: 是否处理透明度通道 (bool, default=False)
            pad_or_crop: 是否填充或裁剪视频 ('pad' 或 'crop', default=True)
            force_original_aspect_ratio: 是否强制保持原始宽高比 ('decrease' 或 'increase', default='decrease')
        '''
        input_stream = ffmpeg.input(input_path).video
        input_stream = input_stream.filter('scale', 
                                        width = VideoFormat.Width, 
                                        height=VideoFormat.Height, 
                                        force_original_aspect_ratio=force_original_aspect_ratio)
        if pad_or_crop == "pad":
            input_stream = input_stream.filter('pad', VideoFormat.Width,
                                                VideoFormat.Height, 
                                                '(ow-iw)/2', '(oh-ih)/2')
        elif pad_or_crop == "crop":
            input_stream = input_stream.filter('crop', VideoFormat.Width,
                                                VideoFormat.Height, 
                                                '(iw-ow)/2', '(ih-oh)/2')
        else:
            logger.error(f'format_video pad_or_crop参数错误,请输入pad或crop')
            raise ValueError(f'format_video pad_or_crop参数错误,请输入pad或crop')
        
        input_stream = input_stream.filter('fps', 
                                        fps=VideoFormat.Fps, 
                                        round=VideoFormat.round)  # 向上取整
        
        if NvidiaVideoFormat.result['NVIDIA']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec,
                'qp': NvidiaVideoFormat.qd,
                'preset': NvidiaVideoFormat.preset,
            }
        elif NvidiaVideoFormat.result['Intel']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec,
                'global_quality': NvidiaVideoFormat.global_quality,
                'preset': NvidiaVideoFormat.preset,
            }
        else:
            ffmpeg_args = {
                'vcodec': VideoFormat.vcodec,
                'preset': VideoFormat.preset,
                'crf': VideoFormat.crf,
            }

        if is_alpha:
            ffmpeg_args = {
                    'c:v': 'prores_ks',           # 视频编码器
                    'pix_fmt': 'yuva444p10le',    # 像素格式（带 Alpha）
                    'profile:v': '4444',          # ProRes 配置档
                    'vendor': 'apl0',             # Apple 厂商代码（可选）
                    'qscale:v': 5 ,                # 质量级别（1-31，越小质量越高）
                    'f': 'mov'
                }
            output_stream = ffmpeg.output(input_stream, 
                                        format_output_path,
                                        **ffmpeg_args,
                                        y=None
                                    )
        else:
            output_stream = ffmpeg.output(input_stream, 
                                        format_output_path,
                                        **ffmpeg_args,
                                        y=None
                                    )
        ffmpeg.run(output_stream,overwrite_output=True,quiet=True)
        #print('成功规范化视频')
        return format_output_path
    

    #############################################################################################################
    ##########################################添加音频以及音频音量控制#############################################
    @staticmethod
    def add_audio_to_video(video_path, audio_path, out_put_path):
        try:
            video_stream = ffmpeg.input(video_path)
            audio_stream = ffmpeg.input(audio_path)
            output_stream = ffmpeg.output(video_stream,
                                        audio_stream,
                                        out_put_path, 
                                        vcodec='copy',       # 复制视频流
                                        acodec=AudioFormat.codec,        # 使用AAC编码
                                        audio_bitrate=AudioFormat.bit_rate, # 设置音频比特率
                                        ar=AudioFormat.sample_rate)             # 采样率48kHz
            ffmpeg.run(output_stream,overwrite_output=True,quiet=True)
            logger.info(f'视频{video_path}添加音频成功！并保存至{out_put_path}')
            return out_put_path
        except Exception as e:
            logger.error(f'视频{video_path}添加音频失败:{str(e)}')
            raise Exception(f'视频{video_path}添加音频失败:{str(e)}') 


    @staticmethod
    def _apply_loudnorm_to_stream(audio_stream, target_lufs=-14):
        """
        【流处理专用】给音频流添加国际标准响度滤镜 (EBU R128 / YouTube Standard)
        :param audio_stream: ffmpeg-python 的音频流对象 (input_audio)
        :param target_lufs: 目标响度，互联网通常为 -14，电视广播为 -23
        :return: 处理后的音频流对象
        """
        # loudnorm: FFmpeg 内置的响度标准化滤镜
        # I: Integrated loudness (目标综合响度)
        # TP: True Peak (最大真峰值，防止爆音，一般设为 -1.0)
        # LRA: Loudness Range (响度范围，一般 11 适合一般视频)
        # dual_mono: 如果是双声道，设为 true 处理更自然
        return audio_stream.filter(
            'loudnorm', 
            I=target_lufs, 
            TP=-1.0, 
            LRA=11
        )
    
    #########################################################在指定时间段添加音频#############################################
    @staticmethod
    def add_audio_segment_to_video(video_path, audio_path, output_path, start_time, end_time, video_volume=1.0, new_audio_volume=1.0):
        """
        在视频指定时间段添加/混合音频，并支持分别调整音量。
        
        :param video_path: 视频文件路径
        :param audio_path: 要添加的音频文件路径
        :param output_path: 输出文件路径
        :param start_time: 音频在视频中开始的时间（秒）
        :param end_time: 音频在视频中结束的时间（秒）
        :param video_volume: 原视频的音量倍数 (1.0 为原声, 0.5 为半音量, 0 为静音)
        :param new_audio_volume: 新加入音频的音量倍数 (1.0 为原声, 2.0 为两倍音量)
        """
        try:
            # 1. 获取视频信息（主要是时长）
            probe = ffmpeg.probe(video_path)
            video_stream_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            video_duration = float(video_stream_info['duration'])
            
            # 检查视频是否包含音频流
            has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])

            # 2. 逻辑计算：修正结束时间
            if start_time >= video_duration:
                logger.warning(f"警告: 开始时间 {start_time}s 已超过视频时长 {video_duration}s，未执行操作。")
                return

            valid_end_time = min(end_time, video_duration)
            insert_duration = valid_end_time - start_time
            
            if insert_duration <= 0:
                logger.warning("警告: 插入时长无效。")
                return

            logger.info(f"处理: 插入区间 {start_time}-{valid_end_time}s, 原声{video_volume}倍, 新声{new_audio_volume}倍")

            # 3. 构建 FFmpeg 输入流
            input_video = ffmpeg.input(video_path)
            input_audio = ffmpeg.input(audio_path)

            # ---------------------------------------------------------
            # 修改点 A: 处理新音频 (截取 -> 调音 -> 延迟)
            # ---------------------------------------------------------
            delay_ms = int(start_time * 1000)
            
            processed_new_audio = (
                input_audio
                .filter('atrim', duration=insert_duration)  # 1. 先截取时长
                .filter('volume', volume=new_audio_volume)  # 2. 调整音量 (新增)
                .filter('adelay', f"{delay_ms}|{delay_ms}") # 3. 设置延迟位置
            )

            # ---------------------------------------------------------
            # 修改点 B: 处理原视频音频并混合
            # ---------------------------------------------------------
            if has_audio:
                # 获取原音频并调整音量 (新增)
                processed_original_audio = VideoOpsV2._apply_loudnorm_to_stream(input_video.audio)
                original_audio = processed_original_audio.filter('volume', volume=video_volume)
                
                # 使用 amix 混合
                final_audio = ffmpeg.filter(
                    [original_audio, processed_new_audio], 
                    'amix', 
                    inputs=2, 
                    duration='first', 
                    dropout_transition=0
                )
            else:
                # 如果原视频没声音，直接使用处理后的新音频
                # 注意：如果 video_volume 设为非0但原视频没音轨，这里无法无中生有，只能忽略 video_volume
                final_audio = processed_new_audio

            # 4. 输出
            output = ffmpeg.output(
                input_video.video,
                final_audio,
                output_path,
                vcodec='copy', # 视频流复制，最快
                acodec='aac',  # 音频需重编码
                strict='experimental'
            )

            output.run(overwrite_output=True, quiet=True)
            logger.info(f"成功: 视频已保存至 {output_path}")

        except ffmpeg.Error as e:
            logger.error("FFmpeg 发生错误:")
            # 尝试解码错误信息，如果失败则打印原始对象
            error_msg = e.stderr.decode('utf8') if e.stderr else str(e)
            logger.error(error_msg)
        except Exception as e:
            logger.error(f"发生未知错误: {e}")

    
    @staticmethod
    def add_voice_overlay(input_video, input_audio, output_video, origin_audio_volume=2.0, add_audio_volume=0.3):
        """
        在视频上叠加新的语音，保留原始音频
        
        参数:
            input_video: 输入视频文件路径
            input_audio: 要添加的语音文件路径
            output_video: 输出视频文件路径
            audio_volume: 新语音的音量级别 (0.0-1.0)
        """
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError(f"视频文件不存在: {input_video}")
            if not os.path.exists(input_audio):
                raise FileNotFoundError(f"音频文件不存在: {input_audio}")
                
            video_input = ffmpeg.input(input_video)
            audio_input = ffmpeg.input(input_audio)
            
            probe = ffmpeg.probe(input_video)
            has_audio = any(stream['codec_type'] == 'audio' for stream in probe['streams'])
            
            # 设置音频混合
            if has_audio:
                # 提取原始音频并调整音量
                original_audio = video_input.audio.filter('volume', origin_audio_volume)
                new_audio = audio_input.audio.filter('volume', add_audio_volume)   
                # 混合两个音频轨道
                mixed_audio = ffmpeg.filter([original_audio, new_audio], 'amix', inputs=2, duration='longest')
            else:
                # 如果视频没有音频，只需使用新语音
                mixed_audio = audio_input.audio.filter('volume', add_audio_volume)
            
            output = ffmpeg.output(
                video_input.video, 
                mixed_audio, 
                output_video,
                vcodec='copy',  # 复制视频流，避免重新编码
                acodec='aac',   # 使用AAC编码音频
                shortest=None   # 确保输出与最长输入相同
            )
            output.run(overwrite_output=True, quiet=True)
            logger.info(f"成功添加语音叠加: {output_video}")
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg错误: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"处理视频时发生错误: {str(e)}")
            raise


    @staticmethod
    def adjust_volume_in_video(input_path, output_path, volume=0.5):
        """
        调整视频中的音量
        """
        try:
            input_stream = ffmpeg.input(input_path)
            probe = ffmpeg.probe(input_path)
            has_audio = any(stream['codec_type'] == 'audio' for stream in probe['streams'])
            if not has_audio:
                logger.error(f"视频 {input_path} 没有音频流，无法调整音量")
                raise Exception(f"视频 {input_path} 没有音频流，无法调整音量")

            audio = input_stream.audio.filter('volume', volume)
            video = input_stream.video
            
            output = ffmpeg.output(video, audio, output_path, vcodec='copy')
            
            ffmpeg.run(output, overwrite_output=True,quiet=True)
            logger.info(f"成功处理: {input_path}")
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg错误: {e.stderr.decode()}")
    

    ###############################################################################################################
    ##############################################调整视频尺寸和位置################################################
    @staticmethod
    def resize_and_cut_video(input_path, output_path, new_width, new_height,crop=True):
        logger.info(f'视频{input_path}开始resize视频')
        probe = ffmpeg.probe(input_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        orig_width = int(video_info['width'])
        orig_height = int(video_info['height'])
        scale_w = new_width / orig_width
        scale_h = new_height / orig_height
        scale = max(scale_w, scale_h)  
        if NvidiaVideoFormat.result['NVIDIA']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec,
                'qp': NvidiaVideoFormat.qd,
                'preset': NvidiaVideoFormat.preset,
            }
        elif NvidiaVideoFormat.result['Intel']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec,
                'global_quality': NvidiaVideoFormat.global_quality,
                'preset': NvidiaVideoFormat.preset,
            }
        else:
            ffmpeg_args = {
                'vcodec': VideoFormat.vcodec,
                'preset': VideoFormat.preset,
                'crf': VideoFormat.crf,
            }
        if crop:
            try:
                (
                ffmpeg
                .input(input_path)
                .filter('scale', new_width, -1)  # 根据宽度缩放，高度自动计算
                .filter('crop', new_width, new_height)  # 裁剪到精确尺寸
                .filter('setsar', 1)  # 设置样本宽高比为1:1
                .output(output_path, **ffmpeg_args)
                .run(overwrite_output=True,quiet=True)
                )
                logger.info(f'视频{input_path}已经调整视频的尺寸并裁剪为{new_width}x{new_height}')
            except:
                logger.warning(f'视频{input_path}调整后的尺寸不满足裁剪尺寸要求强制调整视频尺寸')
                (
                ffmpeg
                .input(input_path)
                .filter('scale', int(orig_width * scale), int(orig_height * scale))
                .filter('crop', new_width, new_height)
                .filter('setsar', 1)
                .output(output_path, **ffmpeg_args)
                .run(overwrite_output=True,quiet=True)
                )
        else:
            try:
                (
                ffmpeg
                .input(input_path)
                .filter('scale', int(orig_width * scale), int(orig_height * scale))
                .filter('setsar', 1)
                .output(output_path, **ffmpeg_args)
                .run(overwrite_output=True,quiet=True)
                )
                logger.info(f'视频{input_path}已经调整视频的尺寸为{int(orig_width * scale)}x{int(orig_height * scale)}')
            except:
                logger.warning(f'视频{input_path}调整后的尺寸不满足要求强制调整视频尺寸')
                (
                ffmpeg
                .input(input_path)
                .filter('scale', int(orig_width * scale), int(orig_height * scale))
                .filter('setsar', 1)
                .output(output_path, **ffmpeg_args)
                .run(overwrite_output=True,quiet=True)
                )


    @staticmethod
    def resize_and_cut_video2(input_path, output_path, new_width, new_height):
        """
        调整视频尺寸
        :param input_path: 输入视频路径
        :param output_path: 输出视频路径
        :param new_width: 新宽度
        :param new_height: 新高度
        """
        video_info = VideoOpsV2.get_video_info(input_path)
        orig_width = int(video_info['width'])
        orig_height = int(video_info['height'])
        scale_w = new_width / orig_width
        scale_h = new_height / orig_height
        scale = max(scale_w, scale_h)

        clip = VideoFileClip(input_path) # 载入原始视频
        clip_resized = clip.resize(scale) # 按比例缩放视频
        logger.info(f'视频{input_path}已经调整视频的尺寸为{int(clip_resized.w)}x{int(clip_resized.h)}')
        
        # 获取缩放后的尺寸
        resized_width = int(clip_resized.w)
        resized_height = int(clip_resized.h)
        
        # 计算裁剪区域，以中心为基准
        x_center = resized_width // 2
        y_center = resized_height // 2
        x1 = max(0, x_center - new_width // 2)
        y1 = max(0, y_center - new_height // 2)
        x2 = min(resized_width, x_center + new_width // 2)
        y2 = min(resized_height, y_center + new_height // 2)
        
        # 裁剪视频到目标尺寸
        clip_cropped = clip_resized.crop(x1=x1, y1=y1, x2=x2, y2=y2)
        logger.info(f'视频{input_path}已经裁剪视频的尺寸为{int(clip_cropped.w)}x{int(clip_cropped.h)}')
        
        if NvidiaVideoFormat.result['NVIDIA']:
            codec = "h264_nvenc"
            # qp = NvidiaVideoFormat.qd
        elif NvidiaVideoFormat.result['Intel']:
            codec = "h264_qsv"
            # global_quality = NvidiaVideoFormat.global_quality
        elif NvidiaVideoFormat.result['AMD']:
            codec = "h264_amf"
            # global_quality = NvidiaVideoFormat.global_quality
        elif NvidiaVideoFormat.result['Apple']:
            codec = "h264_videotoolbox"
            # global_quality = NvidiaVideoFormat.global_quality
        else:   
            codec = "libx264"
        try:
            # 使用更兼容的编码参数
            clip_cropped.write_videofile(
                output_path, 
                codec='libx264',           # 使用标准H.264编码
                audio_codec="aac",         # 使用标准AAC音频编码
                temp_audiofile="temp-audio.m4a",  # 临时音频文件
                remove_temp=True,          # 自动删除临时文件
                fps=VideoFormat.Fps,                    # 设置标准帧率
                bitrate=VideoFormat.bit_rate,            # 设置比特率
                preset="medium"            # 编码速度与质量平衡
            )
            logger.info(f'视频{input_path}已经调整视频的尺寸为{int(clip_cropped.w)}x{int(clip_cropped.h)}')
            return output_path
        except:
            logger.error(f'视频{input_path}调整视频的尺寸失败')
            return None
        finally:
            # 关闭视频剪辑对象以释放资源
            clip.close()
            clip_resized.close()
            clip_cropped.close()
    
    
    @staticmethod
    def resize_and_cut_video3(input_path, output_path, new_width, new_height):
        """
        使用FFmpeg直接处理，速度更快
        """
        video_info = VideoOpsV2.get_video_info(input_path)
        orig_width = int(video_info['width'])
        orig_height = int(video_info['height'])
        
        # 计算缩放比例
        scale_w = new_width / orig_width
        scale_h = new_height / orig_height
        scale = max(scale_w, scale_h)
        
        # 计算缩放后的尺寸
        scaled_width = int(orig_width * scale)
        scaled_height = int(orig_height * scale)
        
        # 计算裁剪位置
        x_offset = max(0, (scaled_width - new_width) // 2)
        y_offset = max(0, (scaled_height - new_height) // 2)
            
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', f'scale={scaled_width}:{scaled_height},crop={new_width}:{new_height}:{x_offset}:{y_offset}',
                '-c:v', 'h264_nvenc' if NvidiaVideoFormat.result['NVIDIA'] else 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            # 执行命令
            subprocess.run(cmd, check=True)
            logger.info(f'视频{input_path}已经调整视频的尺寸为{int(scaled_width)}x{int(scaled_height)}')
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f'FFmpeg处理视频{input_path}失败: {e}')
            return None
        



    ################################################################################################################
    ##################################################视频的裁剪和拼接###############################################
    # @staticmethod   
    # def clip_video(video_path, out_put_path, cut_duration,start_time = 0):

    #     '''裁剪视频'''
    #     #duration,(width,height),fps = VideoOps.get_vidoe_info(video_path)
    #     try:
    #         input_stream = ffmpeg.input(video_path, ss = start_time, t=cut_duration)
    #         output_stream = ffmpeg.output(input_stream, out_put_path, c='copy')
    #         ffmpeg.run(output_stream,overwrite_output=True,quiet=True)
    #         logger.info(f'{video_path}视频裁剪成功！')
    #         return out_put_path
    #     except Exception as e:
    #         logger.error(f'{video_path}视频裁剪失败:{e}')
    #         return None 
    

    @staticmethod
    def clip_video(video_path, out_put_path, cut_duration, start_time=0, save_audio=True):
        """
        裁剪视频
        :param video_path: 输入视频路径
        :param out_put_path: 输出视频路径
        :param cut_duration: 裁剪持续时间
        :param start_time: 开始裁剪的时间点
        :param save_audio: 是否保留音频 (True: 如果原视频有音频则保留，无音频则忽略; False: 强制移除音频)
        :return: 成功返回输出路径，失败返回 None
        """
        try:
            # 1. 定义输入流
            # ss: start time, t: duration
            input_stream = ffmpeg.input(video_path, ss=start_time, t=cut_duration)

            # 2. 定义输出参数字典
            output_kwargs = {
                'c': 'copy',  # 核心参数：流复制模式 (速度极快，不重新编码)
            }

            # 3. 处理音频逻辑
            if not save_audio:
                output_kwargs['an'] = None

            # 5. 执行命令
            output_stream = ffmpeg.output(input_stream, out_put_path, **output_kwargs)
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
            
            logger.info(f'{video_path} 视频裁剪成功！(保留音频: {save_audio})')
            return out_put_path

        except ffmpeg.Error as e:
            # 捕获 FFmpeg 专用错误，通常能看到 stderr 信息
            error_message = e.stderr.decode('utf8') if e.stderr else str(e)
            logger.error(f'{video_path} 视频裁剪 FFmpeg 错误: {error_message}')
            return None
        except Exception as e:
            logger.error(f'{video_path} 视频裁剪发生未知错误: {e}')
            return None
    
    ###############################################################合并视频############################################
    
    @staticmethod
    def merge_videos(video_paths, 
                    output_path,
                    video_size = None, 
                    include_audio=False,
                    force_original_aspect_ratio='increase'):
        """
        合并多个视频，只合并视频流
        params:
            video_paths: 待合并的视频文件路径列表 (List[str])
            output_path: 合并后的视频输出路径 (str)
            video_size: 目标视频尺寸 (VideoSize, default=None)
            include_audio: 是否包含音频 (bool, default=False)
            force_original_aspect_ratio: 是否强制保持原始宽高比 ('decrease' 或 'increase', default='increase')
        """
        logger.info(f'开始合并视频: {video_paths}, 包含音频: {include_audio}')
        try:
            stream = []
            for i, video_p in enumerate(video_paths):
                vid_input = ffmpeg.input(video_p)
                
                video_chain = vid_input.video
                video_chain = video_chain.setpts('PTS-STARTPTS')
                if video_size:
                    video_chain = video_chain.filter('scale', width=video_size.width, height=video_size.height,
                                                force_original_aspect_ratio=force_original_aspect_ratio)
                    video_chain = video_chain.filter('setsar', '1')
                    video_chain = video_chain.filter('fps', fps=video_size.fps)
                    # video_chain = video_chain.filter('pad', width=video_size.width, height=video_size.height,
                    #                             x='(ow-iw)/2', y='(oh-ih)/2', color='black')
                    video_chain = video_chain.filter('crop', video_size.width, video_size.height)
                else:
                    video_chain = video_chain.filter('scale', width=VideoFormat.Width, height=VideoFormat.Height,
                                                force_original_aspect_ratio=force_original_aspect_ratio)
                    video_chain = video_chain.filter('setsar', '1')
                    video_chain = video_chain.filter('fps', fps=VideoFormat.Fps)
                    # video_chain = video_chain.filter('pad', width=VideoFormat.Width, height=VideoFormat.Height,
                    #                             x='(ow-iw)/2', y='(oh-ih)/2', color='black')
                    video_chain = video_chain.filter('crop', VideoFormat.Width, VideoFormat.Height)
            
                if include_audio:
                    audio_chain = vid_input.audio
                    stream.append(video_chain)
                    stream.append(audio_chain)
                else:
                    stream.append(video_chain)
            if include_audio:
                merged_video = ffmpeg.concat(*stream, v=1, a=1)
            else:
                merged_video = ffmpeg.concat(*stream, v=1, a=0)

            if NvidiaVideoFormat.result['NVIDIA']:
                ffmpeg_args = {'vcodec': NvidiaVideoFormat.vcodec, 
                                'qp' : NvidiaVideoFormat.qd,
                                'pix_fmt': NvidiaVideoFormat.pix_fmt, 
                                'preset': NvidiaVideoFormat.preset}
                
            elif NvidiaVideoFormat.result['Intel']:
                ffmpeg_args = {'vcodec': NvidiaVideoFormat.vcodec, 
                                'pix_fmt': NvidiaVideoFormat.pix_fmt,
                                'global_quality': NvidiaVideoFormat.global_quality, 
                                'preset': NvidiaVideoFormat.preset
                                }
            else:
                ffmpeg_args = {
                    'vcodec': VideoFormat.vcodec,
                    'preset': VideoFormat.preset,
                    'crf': VideoFormat.crf,
                    'pix_fmt': VideoFormat.pix_fmt
                }
            
            if include_audio:
                ffmpeg_args.update({
                    'acodec': AudioFormat.codec,
                    # 'audio_bitrate': AudioFormat.bit_rate,
                    # 'ar': AudioFormat.sample_rate
                })
            ffmpeg.output(merged_video, 
                    output_path,
                    **ffmpeg_args
                ).run(overwrite_output=True, quiet=True)
            logger.info(f'成功拼接视频流 (不含音频)。输出路径:{output_path}')
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg错误: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
            logger.error(f'合并{video_paths}的时候出现错误')
            raise e
            #return None
        except Exception as e:
            logger.error(f'合并视频失败请检测merge_videos输入参数: {str(e)}')
            logger.error(f'合并{video_paths}的时候出现错误')
            raise e
            #return None


    @staticmethod
    def repeat_video(input_path, output_path, repeat_times=2):
        """
        将视频重复拼接多次
        
        参数:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径
        repeat_times: 重复次数，默认为2次
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"输入文件不存在: {input_path}")
            temp_list_path = "concat_list.txt"
            with open(temp_list_path, 'w') as f:
                for _ in range(repeat_times):
                    f.write(f"file '{os.path.abspath(input_path)}'\n")
        
            (
                ffmpeg
                .input(temp_list_path, format='concat', safe=0)
                .output(output_path, c='copy')  # 使用copy编码以保持原质量
                .overwrite_output()
                .run(overwrite_output=True, quiet=True)
            )
            
            f.close()
            os.remove(temp_list_path)
            logger.info(f"视频已成功重复拼接 {repeat_times} 次，输出文件: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg错误: {e.stderr.decode()}")
            raise e
        except Exception as e:
            logger.error(f"错误: {str(e)}")
            raise e
        # finally:
        #     if os.path.exists(temp_list_path):
                # os.remove(temp_list_path)
                

    #######################################再指定时间短插入视频############################################

    @staticmethod
    def insert_video_at_time(main_video_path, insert_video_path, output_path, insert_time):
        """
        修复版：解决了 concat 输入顺序导致的 Media type mismatch 错误
        """

        # --- 内部辅助函数 ---
        def _get_info(path):
            try:
                probe = ffmpeg.probe(path)
                has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])
                duration = float(probe['format']['duration'])
                return has_audio, duration
            except ffmpeg.Error as e:
                print(e.stderr.decode('utf8'))
                raise ValueError(f"无法读取文件信息: {path}")

        def _get_silence(duration):
            return (
                ffmpeg
                .input('anullsrc', format='lavfi', t=duration)
                .filter_('aformat', sample_rates=44100, channel_layouts='stereo')
                .filter_('asetpts', 'PTS-STARTPTS')
            )

        def _normalize_audio(audio_stream):
            return (
                audio_stream
                .filter_('aformat', sample_rates=44100, channel_layouts='stereo')
            )

        if not os.path.exists(main_video_path) or not os.path.exists(insert_video_path):
            raise FileNotFoundError("输入视频文件不存在")

        logger.info(f"正在处理: {main_video_path} + {insert_video_path} @ {insert_time}s")

        try:
            has_a, dur_a = _get_info(main_video_path)
            has_b, dur_b = _get_info(insert_video_path)

            in_main = ffmpeg.input(main_video_path)
            in_insert = ffmpeg.input(insert_video_path)

            # 4. 处理视频流
            v_a_pre = in_main.video.trim(start=0, end=insert_time).setpts('PTS-STARTPTS')
            v_b = in_insert.video.setpts('PTS-STARTPTS')
            v_a_post = in_main.video.trim(start=insert_time).setpts('PTS-STARTPTS')
            
            video_segments = [v_a_pre, v_b, v_a_post]

            # 5. 处理音频流
            audio_segments = []
            has_output_audio = False 

            if not has_a and not has_b:
                logger.info("模式: 无音频拼接")
                has_output_audio = False
            else:
                has_output_audio = True
                if has_a:
                    a_a_pre = _normalize_audio(in_main.audio.filter_('atrim', start=0, end=insert_time).filter_('asetpts', 'PTS-STARTPTS'))
                    a_a_post = _normalize_audio(in_main.audio.filter_('atrim', start=insert_time).filter_('asetpts', 'PTS-STARTPTS'))
                else:
                    a_a_pre = _get_silence(insert_time)
                    remaining_dur = max(0, dur_a - insert_time)
                    a_a_post = _get_silence(remaining_dur)

                if has_b:
                    a_b = _normalize_audio(in_insert.audio.filter_('asetpts', 'PTS-STARTPTS'))
                else:
                    a_b = _get_silence(dur_b)

                audio_segments = [a_a_pre, a_b, a_a_post]

            # ----------------------------------------------------
            # 6. 合并 (Concat) - 【关键修改点】
            # ----------------------------------------------------
            if has_output_audio:
                # 我们需要把列表变成 [V1, A1, V2, A2, V3, A3] 的顺序
                concat_streams = []
                for v, a in zip(video_segments, audio_segments):
                    concat_streams.append(v)
                    concat_streams.append(a)
                
                # 使用交叉排列后的流进行合并
                joined = ffmpeg.concat(*concat_streams, v=1, a=1)
            else:
                # 纯视频模式，顺序无所谓，因为只有视频
                joined = ffmpeg.concat(*video_segments, v=1, a=0)

            output = ffmpeg.output(joined, output_path, vsync=2)
            output.run(overwrite_output=True, quiet=True) # quiet=False 方便看日志
            
            logger.info(f"✅ 处理成功，已保存: {output_path}")

        except ffmpeg.Error as e:
            logger.error("❌ FFmpeg 发生错误:")
            logger.error(e.stderr.decode('utf8') if e.stderr else str(e))
            raise
        

    ###################################################################################################
    #########################################添加字幕到视频##############################################
    @staticmethod
    def add_hardsub(video_path,subtitle_path,output_path):
        input_stream = ffmpeg.input(video_path)
        video_with_subs = input_stream.video.filter('ass', subtitle_path)

        if NvidiaVideoFormat.result['NVIDIA']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec, 
                'qp' : NvidiaVideoFormat.qd,
                'preset': NvidiaVideoFormat.preset}
                
        elif NvidiaVideoFormat.result['Intel']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec, 
                'global_quality': NvidiaVideoFormat.global_quality, 
                'preset': NvidiaVideoFormat.preset
                }
        else:
            ffmpeg_args = {
            'vcodec': VideoFormat.vcodec,
            'preset': VideoFormat.preset,
            'crf': VideoFormat.crf,
        }
        
        ffmpeg.output(
            video_with_subs,
            output_path,
            **ffmpeg_args,
            acodec='copy',  # 直接复制音频，不重新编码
        ).run(overwrite_output=True, quiet=True)

        logger.info(f"✅ 成功：{output_path}")
        return output_path

    
    @staticmethod
    def add_hardsub_v2(video_path, subtitle_path, output_path):
        """
        为视频添加硬字幕（ASS格式）。
        智能判断：如果有音频则保留（不转码），如果没有音频则只输出画面。
        """
        try:
            # 1. 使用 probe 探测文件信息，检查是否有音频流
            probe = ffmpeg.probe(video_path)
            # 在所有流中查找 codec_type 为 'audio' 的流
            audio_stream_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            has_audio = audio_stream_info is not None

            # 2. 构建输入流
            input_stream = ffmpeg.input(video_path)
            
            # 3. 处理视频流：添加字幕滤镜
            # 注意：这里只处理画面
            video_with_subs = input_stream.video.filter('ass', subtitle_path)

            # 4. 设置视频编码参数 (保持你原有的硬件加速逻辑)
            if NvidiaVideoFormat.result['NVIDIA']:
                ffmpeg_args = {
                    'vcodec': NvidiaVideoFormat.vcodec, 
                    'qp' : NvidiaVideoFormat.qd,
                    'preset': NvidiaVideoFormat.preset
                }
            elif NvidiaVideoFormat.result['Intel']:
                ffmpeg_args = {
                    'vcodec': NvidiaVideoFormat.vcodec, 
                    'global_quality': NvidiaVideoFormat.global_quality, 
                    'preset': NvidiaVideoFormat.preset
                }
            else:
                ffmpeg_args = {
                    'vcodec': VideoFormat.vcodec,
                    'preset': VideoFormat.preset,
                    'crf': VideoFormat.crf,
                }

            # 5. 构建输出指令
            if has_audio:
                logger.info(f"检测到音频流，将在合并字幕时保留音频: {video_path}")
                # 如果有音频，显式传入 input_stream.audio，并设置 copy 模式
                out = ffmpeg.output(
                    video_with_subs,
                    input_stream.audio,
                    output_path,
                    **ffmpeg_args,
                    acodec='copy' # 直接复制音频，不重新编码，速度快且不损质
                )
            else:
                logger.info(f"未检测到音频流，将仅生成带有字幕的静音视频: {video_path}")
                # 如果没音频，只传入视频流，不传 acodec 参数
                out = ffmpeg.output(
                    video_with_subs,
                    output_path,
                    **ffmpeg_args
                )

            # 6. 执行命令
            out.run(overwrite_output=True, quiet=True)

            logger.info(f"✅ 字幕添加成功：{output_path}")
            return output_path

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg Error: {e.stderr.decode('utf8') if e.stderr else str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Add Hardsub Error: {str(e)}")
            raise e
        

    @staticmethod
    def soft_subtitle(input_video_path, input_audio_path, input_subtitle_path, output_video_path):
        video = ffmpeg.input(input_video_path)
        audio = ffmpeg.input(input_audio_path)
        subtitle = ffmpeg.input(input_subtitle_path)
        if NvidiaVideoFormat.result['NVIDIA']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec, 
                'qp' : NvidiaVideoFormat.qd,
                'preset': NvidiaVideoFormat.preset}
                    
        elif NvidiaVideoFormat.result['Intel']:
            ffmpeg_args = {
                'vcodec': NvidiaVideoFormat.vcodec, 
                'global_quality': NvidiaVideoFormat.global_quality, 
                'preset': NvidiaVideoFormat.preset
                }
        else:
            ffmpeg_args = {
            'vcodec': VideoFormat.vcodec,
            'preset': VideoFormat.preset,
            'crf': VideoFormat.crf,
            }
        (
            ffmpeg
            .output(
                video.video,                    # 只取视频流
                audio.audio,                    # 只取音频流
                subtitle,                       # 字幕作为独立轨道
                output_video_path,
                **ffmpeg_args,
                acodec=AudioFormat.codec,                   # 音频编码（WAV 可能是 PCM，转 AAC）
                scodec='mov_text',              # SRT 字幕编码（MP4 支持）
                # strict='-2'                     # 允许 mov_text
            )
            .run(overwrite_output=True, quiet=False)
        )

    
    @staticmethod
    def image_to_video(black_img_path,bs_output_video_path,duration):
        '''根据图片和时长生成一段视频'''
        try:
            input_stream = ffmpeg.input(black_img_path, 
                                        loop=1, 
                                        t=duration, 
                                        framerate=VideoFormat.Fps)
            video = input_stream.filter('format', 'rgb24')
            video = input_stream.filter('scale', VideoFormat.Width, VideoFormat.Height)
            video = video.filter('setsar', '1')  # 强制设置方形像素
            output_stream = ffmpeg.output(video, 
                                        bs_output_video_path, 
                                        vcodec=VideoFormat.vcodec, #编码
                                        acodec=AudioFormat.codec, #音频编码
                                        s=f'{VideoFormat.Width}x{VideoFormat.Height}') #分辨率
            ffmpeg.run(output_stream,quiet=True)
            logger.info('黑幕视频生成成功！')
            return bs_output_video_path
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg错误: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
            return None
        except Exception as e:
            logger.error(f'生成黑屏视频失败:{e}')
            return None

    ###################################################################################################################
    ####################################################去除视频的绿幕##################################################
    
class RemoveGreenScreen:
    
    @staticmethod
    def get_domain_color(image):

        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image
            
        img_array = np.array(img)
        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]
        
        quantized = (img_array // 5) * 5
        
        pixels = quantized.reshape(-1, 3)
        
        colors, counts = np.unique(pixels, axis=0, return_counts=True)
        most_common_idx = np.argmax(counts)
        most_common_color = colors[most_common_idx]
        
        mask = np.all(pixels == most_common_color, axis=1)
        group_pixels = img_array.reshape(-1, 3)[mask]
        
        if len(group_pixels) > 0:
            average_color = np.mean(group_pixels, axis=0).astype(int)
            return tuple(average_color)
        return tuple(most_common_color)
    
    @staticmethod
    def remove_image_background_color(input_image, bg_color, dilation = True,tolerance=65):
        
        img = np.array(input_image)
        # bg_mask = np.all(np.abs(img - bg_color) <= tolerance, axis=-1)
        diff = np.abs(img - bg_color)
        bg_mask = (diff[:,:,0]**2 + diff[:,:,1]**2 + diff[:,:,2]**2) <= (tolerance**2 * 3)
        # footprint = disk(3)
        # expanded_mask = dilation(bg_mask, footprint)
        # img[expanded_mask] = [255, 0, 255]
        img[bg_mask] = [255, 0, 255]
        return img
    
    
    @staticmethod
    def remove_image_background_color2(input_image, bg_color, is_dilation = True,tolerance=45):
        """
        去除绿幕变为透明背景
        
        :param input_image: 输入图像，支持numpy数组和PIL图像
        :param bg_color: 背景颜色，RGB格式，例如(0, 255, 0)
        :param is_dilation: 是否使用膨胀操作，默认为True
        :param tolerance: 颜色匹配容差，默认为45
        :return: 处理后的图像，BGRA格式
        """ 
        img = input_image.copy()
        
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        
        diff = np.abs(img[:,:,:3] - bg_color)
        color_distance = (diff[:,:,0]**2 + diff[:,:,1]**2 + diff[:,:,2]**2) <= (tolerance**2 * 3)
        
        if is_dilation:
            bg_mask = color_distance
            footprint = disk(2)
            expanded_mask = dilation(bg_mask, footprint)
            img[expanded_mask, 3] = 0  # 设置alpha通道为0（透明）
        else:
            img[color_distance, 3] = 0  # 设置alpha通道为0（透明）
        
        return img
    
    
    @staticmethod
    def get_bg_index(input_image,bg_color):
        img = np.array(input_image)
        tolerance = 65
        # bg_mask = np.all(np.abs(img - bg_color) <= tolerance, axis=-1)
        diff = np.abs(img - bg_color)
        bg_mask = (diff[:,:,0]**2 + diff[:,:,1]**2 + diff[:,:,2]**2) <= (tolerance**2 * 3)
        index = np.argwhere(bg_mask)
        return index,bg_mask

####################################################移除绿幕############################################

    @staticmethod
    def remove_dynamic_greenscreen2(input_video_path,output_video_path,is_dilation=True,tolerance = 45):
        """
        移除动态绿屏
        :param input_video_path: 输入视频路径
        :param output_video_path: 输出文件路径
        :param is_dilation: 是否使用膨胀操作，默认为True
        :param tolerance: 颜色匹配容差，默认为45
        :return: 处理后的视频路径，背景色索引
        """
        logger.info(f'视频{input_video_path}开始处理动态绿屏')
        cap = cv2.VideoCapture(input_video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        ret, first_frame = cap.read()
        if not ret:
            raise ValueError("无法读取视频第一帧")
        first_frame_rgba = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGBA)
        bg_color = RemoveGreenScreen.get_domain_color(first_frame_rgba)
        first_frame_rgb = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB)
        bg_index,_ = RemoveGreenScreen.get_bg_index(first_frame_rgb, bg_color)

        logger.info(f'视频{input_video_path}从中间帧检测到背景色: RGB{bg_color}')

        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        opv_dir = os.path.dirname(output_video_path)
        vn = os.path.basename(output_video_path).split('.')[0]
        nopv_path = os.path.join(opv_dir,vn + '.mov')
        index_save_path = os.path.join(opv_dir,vn + '_index.npy')
        np.save(index_save_path,bg_index)

        # 初始化视频写入器
        writer = imageio.get_writer(
                        nopv_path, 
                        fps=fps,
                        codec='prores_ks',
                        pixelformat='yuva444p10le',#'yuva444p10le',
                        macro_block_size=None
                    )
        pbar = tqdm(total=total_frames, desc="处理视频")
        try:
            frame_count = 0
            start_time = time.time()
            while True:
                ret, frame =  cap.read()
                if not ret:
                    break

                processed_frame = RemoveGreenScreen.remove_image_background_color2(frame, bg_color,is_dilation,tolerance)

                rgba_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGRA2RGBA)
                
                writer.append_data(rgba_frame)
                
                frame_count += 1
                pbar.update(1)

                if frame_count % 500 == 0:
                    #输出每秒平均处理多少帧
                    avg_fps = frame_count / (time.time() - start_time)
                    logger.info(f"已处理 {frame_count}/{total_frames} 帧, 平均帧率: {avg_fps:.2f}")

            return nopv_path,index_save_path
        
        except Exception as e:
            logger.error(f"[错误]remove_dynamic_greenscreen2方法出现错误-: {e}")
            raise
        
        finally:
            cap.release()
            writer.close()
            pbar.close()
            logger.info(f'视频{input_video_path}动态绿屏处理完成,资源已经释放')

    @staticmethod
    def _get_top_bg_w_h(coordinates):
        coord_array = np.array(coordinates)
        min_values = coord_array.min(axis=0)
        max_values = coord_array.max(axis=0) 
        width = max_values[1] - min_values[1]
        height = max_values[0] - min_values[0]
        top_left_corner = tuple(min_values)
        bottom_right_corner = tuple(max_values)
        return top_left_corner, bottom_right_corner,width,height
    

    @staticmethod
    def _zoom_out_video(video_path,output_path,md_videoinfo,w,h,x,y):
        try:
            stream = ffmpeg.input(video_path)
            video_stream = stream.video
            bg_videoinfo = VideoOpsV2.get_video_info(video_path)
            bg_width = bg_videoinfo['width']
            bg_height = bg_videoinfo['height']
            if max(bg_width,bg_height) > max(w,h):
                if w/bg_width >  h/bg_height:
                    scale = w/bg_width
                else:
                    scale = h/bg_height
            elif max(bg_width,bg_height) < max(w,h):
                if w/bg_width >  h/bg_height:
                    scale = w/bg_width
                else:
                    scale = h/bg_height
            else:
                scale = 1.0

            logger.info(f'bg_width:{bg_width},bg_height:{bg_height},scale:{scale}')
            logger.info(f'w:{w},h:{h},w*scale:{w*scale},h*scale:{h*scale},x:{x},y:{y}')
            scaled_video = video_stream.filter(
                'scale', 
                w=bg_width*scale,  #如果无徐保持素材真实比例，可以将w，h的值设置为 w ，h
                h=bg_height*scale  
            )

            black_canvas = (
                ffmpeg
                .input(
                    f'color=c=black:s={md_videoinfo.width}x{md_videoinfo.height}:d={md_videoinfo.duration}', 
                    format='lavfi'
                )
                .filter('fps', fps=f'{md_videoinfo.fps}') 
            )

            final_video = ffmpeg.overlay(
                black_canvas,      # 背景 (黑色画布)
                scaled_video,      # 前景 (缩小后的视频)
                x=x, 
                y=y
            )

            if NvidiaVideoFormat.result['NVIDIA']:
                ffmpeg_args = {
                    'vcodec': NvidiaVideoFormat.vcodec,
                    'qp': NvidiaVideoFormat.qd,
                    'pix_fmt': NvidiaVideoFormat.pix_fmt,
                    'preset': NvidiaVideoFormat.preset,
                    'acodec': AudioFormat.codec
                }
            elif NvidiaVideoFormat.result['Intel']:
                ffmpeg_args = {
                    'vcodec': NvidiaVideoFormat.vcodec,
                    'pix_fmt': NvidiaVideoFormat.pix_fmt,
                    'global_quality': NvidiaVideoFormat.global_quality,
                    'preset': NvidiaVideoFormat.preset,
                    'acodec': AudioFormat.codec
                }
            else:
                ffmpeg_args = {
                    'vcodec': VideoFormat.vcodec,
                    'preset': VideoFormat.preset,
                    'crf': VideoFormat.crf,
                    'acodec': AudioFormat.codec,
                    'pix_fmt': VideoFormat.pix_fmt
                }

            (
                ffmpeg
                .output(final_video, output_path, **ffmpeg_args)
                .run(overwrite_output=True, quiet=True)
            )
            logger.info(f"[完成] 视频{video_path}缩放完成: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"[错误]zoom_out_video方法出错—叠加视频时出错: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"[错误]zoom_out_video方法出错—处理视频时出错: {str(e)}")
            raise

######################################################填充绿幕#################################################
    @staticmethod
    def fill_transparent_background(fill_video,foreground_path, bg_index,output_path,
                                    fully_fill = True,need_audio = False):
        """
        在视频都名部分填充上背景素材
        参数:
            file_video: 填充素材视频路径
            foreground_path: 带 Alpha 通道的 MOV 视频（如 ProRes 4444）
            bg_index: 绿幕背景色索引
            fully_fill: 是否完全填充背景（True: 填充整个视频区域，
            output_path: 输出视频路径（如 output.mp4）
        """
        VideoInfo = namedtuple('VideoInfo', ['duration', 'bit_rate', 'size', 'width', 'height', 'fps'])
        fill_video_info_dict = VideoOpsV2.get_video_info(fill_video)
        fill_video_info = VideoInfo(**fill_video_info_dict)
        if fully_fill:
            
            top_left_corner, bottom_right_corner,nw,nh = RemoveGreenScreen._get_top_bg_w_h(bg_index)
            foregrount_video_info_dict = VideoOpsV2.get_video_info(foreground_path)
            foregrount_video_info = VideoInfo(**foregrount_video_info_dict)
            tfill_video_path = tempfile.mktemp(suffix='.mp4')
            RemoveGreenScreen._zoom_out_video(fill_video,
                                tfill_video_path,
                                foregrount_video_info,
                                nw,nh,
                                top_left_corner[1],top_left_corner[0])
            fill_video = tfill_video_path
        logger.info(f"[信息] 填充视频信息: {fill_video_info}")
        try:
            overlay_duration = fill_video_info.duration
            logger.info(f"[信息] 叠加视频时长: {overlay_duration:.2f}秒")
            bg = ffmpeg.input(fill_video, t=overlay_duration)
            fg = ffmpeg.input(foreground_path)
            merged = ffmpeg.filter([bg, fg], 'overlay', format='auto')

            # 输出（H.264 不支持透明，所以合成后为 RGB 视频）
            if NvidiaVideoFormat.result['NVIDIA']:
                ffmpeg_args = {
                    'vcodec': NvidiaVideoFormat.vcodec,
                    'qp': NvidiaVideoFormat.qd,
                    'pix_fmt': NvidiaVideoFormat.pix_fmt,
                    'preset': NvidiaVideoFormat.preset,
                    'acodec': AudioFormat.codec
                }
            elif NvidiaVideoFormat.result['Intel']:
                ffmpeg_args = {
                    'vcodec': NvidiaVideoFormat.vcodec,
                    'pix_fmt': NvidiaVideoFormat.pix_fmt,
                    'global_quality': NvidiaVideoFormat.global_quality,
                    'preset': NvidiaVideoFormat.preset,
                    'acodec': AudioFormat.codec
                }
            else:
                ffmpeg_args = {
                    'vcodec': VideoFormat.vcodec,
                    'preset': VideoFormat.preset,
                    'crf': VideoFormat.crf,
                    'acodec': AudioFormat.codec,
                    'pix_fmt': VideoFormat.pix_fmt
                }

            if need_audio:
                stream = ffmpeg.output(
                    merged, # 处理后的视频流
                    fg.audio, # 叠加视频的音频流
                    output_path, # 输出文件路径
                    **ffmpeg_args
                )
            else:
                stream = ffmpeg.output(
                    merged, # 处理后的视频流
                    # overlay_video_input.audio, # 叠加视频的音频流
                    output_path, # 输出文件路径
                    **ffmpeg_args
                )
            stream.run(overwrite_output=True, quiet=True)
            logger.info(f"[完成] {foreground_path}视频叠加完成: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"[错误] merge_videos_with_overlay方法出错-: {e}")
            raise 
        finally:
            os.remove(tfill_video_path) if fully_fill and os.path.exists(tfill_video_path) else None


    @staticmethod
    def convert_mov_to_mp4(input_path, output_path):
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vcodec='libx264',
                acodec='aac',
                crf=23,  # 视频质量 (0-51, 值越小质量越高)
                preset='medium'  # 编码速度/压缩率平衡
            )
            .overwrite_output()
            .run(quiet=True)
        )


if __name__ == '__main__':

    video_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test.mp4"
    # insert_video_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test2.mp4"
    # audio_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test2.wav"
    output_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\1111111111111111.mp4"
    # adjust_volume_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test_adjust_volume.wav"
    # start_time = 2
    # end_time = 4
    # VideoOpsV2.add_audio_segment_to_video(video_path, audio_path, output_path, start_time, end_time)
    # audio_path = AudioOpsV2.normalize_music_volume(audio_path)
    # VideoOpsV2.insert_video_at_time(video_path, insert_video_path, output_path, insert_time=2)
    # VideoOpsV2.resize_and_cut_video2(video_path, output_path, new_width=1280, new_height=720)
    VideoOpsV2.format_video(video_path, output_path)
    VideoOpsV2.merge_videos([video_path], output_path)

    ###########################################测试删除绿幕视频##########################################
    # green_screen_video_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_video_rmbg.mp4"
    # rm_gs_output_video_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_video_rmgs_method_test.mov"
    # fill_video_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\1 (110).mp4"
    # avve_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\填充素材测试.mp4"
    # # save_temp = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_video_rmgs_method_test_aaaaa.mp4"
    # nopv_path,bg_index = RemoveGreenScreen.remove_dynamic_greenscreen2(green_screen_video_path,rm_gs_output_video_path,is_dilation=True,tolerance=45)
    # # VideoOpsV2.convert_mov_to_mp4(rm_gs_output_video_path,save_temp)
    # RemoveGreenScreen.fill_transparent_background(fill_video_path,nopv_path,bg_index,avve_path,fully_fill=False)
    
    ############################################测试音频裁剪########################################
    # audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_audio.wav"
    # cut_audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_audio_cut.wav"
    # AudioOpsV2.clip_audio(audio_path, start_time=10, duration=5, output_path=cut_audio_path)











