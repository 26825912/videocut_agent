import os
import logging
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

from langchain.agents import AgentState
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from .tools_manager import ToolManager 

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
    result_video_path: str = Field(description="生成的最终视频文件路径")
    theme: str = Field(description="视频主题")
    duration: int = Field(description="视频时长")
    language: str = Field(description="视频语言")


def create_video_gen_agent():
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
    
    system_prompt = """
    你是一个通用tiktok短视频生成助手，你可以根据主题和时间要求生成对应的短视频
    1.接到指令后,将指令整理成指令和视频时长参数
    2.根据主题和时间要求,生成对应的文案
    3.将文案转换为语音
    4.根据文案和语音,生成素材检索关键词和视频时长
    5.检索素材，并合并素材视频
    6.生成字幕文件
    7.将语音添加到视频中
    8.将字幕添加到视频中
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


@tool
def videogen_agent(query):
    """
    通用视频生成助手
    """
    logger.info("🚀 Agent 启动 (Function Mode)...") 
    video_agent = create_video_gen_agent()
    input_payload = {"messages": [("user", query)]}
    
    try:
        raw_response = video_agent.invoke(input_payload)
        final_result = parse_agent_output(raw_response)
        logger.info(f"Output: {final_result}")
        return final_result
        
    except Exception as e:
        logger.error(f"Error: {e}")


def videogen_agent_stream(query):
    """
    通用视频生成助手
    """
    logger.info("🚀 Agent 启动 (Function Mode)...") 
    video_agent = create_video_gen_agent()
    input_payload = {"messages": [("user", query)]}
    
    try:
        raw_response = video_agent.stream(input_payload)
        for chunk in raw_response:
            yield chunk
        
    except Exception as e:
        logger.error(f"Error: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    query = "帮我以广州自驾游生成一个15-20秒的视频"
    # videogen_agent.invoke(query)   #测试的时候将@tool注释掉
    for chunk in videogen_agent_stream(query):
        for step, data in chunk.items():
            print(f"step: {step}")
            print(f"content: {data['messages'][-1].content_blocks}")
    