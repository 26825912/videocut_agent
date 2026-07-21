from typing import List, Dict, Optional, Any
import logging
from langchain_core.tools import BaseTool

# 导入各个子智能体
from subtitle_agent.agent import subtitle_editor_agent
from videoscript_agent.agent import videoscript_agent
from audiocut_agent.graph import audio_cut_agent
from videocut_agent.graph import video_cut_agent
from videogen_agent.graph import generate_video_agent
from assert_search_agent.graph import assert_search_agent
from videocopywrite_agent.graph import generate_copywrite_video_agent



# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentManager:
    """智能体管理器，将子智能体作为工具进行管理"""
    
    def __init__(self):
        """初始化智能体管理器"""
        self.agents: List[BaseTool] = []
        self.agent_dict: Dict[str, BaseTool] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """初始化所有智能体工具"""
        # 初始化各个子智能体作为工具
        agents_to_register = [
            video_cut_agent,
            subtitle_editor_agent,
            videoscript_agent,
            audio_cut_agent,
            assert_search_agent,
            generate_video_agent,
            generate_copywrite_video_agent
        ]
        
        for agent in agents_to_register:
            self.register_agent(agent)
    
    def register_agent(self, agent: BaseTool) -> bool:
        """注册智能体工具
        Args:
            agent: 要注册的智能体工具
        Returns:
            bool: 注册是否成功
        """
        try:
            agent_name = agent.name if hasattr(agent, 'name') else str(agent)
            
            # 检查智能体名称是否已存在
            if agent_name in self.agent_dict:
                logger.warning(f"智能体 {agent_name} 已存在，跳过注册")
                return False
            
            # 验证智能体是否具有必要的方法
            if not hasattr(agent, '_run') and not hasattr(agent, 'run'):
                logger.error(f"智能体 {agent_name} 缺少必要的运行方法")
                return False
            
            self.agents.append(agent)
            self.agent_dict[agent_name] = agent
            logger.info(f"成功注册智能体: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"注册智能体失败: {e}")
            return False
    
    def get_agents(self) -> List[BaseTool]:
        """获取所有智能体工具列表
        
        Returns:
            List[BaseTool]: 智能体工具列表
        """
        return self.agents.copy()
    
    def get_agent_by_name(self, name: str) -> Optional[BaseTool]:
        """根据名称获取智能体工具
        
        Args:
            name: 智能体名称
            
        Returns:
            Optional[BaseTool]: 找到的智能体工具，未找到返回None
        """
        return self.agent_dict.get(name)
    
    def list_agent_names(self) -> List[str]:
        """列出所有智能体名称
        
        Returns:
            List[str]: 智能体名称列表
        """
        return list(self.agent_dict.keys())
    

if __name__ == "__main__":
    # 获取智能体管理器
    manager = AgentManager()
    
    # 列出所有智能体名称
    agent_names = manager.list_agent_names()
    print("可用的智能体:", agent_names)
    
    # 获取智能体列表
    agents = manager.get_agents()
    print(f"共 {len(agents)} 个智能体")
    
    # 测试获取特定智能体
    video_agent = manager.get_agent_by_name("videocut_agent")
    if video_agent:
        print("找到视频编辑智能体")