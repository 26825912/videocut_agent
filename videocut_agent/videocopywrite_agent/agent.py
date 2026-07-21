import os
import logging
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

from langchain.agents import AgentState
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .tools_manager import ToolManager 
from pydantic import BaseModel, Field

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
    result_video_path: str = Field(description="生视频的结果路径")
    audio_path: str = Field(description="生成的音频文件路径")
    ass_path: str = Field(description="生成的字幕文件路劲")
    language: str = Field(description="视频中的字幕和语音的语种")
    duration: str = Field(description="视频的时长范围")
    
    


def create_copywrite_video_agent():
    """
    构建并返回视频编辑智能体 (Agent Runnable)。
    
    参数:
        llm_api_key: OpenAI/Gemini API Key (如果未传入 llm 实例则必须提供)
        llm: 可选，已初始化好的 ChatOpenAI 实例 (推荐多智能体场景使用，以共享连接)
    返回:
        一个配置好的 Agent Runnable 对象，可直接调用 .invoke()
    """
    llm = ChatOpenAI(
        model="gpt-5.1",
        openai_api_key=GEMINI_API_KEY,
        openai_api_base=GEMINI_API_BASE, 
        temperature=0
    )
    
    tool_manager = ToolManager()
    tools = tool_manager.get_tools()
    
    system_prompt = """你是一个爆款视频仿写助手，可以更具用户输入的视频连接、仿写主题和识破时长范围仿写一个新的视频,用户没有指定的话默认使用英文
                            1.接到指令之后，确定是否有视频连接、仿写主题、时长范围信息
                            按照以下流程分别取调用工具
                            2.先仿写爆款视频文案,生成文案文件(没有指定语言的情况下默认使用英文)
                            3.根据爆款文案,生成语音文件
                            4.根据语音文件,生成字幕文件
                            5.把爆款文案文件和语音文件，生成对应的素材检索关键词和时间
                            6.根据素材检索关键词和时间,去检索素材
                            7.把素材视频合并成一个视频文件 
                            8.把视频文件,音频文件,字幕文件合并成最终的视频文件
                            """
    agent_runnable = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        response_format=ContactInfo
    )

    return agent_runnable
    


def parse_agent_output(response):
    """统一解析 Agent 返回的字典或消息列表"""

    if isinstance(response, dict):
        if "output" in response:
            return response["output"]
        elif "messages" in response and len(response["messages"]) > 0:
            return response["messages"][-1].content
    return str(response)


# @tool
def copywrite_video_agent(query):
    """
    你是一个专业的视频仿写助手，可以更具用户输入的视频连接、仿写主题和识破时长范围仿写一个新的视频
    用户没有指定语言的话默认使用英文
    """
    logger.info("🚀 Agent 启动 (Function Mode)...") 
    video_agent = create_copywrite_video_agent()
    input_payload = {"messages": [("user", query)]}
    try:
        raw_response = video_agent.invoke(input_payload)
        logger.info(f"Raw Response: {raw_response}")

        final_result = parse_agent_output(raw_response)
        logger.info(f"Output: {final_result}")
        return final_result
        
    except Exception as e:
        logger.error(f"Error: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    query = """帮我以"https://www.youtube.com/shorts/eR3JLe3wQZE?t=8&feature=share"为基础，生成一个关于美国洛杉矶租车自驾攻略的视频,目标语言是英文,时间范围20-25秒"""
    copywrite_video_agent(query)   #测试的时候将@tool注释掉



