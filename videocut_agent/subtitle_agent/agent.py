import os
import logging
from dotenv import load_dotenv

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
    success: bool = Field(description="处理是否成功")
    result_subtitle_path: str = Field(description="处理后的结果字幕路径")
    # subtitle: str = Field(description="字幕内容")


def create_subtitle_editor_agent():
    """
    构建并返回音频编辑智能体 (Agent Runnable)。
    
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
        你是一个专业字幕编辑助手
        你的核心能力是：
        语音文件转ass字幕文件
        视频文件转ass字幕文件
        """
    
    agent_runnable = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        response_format=ContactInfo,
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
def subtitle_editor_agent(query):
    """
    字幕编辑助手：
    核心能力
    语音文件转ass字幕文件
    视频文件转ass字幕文件
    """
    logger.info("🚀 Agent 启动 (Function Mode)...") 
    subtitle_agent = create_subtitle_editor_agent()
    input_payload = {"messages": [("user", query)]}
    
    try:
        raw_response = subtitle_agent.invoke(input_payload)
        final_result = parse_agent_output(raw_response)
        logger.info(f"Output: {final_result}")
        return final_result
        
    except Exception as e:
        logger.error(f"Error: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    query = "result_video/clip_audio/0eec12da-7fa7-4540-a13e-f184e0afe7dd.mp3将这个音频文件转换成字幕"
    subtitle_editor_agent(query)   #测试的时候将@tool注释掉
    