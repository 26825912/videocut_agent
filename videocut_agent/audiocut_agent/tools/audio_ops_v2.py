import os
import subprocess
from ffmpeg_normalize import FFmpegNormalize
import platform
import ffmpeg
import logging
import tempfile
import sys
from collections import namedtuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


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
    



if __name__ == '__main__':

    video_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test.mp4"
    # insert_video_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test2.mp4"
    # audio_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test2.wav"
    output_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\1111111111111111.mp4"
    
    ############################################测试音频裁剪########################################
    # audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_audio.wav"
    # cut_audio_path = r"C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo2_audio_cut.wav"
    # AudioOpsV2.clip_audio(audio_path, start_time=10, duration=5, output_path=cut_audio_path)











