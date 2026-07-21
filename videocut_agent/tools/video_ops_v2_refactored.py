"""
Refactored Video Operations Module - Main entry point for video processing

This module serves as the main entry point, importing from the new focused modules:
- gpu_detection: Hardware detection for optimization
- video_formats: Encoding and format configurations
- audio_ops: Audio processing operations
- video_ops_core: Core video manipulation functions
- video_effects: Advanced effects and green screen removal
"""

# Import all the refactored modules
from .gpu_detection import detect_gpu
from .video_formats import VideoFormat, AudioFormat, NvidiaVideoFormat
from .audio_ops import AudioOpsV2
from .video_ops_core import VideoOpsCore
from .video_effects import RemoveGreenScreen, VideoEffects
from .error_handler import ErrorHandler, handle_errors

# For backward compatibility, expose the main classes
class VideoOpsV2(VideoOpsCore):
    """
    Main video operations class - extends VideoOpsCore with additional functionality

    This class maintains backward compatibility while providing access to all
    the refactored video processing capabilities.
    """

    # Audio operations (delegated to AudioOpsV2)
    @staticmethod
    def get_audio_duration(file_path):
        """Get audio file duration in seconds"""
        return AudioOpsV2.get_audio_duration(file_path)

    @staticmethod
    def concatenate_audio_files(input_files, output_file):
        """Concatenate multiple audio files"""
        return AudioOpsV2.concatenate_audio_files(input_files, output_file)

    @staticmethod
    def normalize_music_volume(input_audio_path, output_audio_path):
        """Normalize audio volume to -14 LUFS"""
        return AudioOpsV2.normalize_music_volume(input_audio_path, output_audio_path)

    @staticmethod
    def adjust_audio_volume(input_path, output_path, volume_factor=1.0):
        """Adjust audio volume with limiter to prevent distortion"""
        return AudioOpsV2.adjust_audio_volume(input_path, output_path, volume_factor)


# Export all the important classes and functions for easy access
__all__ = [
    'VideoOpsV2',
    'AudioOpsV2',
    'VideoOpsCore',
    'RemoveGreenScreen',
    'VideoEffects',
    'VideoFormat',
    'AudioFormat',
    'NvidiaVideoFormat',
    'detect_gpu',
    'ErrorHandler',
    'handle_errors'
]