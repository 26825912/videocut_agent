"""
共享工具库 - 所有智能体通用的工具类

重构后的模块化架构:
- gpu_detection: GPU硬件检测
- video_formats: 视频格式配置
- audio_ops: 音频处理操作
- video_ops_core: 核心视频操作
- video_effects: 视频特效处理
- error_handler: 错误处理工具
- video_ops_v2_refactored: 重构后的主入口（向后兼容）

传统工具（保持兼容）:
- video_cut_tools: 视频剪切工具
- video_ops_v2: 原始视频操作工具（大文件，建议使用重构版）
"""

# Import refactored modules
try:
    from .gpu_detection import detect_gpu
    from .video_formats import VideoFormat, AudioFormat, NvidiaVideoFormat
    from .audio_ops import AudioOpsV2
    from .video_ops_core import VideoOpsCore
    from .video_effects import RemoveGreenScreen, VideoEffects
    from .error_handler import ErrorHandler, handle_errors
    from .video_ops_v2_refactored import VideoOpsV2
except ImportError:
    # 在某些情况下可能出现导入错误，这是正常的
    pass

# Import legacy tools for backward compatibility
try:
    from .video_cut_tools import VideoCutTool
    # Note: video_ops_v2 is kept for compatibility but recommend using video_ops_v2_refactored
except ImportError:
    pass

__all__ = [
    # Refactored modular components
    'detect_gpu',
    'VideoFormat',
    'AudioFormat',
    'NvidiaVideoFormat',
    'AudioOpsV2',
    'VideoOpsCore',
    'RemoveGreenScreen',
    'VideoEffects',
    'ErrorHandler',
    'handle_errors',
    'VideoOpsV2',  # Main refactored entry point

    # Legacy tools (backward compatibility)
    'VideoCutTool',
]