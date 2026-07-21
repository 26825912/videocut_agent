"""Video operations utilities for subtitle agent."""

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VideoFormat:
    """标准视频格式配置"""
    Width = 780
    Height = 1280
