from typing import List
from langchain_core.tools import BaseTool

# 导入所有带有 @tool 装饰器的工具函数
from tools.dify_workflower.video_scripts_tools import get_video_scripts
from tools.asr_tools import asr_audio_file, get_script_text_time
from tools.subtitle_v2_tools import video2ass_tool, audio2ass_tool
from tools.tts_tools import text_to_speech_tool
from tools.image_search_tools import img_search_tool_v2
from tools.video_search_tools import video_serach_and_clip_tools
from tools.video_cut_tools import * 
from tools.dify_workflower.script_tools import *


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
            # img_search_tool_v2,
            # image_to_video_v2,
            video_serach_and_clip_tools,
            merge_videos,
            audio2ass_tool,
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
    


class AgentToolManager:
    """智能体工具管理器 - 为对话形式的智能体提供完整的工具管理功能"""
    
    def __init__(self):
        self.agent_tools = {}
        self._initialize_agent_tools()
    
    def _initialize_agent_tools(self):
        """初始化所有智能体的工具映射"""
        # 1. 视频编辑智能体
        self.agent_tools['video_edit_agent'] = [
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
        
        # 2. 字幕智能体
        self.agent_tools['subtitle_agent'] = [
            audio2ass_tool,
            video2ass_tool,
            # 语音识别工具
            # asr_audio_file,
            get_script_text_time,
        ]
        
        # 3. 音频智能体
        self.agent_tools['audio_agent'] = [
            text_to_speech_tool,
            # 音频处理工具
            clip_audio,
            concate_audios,
            adjust_audio_volume,
        ]
        
        # 4. 视频文案智能体
        self.agent_tools['video_script_agent'] = [
            get_video_scripts,
            get_script_text_time,
            video_script_analysis,
            ai_copywrite_tool,
        ]
        
        # 5. 素材检索智能体
        self.agent_tools['material_search_agent'] = [
            img_search_tool_v2,
            video_serach_and_clip_tools,
        ]
    
    def get_agent_tools(self, agent_name: str) -> List[BaseTool]:
        """根据智能体名称获取对应的工具列表"""
        if agent_name in self.agent_tools:
            logger.info(f"为智能体 '{agent_name}' 加载了 {len(self.agent_tools[agent_name])} 个工具")
            return self.agent_tools[agent_name]
        else:
            logger.warning(f"未找到智能体 '{agent_name}' 对应的工具")
            return []
    
    def get_tool_by_name(self, tool_name: str, agent_name: str = None) -> BaseTool:
        """根据工具名称获取工具，可指定智能体范围"""
        if agent_name:
            # 在指定智能体的工具中查找
            tools = self.get_agent_tools(agent_name)
            for tool in tools:
                if hasattr(tool, 'name') and tool.name == tool_name:
                    return tool
        else:
            # 在所有智能体的工具中查找
            for agent_tools in self.agent_tools.values():
                for tool in agent_tools:
                    if hasattr(tool, 'name') and tool.name == tool_name:
                        return tool
        return None
    
    def get_all_agents(self) -> List[str]:
        """获取所有可用的智能体名称"""
        return list(self.agent_tools.keys())
    
    def get_agent_tool_info(self, agent_name: str) -> Dict[str, Any]:
        """获取智能体工具的详细信息"""
        tools = self.get_agent_tools(agent_name)
        tool_info = []
        
        for tool in tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                tool_info.append({
                    'name': tool.name,
                    'description': tool.description,
                    'args': getattr(tool, 'args', {})
                })
        
        return {
            'agent_name': agent_name,
            'tool_count': len(tools),
            'tools': tool_info
        }
    
    def validate_tool_availability(self, agent_name: str, tool_name: str) -> bool:
        """验证工具是否对指定智能体可用"""
        tools = self.get_agent_tools(agent_name)
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == tool_name:
                return True
        return False
        


class ToolExecutionManager:
    """工具执行管理器 - 提供工具执行和结果处理功能"""
    
    def __init__(self, agent_tool_manager: AgentToolManager):
        self.agent_tool_manager = agent_tool_manager
        self.execution_history = []
    
    def execute_tool(self, agent_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行指定智能体的工具"""
        try:
            # 获取工具
            tool = self.agent_tool_manager.get_tool_by_name(tool_name, agent_name)
            if not tool:
                raise ValueError(f"工具 '{tool_name}' 对智能体 '{agent_name}' 不可用")
            
            # 记录执行开始
            execution_id = f"{agent_name}_{tool_name}_{len(self.execution_history)}"
            execution_record = {
                'id': execution_id,
                'agent_name': agent_name,
                'tool_name': tool_name,
                'parameters': kwargs,
                'status': 'running',
                'start_time': time.time()
            }
            self.execution_history.append(execution_record)
            
            logger.info(f"开始执行工具: {tool_name} (智能体: {agent_name})")
            
            # 执行工具
            result = tool.run(**kwargs)
            
            # 记录执行完成
            execution_record.update({
                'status': 'completed',
                'end_time': time.time(),
                'execution_time': time.time() - execution_record['start_time'],
                'result': result
            })
            
            logger.info(f"工具执行完成: {tool_name} (执行时间: {execution_record['execution_time']:.2f}s)")
            
            return {
                'success': True,
                'execution_id': execution_id,
                'result': result,
                'execution_time': execution_record['execution_time']
            }
            
        except Exception as e:
            # 记录执行失败
            execution_record.update({
                'status': 'failed',
                'end_time': time.time(),
                'execution_time': time.time() - execution_record['start_time'],
                'error': str(e)
            })
            
            logger.error(f"工具执行失败: {tool_name} (错误: {str(e)})")
            
            return {
                'success': False,
                'execution_id': execution_id,
                'error': str(e),
                'execution_time': execution_record['execution_time']
            }
    
    def get_execution_history(self, agent_name: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        history = self.execution_history.copy()
        
        if agent_name:
            history = [record for record in history if record['agent_name'] == agent_name]
        
        return history[-limit:]
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取指定执行的详细状态"""
        for record in self.execution_history:
            if record['id'] == execution_id:
                return record
        return None




if __name__ == '__main__':
    tool_manager = AgentToolManager()
    print(tool_manager.get_agent_tool_info('video_edit_agent'))
        
    
