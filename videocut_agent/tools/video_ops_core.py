"""
Core Video Operations Module - Main video processing and manipulation functions
"""
import os
import cv2
import logging
import ffmpeg
import numpy as np
from .error_handler import ErrorHandler, handle_errors
from .video_formats import VideoFormat, NvidiaVideoFormat

logger = logging.getLogger(__name__)

class VideoOpsCore:
    """核心视频操作工具类"""

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def get_video_info(video_path):
        """
        获取视频信息，优先使用ffmpeg，失败时使用opencv备用

        Args:
            video_path (str): 视频文件路径

        Returns:
            dict: 视频信息字典，包含duration, width, height, fps等
        """
        if not video_path:
            logger.error('get_video_info输入路径为空')
            raise ValueError('get_video_info输入路径为空')

        # 验证文件存在
        ErrorHandler.validate_file_exists(video_path, "视频文件")

        # 首先尝试使用ffmpeg获取信息
        try:
            result = ffmpeg.probe(video_path)
            video_info = {
                'duration': float(result['format']['duration']),
                'bit_rate': int(result['format']['bit_rate']),
                'size': int(result['format']['size']),
                'width': result['streams'][0]['width'],
                'height': result['streams'][0]['height'],
                'fps': result['streams'][0]['avg_frame_rate'],
            }
            logger.info(f'获取视频信息成功: {video_info}')
            return video_info

        except Exception as e:
            logger.error(f'ffmpeg获取视频信息失败，使用opencv重新获取: {str(e)}')

            # 使用opencv作为备用方案
            return VideoOpsCore._get_video_info_opencv(video_path)

    @staticmethod
    def _get_video_info_opencv(video_path):
        """使用opencv获取视频信息（备用方案）"""
        # 验证文件存在
        if not os.path.exists(video_path):
            logger.error(f'视频文件不存在: {video_path}')
            raise FileNotFoundError(f'视频文件不存在: {video_path}')

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f'无法打开视频文件: {video_path}')
            raise ValueError(f'无法打开视频文件，可能文件已损坏或格式不支持: {video_path}')

        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

            # 验证获取的参数有效性
            if fps <= 0:
                logger.error(f'无效的帧率: {fps}')
                raise ValueError(f'视频帧率无效: {fps}')

            if frame_count <= 0:
                logger.error(f'无效的帧数: {frame_count}')
                raise ValueError(f'视频帧数无效: {frame_count}')

            duration = frame_count / fps
            video_info = {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps,
            }

            logger.info(f'使用opencv重新获取视频信息成功: {video_info}')
            return video_info

        finally:
            cap.release()

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def format_video(input_path, format_output_path, is_alpha=False,
                     pad_or_crop='crop', force_original_aspect_ratio='increase'):
        """
        简单格式化视频（仅处理视频）

        Args:
            input_path (str): 输入视频文件的路径
            format_output_path (str): 格式化后的视频保存路径
            is_alpha (bool): 是否处理透明度通道
            pad_or_crop (str): 填充或裁剪视频 ('pad' 或 'crop')
            force_original_aspect_ratio (str): 强制保持原始宽高比 ('decrease' 或 'increase')

        Returns:
            str: 输出文件路径，失败则返回None
        """
        # 验证输入文件
        ErrorHandler.validate_file_exists(input_path, "输入视频文件")

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(format_output_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        # 验证参数
        if pad_or_crop not in ['pad', 'crop']:
            logger.error('format_video pad_or_crop参数错误,请输入pad或crop')
            raise ValueError('format_video pad_or_crop参数错误,请输入pad或crop')

        try:
            # 构建ffmpeg处理流
            input_stream = ffmpeg.input(input_path).video

            # 缩放处理
            input_stream = input_stream.filter(
                'scale',
                width=VideoFormat.Width,
                height=VideoFormat.Height,
                force_original_aspect_ratio=force_original_aspect_ratio
            )

            # 填充或裁剪处理
            if pad_or_crop == "pad":
                input_stream = input_stream.filter(
                    'pad', VideoFormat.Width, VideoFormat.Height,
                    '(ow-iw)/2', '(oh-ih)/2'
                )
            elif pad_or_crop == "crop":
                input_stream = input_stream.filter(
                    'crop', VideoFormat.Width, VideoFormat.Height,
                    '(iw-ow)/2', '(ih-oh)/2'
                )

            # 帧率处理
            input_stream = input_stream.filter(
                'fps', fps=VideoFormat.Fps, round=VideoFormat.round
            )

            # 根据硬件配置选择编码参数
            nvidia_format = NvidiaVideoFormat()
            if hasattr(nvidia_format, 'vcodec') and nvidia_format.vcodec == 'h264_nvenc':
                ffmpeg_args = {
                    'vcodec': nvidia_format.vcodec,
                    'qp': getattr(nvidia_format, 'qd', '23'),
                    'preset': nvidia_format.preset,
                }
            elif hasattr(nvidia_format, 'vcodec') and 'qsv' in nvidia_format.vcodec:
                ffmpeg_args = {
                    'vcodec': nvidia_format.vcodec,
                    'global_quality': getattr(nvidia_format, 'global_quality', '23'),
                    'preset': nvidia_format.preset,
                }
            else:
                ffmpeg_args = {
                    'vcodec': VideoFormat.vcodec,
                    'preset': VideoFormat.preset,
                    'crf': VideoFormat.crf,
                }

            # 输出设置
            output_stream = ffmpeg.output(input_stream, format_output_path, **ffmpeg_args)
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

            logger.info(f"视频格式化完成: {format_output_path}")
            return format_output_path

        except ffmpeg.Error as e:
            logger.error(f"视频格式化失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理视频时发生未知错误: {e}")
            return None

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def resize_and_cut_video(input_path, output_path, width, height, crop=False):
        """
        调整视频尺寸并可选择裁剪

        Args:
            input_path (str): 输入视频文件路径
            output_path (str): 输出视频文件路径
            width (int): 目标宽度
            height (int): 目标高度
            crop (bool): 是否裁剪

        Returns:
            str: 输出文件路径，失败则返回None
        """
        # 验证输入文件
        ErrorHandler.validate_file_exists(input_path, "输入视频文件")

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        try:
            input_stream = ffmpeg.input(input_path)

            if crop:
                # 先缩放再裁剪到目标尺寸
                input_stream = input_stream.filter('scale', width, height, force_original_aspect_ratio='increase')
                input_stream = input_stream.filter('crop', width, height)
            else:
                # 直接缩放到目标尺寸
                input_stream = input_stream.filter('scale', width, height)

            output_stream = ffmpeg.output(input_stream, output_path)
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

            logger.info(f"视频尺寸调整完成: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            logger.error(f"调整视频尺寸失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理视频时发生未知错误: {e}")
            return None

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def clip_video(input_path, output_path, start_time=0, cut_duration=None, save_audio=True):
        """
        剪切视频片段

        Args:
            input_path (str): 输入视频文件路径
            output_path (str): 输出视频文件路径
            start_time (float): 开始时间（秒）
            cut_duration (float): 剪切时长（秒），None表示到结尾
            save_audio (bool): 是否保留音频

        Returns:
            str: 输出文件路径，失败则返回None
        """
        # 验证输入文件
        ErrorHandler.validate_file_exists(input_path, "输入视频文件")

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        try:
            input_stream = ffmpeg.input(input_path, ss=start_time)

            if cut_duration:
                input_stream = input_stream.output(
                    output_path,
                    t=cut_duration,
                    c='copy' if save_audio else None,
                    an=None if save_audio else True
                )
            else:
                input_stream = input_stream.output(
                    output_path,
                    c='copy' if save_audio else None,
                    an=None if save_audio else True
                )

            ffmpeg.run(input_stream, overwrite_output=True, quiet=True)

            logger.info(f"视频剪切完成: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            logger.error(f"剪切视频失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理视频时发生未知错误: {e}")
            return None