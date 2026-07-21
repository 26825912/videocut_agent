import os
import logging
from dotenv import load_dotenv

from langchain.agents import AgentState
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from .tools_manager import ToolManager

# 加载.env文件
load_dotenv() 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://api.openai.com/v1")


class ContactInfo(BaseModel):
    """结构化输出的内容形式"""
    success: bool = Field(description="是否成功生成视频")
    result_script: str = Field(description="生成的最终视频文案内容")
    language: str = Field(description="文案语言")


def create_video_script_agent():
    """
    构建并返回视频脚本智能体 (Agent Runnable)。
    
    参数:
        llm_api_key: OpenAI/Gemini API Key (如果未传入 llm 实例则必须提供)
        llm: 可选，已初始化好的 ChatOpenAI 实例 (推荐多智能体场景使用，以共享连接)
        
    返回:
        一个配置好的 Agent Runnable 对象，可直接调用 .invoke()
    """
    llm = ChatOpenAI(
        model="gemini-2.5-pro",
        openai_api_key=GEMINI_API_KEY,
        openai_api_base=GEMINI_API_BASE, 
        temperature=0
    )
    
    tool_manager = ToolManager()
    tools = tool_manager.get_tools()
    
    system_prompt = """
        你是一个专业的视频文案创作助手。
        你的核心能力包括：
        - 视频文案生成，根据主题和时间范围，调用工具生成视频文案
        - 爆款视频的拆解，调用工具拆解视频文案
        - 爆款视频文案的仿写输入视频连接，仿写主题和时间可以仿写一个新的文案
        注意，在没有指定语言的情况下默认使用英文
        """
    agent_runnable = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        # response_format=ContactInfo
    )
    return agent_runnable
    

def parse_agent_output(response):
    """统一解析 Agent 返回的字典或消息列表"""

    if isinstance(response, dict):
        if "output" in response:
            return response["output"]
        elif "messages" in response and len(response["messages"]) > 0:
            # for m in response["messages"]:
            #     m.pretty_print()
            return response["messages"][-1].content
    return str(response)


@tool
def videoscript_agent(query):
    """
    文案创作助手
    适用场景：
    - “帮我写一个关于减肥的短视频脚本,视频时长大概20秒
    - “分析一下这个视频为什么会火（附链接）”
    - “模仿这个视频的风格，写一个介绍旅游产品的文案”
    最后返回结构化的文案内容
    """
    logger.info("🚀 Agent 启动 (Function Mode)...") 
    video_agent = create_video_script_agent()
    input_payload = {"messages": [("user", query)]}
    
    try:
        raw_response = video_agent.invoke(input_payload)
        final_result = parse_agent_output(raw_response)
        logger.info(f"Output: {final_result}")
        return final_result
        
    except Exception as e:
        logger.error(f"Error: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    # query = """帮我参照'https://www.youtube.com/shorts/HTAjH864sEU?t=5&feature=share'这个爆款视频进行仿写，仿写的主题是是广州自驾,视频时长范围大概20-25秒"""
    query = """https://www.youtube.com/shorts/m_OoEFR0uwI?t=2&feature=share帮我拆解一下这个视频"""
    videoscript_agent.invoke(query)   #测试的时候将@tool注释掉
    