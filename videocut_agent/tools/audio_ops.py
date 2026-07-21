"""
Audio Operations Module - Audio processing and manipulation functions
"""
import os
import logging
import ffmpeg
from ffmpeg_normalize import FFmpegNormalize
from .error_handler import ErrorHandler, handle_errors

logger = logging.getLogger(__name__)

class AudioOpsV2:
    """音频操作工具类"""

    @staticmethod
    @handle_errors(error_types={FileNotFoundError: None})
    def get_audio_duration(file_path):
        """
        使用 ffmpeg-python 获取音频文件的时长（以秒为单位）

        Args:
            file_path (str): 音频文件的路径

        Returns:
            float: 文件时长，如果出错则返回 None
        """
        # 验证文件存在
        ErrorHandler.validate_file_exists(file_path, "音频文件")

        try:
            probe_output = ffmpeg.probe(file_path)
            duration = float(probe_output['format']['duration'])
            return duration

        except ffmpeg.Error as e:
            logger.error(f"处理文件时出错: {e.stderr.decode('utf8') if e.stderr else e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"无法从文件信息中找到时长: {e}")
            return None

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def concatenate_audio_files(input_files, output_file):
        """
        使用 ffmpeg-python 实现的快速拼接 (Stream Copy)
        无需重编码，速度极快

        Args:
            input_files (list): 输入音频文件列表
            output_file (str): 输出文件路径

        Returns:
            str: 输出文件路径，失败则返回None
        """
        if not input_files:
            logger.error("输入文件列表为空")
            return None

        # 验证所有输入文件存在
        for file_path in input_files:
            ErrorHandler.validate_file_exists(file_path, "输入音频文件")

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_file))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        list_filename = 'inputs.txt'
        try:
            # 创建文件列表
            with open(list_filename, 'w', encoding='utf-8') as f:
                for path in input_files:
                    abs_path = os.path.abspath(path).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")

            # 执行拼接
            (
                ffmpeg
                .input(list_filename, format='concat', safe=0)
                .output(output_file, c='copy')
                .overwrite_output()  # 对应 -y 参数，允许覆盖
                .run(quiet=True)
            )

            logger.info(f"音频拼接成功: {output_file}")
            return output_file

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg 执行错误: {e}")
            return None
        except Exception as e:
            logger.error(f"拼接音频时发生错误: {e}")
            return None
        finally:
            # 清理临时文件
            if os.path.exists(list_filename):
                try:
                    os.remove(list_filename)
                except OSError as e:
                    logger.warning(f"清理临时文件失败: {e}")

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def normalize_music_volume(input_audio_path, output_audio_path):
        """
        预处理音乐文件：将其响度统一为 -14 LUFS，并生成一个临时文件

        Args:
            input_audio_path (str): 输入音频文件路径
            output_audio_path (str): 输出音频文件路径

        Returns:
            str: 输出文件路径，失败则返回None
        """
        # 验证输入文件存在
        ErrorHandler.validate_file_exists(input_audio_path, "输入音频文件")

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_audio_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        logger.info(f"⏳ 正在标准化音频: {input_audio_path} -> {output_audio_path}")

        try:
            # 初始化标准化器
            normalizer = FFmpegNormalize(
                target_level=-14,   # 目标 LUFS
                print_stats=False,
                true_peak=-1.0,     # 峰值限制
            )

            # 执行标准化
            normalizer.add_media_file(input_audio_path, output_audio_path)
            normalizer.run_normalization()

            logger.info(f"✅ 音频标准化完成: {output_audio_path}")
            return output_audio_path

        except Exception as e:
            logger.error(f"音频标准化失败: {e}")
            return None

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def adjust_audio_volume(input_path, output_path, volume_factor=1.0):
        """
        调整音频音量并防止失真 (使用限制器)

        Args:
            input_path (str): 输入音频文件路径
            output_path (str): 输出音频文件路径
            volume_factor (float): 音量系数，1.0为原音量

        Returns:
            str: 输出文件路径，失败则返回None
        """
        # 验证输入文件存在
        ErrorHandler.validate_file_exists(input_path, "输入音频文件")

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        try:
            stream = ffmpeg.input(input_path)

            # 先调整音量
            stream = stream.filter('volume', volume_factor)
            # 使用限制器防止失真
            stream = stream.filter('alimiter', limit=1.0, level_in=1.0, level_out=1.0)

            stream = ffmpeg.output(stream, output_path)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)

            logger.info(f"音频音量调整完成: {output_path} (系数: {volume_factor})")
            return output_path

        except ffmpeg.Error as e:
            logger.error(f"调整音频音量失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理音频时发生未知错误: {e}")
            return None