from typing import List
from langchain_core.tools import BaseTool
from .tools.video_cut_tools import * 

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)



class ToolManager:
    def __init__(self):
        # 使用列表存储顺序，使用字典加速查找
        self._tools_list: List[Any] = []
        self._tools_map: dict[str, Any] = {}
        
        self._initialize_tools()

    def _initialize_tools(self):
        """初始化默认工具列表"""
        # 假设这些函数已经在外部定义好了
        default_tools = [
            # 视频剪辑工具
            clip_video,
            merge_videos,
            resize_and_cut_video,
            adjust_video_volume,
            insert_video_at_time,
            format_video,
            image_to_video,
            # 背景处理工具
            remove_green_screen,
            fill_video,
            # 音频处理工具
            add_audio_to_video,
            # 字幕工具
            add_hardsub_with_offset,
        ]
        
        for tool in default_tools:
            self.register_tool(tool)

    def register_tool(self, tool: Any):
        """
        动态注册单个工具，包含校验逻辑
        """
        # 1. 校验工具是否有 name 属性 (兼容 LangChain @tool 和自定义类)
        if not hasattr(tool, 'name'):
            logger.error(f"Failed to register tool: {tool} has no 'name' attribute.")
            return

        tool_name = tool.name
        
        # 2. 检查是否重复注册
        if tool_name in self._tools_map:
            logger.warning(f"Tool '{tool_name}' is being overwritten.")
            # 如果覆盖，先从列表中移除旧的
            self._tools_list = [t for t in self._tools_list if t.name != tool_name]

        # 3. 添加到存储
        self._tools_list.append(tool)
        self._tools_map[tool_name] = tool
        logger.info(f"Tool registered: {tool_name}")

    def get_tools(self) -> List[Any]:
        """获取所有工具列表"""
        return self._tools_list
    
    def get_tool_by_name(self, name: str) -> Optional[Any]:
        """
        根据名称获取工具 (O(1) 复杂度)
        """
        return self._tools_map.get(name)

    def list_tool_names(self) -> List[str]:
        """获取所有已注册工具的名称"""
        return list(self._tools_map.keys())