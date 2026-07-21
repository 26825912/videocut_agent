"""
VideoScript Agent - 脚本生成智能体

专门负责视频脚本创作和文案生成的智能体。

功能:
- 视频脚本生成
- 文案创作
- 内容策划
- 脚本优化
"""

try:
    from .agent import VideoScriptAgent
except ImportError:
    pass

__all__ = [
    'VideoScriptAgent',
]