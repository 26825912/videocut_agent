"""
Video Format Configuration Module - Encoding and hardware acceleration settings
"""
import logging
from .gpu_detection import detect_gpu

logger = logging.getLogger(__name__)

class VideoFormat:
    """标准视频格式配置"""
    Width = 720
    Height = 1280
    Fps = 30
    bit_rate = '12000000'     # 12Mbps
    crf = '23'                # 恒定质量系数（18-28）
    preset = 'medium'         # 编码速度预设
    vcodec = 'libx264'
    pix_fmt = 'yuv420p'       # 像素格式（必须yuv420p兼容移动设备）
    round = 'up'              # 向上取整


class AudioFormat:
    """音频格式配置"""
    aac = True  # 是否使用AAC编码
    codec = 'aac'  # 音频编码格式
    bit_rate = '122000'  # 128kbps
    sample_rate = 44100  # 44.1kHz
    channels = 2  # 双声道


class NvidiaVideoFormat:
    """硬件加速视频格式配置 - 基于GPU检测自动选择"""

    def __init__(self):
        """根据检测到的GPU硬件初始化编码配置"""
        try:
            result = detect_gpu()
            self._configure_for_gpu(result)
        except Exception as e:
            logger.error(f"检测GPU失败,使用默认设置: {e}")
            self._configure_default()

    def _configure_for_gpu(self, gpu_result):
        """根据GPU检测结果配置编码参数"""
        if gpu_result['NVIDIA'] and gpu_result["System"] in ["Windows", "Linux"]:
            logger.info(f"检测到{gpu_result['System']} 操作系统和NVIDIA GPU,使用NVENC编码")
            self.pix_fmt = 'yuv420p'
            self.hwaccel = 'cuda'
            self.vcodec = 'h264_nvenc'
            self.preset = 'p3'
            self.rc = 'vbr'
            self.qd = '23'
            self.async_depth = 4

        elif gpu_result['Intel'] and gpu_result["System"] in ["Windows", "Linux"]:
            logger.info(f"检测到{gpu_result['System']} 操作系统和Intel GPU,使用QSV编码")
            self.pix_fmt = 'nv12'
            self.hwaccel = 'qsv'
            self.vcodec = 'h264_qsv'
            self.preset = 'fast'
            self.rc = 'vbr'
            self.global_quality = '23'
            self.async_depth = 4

        elif gpu_result['Intel'] and gpu_result["System"] == "Darwin":
            logger.info(f"检测到{gpu_result['System']} 操作系统和Intel GPU,使用VideoToolbox编码")
            self.pix_fmt = 'nv12'
            self.hwaccel = 'videotoolbox'
            self.vcodec = 'h264_videotoolbox'
            self.preset = 'fast'
            self.rc = 'vbr'
            self.quality = '23'

        elif gpu_result['Apple'] and gpu_result["System"] == "Darwin":
            logger.info(f"检测到{gpu_result['System']} 操作系统和Apple GPU,使用VideoToolbox编码")
            self.pix_fmt = 'nv12'
            self.hwaccel = 'videotoolbox'
            self.vcodec = 'h264_videotoolbox'
            self.preset = 'fast'
            self.rc = 'vbr'
            self.quality = '100'

        elif gpu_result['AMD'] and gpu_result["System"] in ["Windows", "Linux"]:
            logger.info(f"检测到{gpu_result['System']} 操作系统和AMD GPU,使用AMF编码")
            self.pix_fmt = 'nv12'
            self.hwaccel = 'amf'
            self.vcodec = 'h264_amf'
            self.preset = 'balanced'    # 编码预设（balanced/speed/quality）
            self.rc = 'vbr_peak'
            self.quality = '23'         # 质量优先模式（speed/balanced/quality）
        else:
            self._configure_default()

    def _configure_default(self):
        """配置默认软件编码参数"""
        logger.info("使用默认软件编码设置")
        self.pix_fmt = VideoFormat.pix_fmt
        self.vcodec = VideoFormat.vcodec
        self.preset = VideoFormat.preset
        self.crf = VideoFormat.crf