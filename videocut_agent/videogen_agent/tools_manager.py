from typing import List
from langchain_core.tools import BaseTool

# 导入所有带有 @tool 装饰器的工具函数
from .tools.video_scripts_tools import get_video_scripts
from .tools.asr_tools import get_script_text_time
from .tools.subtitle_v2_tools import audio2ass_tool
from .tools.tts_tools import text_to_speech_tool
from .tools.video_search_tools import video_serach_and_clip_tools
from .tools.video_cut_tools import * 


class ToolManager:
    def __init__(self):
        self.tools = []
        self._initialize_tools()
    
    def _initialize_tools(self):
        """初始化所有工具"""
        # 直接添加已经用 @tool 装饰器装饰过的函数
        self.tools.extend([
            get_video_scripts,
            get_script_text_time,
            text_to_speech_tool,
            audio2ass_tool,
            # img_search_tool_v2,
            # image_to_video_v2,
            video_serach_and_clip_tools,
            merge_videos,
            add_hardsub_with_offset,
            add_audio_to_video,
        ])
    def get_tools(self) -> List[BaseTool]:
        """获取所有工具"""
        return self.tools
    
    def get_tool_by_name(self, name: str) -> BaseTool:
        """根据名称获取工具"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
