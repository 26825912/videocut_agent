"""
GPU Detection Module - Hardware detection for video processing optimization
"""
import os
import platform
import subprocess
import logging

logger = logging.getLogger(__name__)

def detect_gpu():
    """
    检测系统GPU硬件信息，用于优化视频处理性能

    Returns:
        dict: GPU信息字典，包含NVIDIA、Intel、AMD、Apple等GPU信息
    """
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
        except Exception as e:
            logger.warning(f"Windows GPU检测失败: {e}")

    elif system == "Linux":
        # 使用lspci命令获取显卡信息
        try:
            output = subprocess.check_output(
                "lspci | grep VGA",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            gpu_info = output.strip().split('\n')
        except Exception as e:
            logger.warning(f"Linux GPU检测失败: {e}")

    elif system == "Darwin":  # macOS
        # 使用system_profiler命令获取显卡信息
        try:
            output = subprocess.check_output(
                "system_profiler SPDisplaysDataType",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            gpu_info = [line.strip() for line in output.split('\n') if 'Chipset Model:' in line]
        except Exception as e:
            logger.warning(f"macOS GPU检测失败: {e}")

    # 分析GPU类型
    result = {
        'NVIDIA': False,
        'Intel': False,
        'AMD': False,
        'Apple': False,
        'System': system,
        'raw_info': gpu_info
    }

    gpu_text = ' '.join(gpu_info).lower()

    if 'nvidia' in gpu_text or 'geforce' in gpu_text or 'quadro' in gpu_text:
        result['NVIDIA'] = True
    if 'intel' in gpu_text:
        result['Intel'] = True
    if 'amd' in gpu_text or 'radeon' in gpu_text:
        result['AMD'] = True
    if 'apple' in gpu_text or 'm1' in gpu_text or 'm2' in gpu_text:
        result['Apple'] = True

    logger.info(f"GPU检测结果: {result}")
    return result