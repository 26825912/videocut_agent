import os
import logging
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from tools_manager import ToolManager

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
    search_keywords: str = Field(description="素材检索的关键词列表")
    search_time: str = Field(description="素材检索的时间范围列表")
    search_type: str = Field(description="素材检索的类型, 图像搜索或视频搜索")


def create_assert_search_agent():
    """
    构建并返回素材检索智能体 (Agent Runnable)。
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
        你是一个专业的素材检索助手，专门处理图像和视频素材的搜索和获取。
        你可以处理以下类型的任务：
        - 图像搜索：根据关键词搜索相关图片素材
        - 视频搜索：根据关键词搜索相关视频素材
        注意如果关键词检索不到素材的时候,可替换一个相关的关键词进行搜索
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
def assert_search_agent(query):
    """
    素材检索助手
    目前支持图像搜索和视频搜索
    """
    logger.info("🚀 Agent 启动 (Function Mode)...") 
    assert_search_agent = create_assert_search_agent()
    input_payload = {"messages": [("user", query)]}
    
    try:
        raw_response = assert_search_agent.invoke(input_payload)
        final_result = parse_agent_output(raw_response)
        logger.info(f"Output: {final_result}")
        return final_result
        
    except Exception as e:
        logger.error(f"Error: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    query = """帮我搜索关于'鸟'的视频素材,时长为是5秒"""
    assert_search_agent(query)   #测试的时候将@tool注释掉
    