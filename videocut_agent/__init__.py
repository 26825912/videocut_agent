"""
Videocut Agent System - AI多智能体视频制作系统

基于LangChain + LangGraph的智能体框架，支持完整视频制作流程。

主要组件:
- agents_manager: 智能体管理器
- tool_manager: 工具管理系统
- 7个专业化智能体: videocut, subtitle, audiocut, videoscript, assert_search, videogen, videocopywrite
"""

__version__ = "1.0.0"

# 导入核心管理器
try:
    from .agents_manager import AgentsManager
    from .tool_manager import ToolManager
except ImportError as e:
    # 在开发环境中可能会出现循环导入，这是正常的
    pass

__all__ = [
    'AgentsManager',
    'ToolManager',
]