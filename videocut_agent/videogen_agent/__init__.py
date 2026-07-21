"""
VideoGen Agent - 视频生成智能体

专门负责视频合成、特效添加和视频生成的智能体。

功能:
- 视频合成和渲染
- 特效添加
- 视频质量优化
- 视频导出
"""

try:
    from .agent import VideoGenAgent
    from .graph import generate_video_agent
except ImportError:
    pass

__all__ = [
    'VideoGenAgent',
    'generate_video_agent',
]