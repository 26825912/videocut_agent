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
from tools_manager import ToolManager 

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
    origin_video_path: str = Field(description="原始视频文件路径")
    

def create_video_editor_agent():
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
    你是一个专业的视频编辑助手，专门处理视频剪辑、合并、调整、格式转换等任务。
    你可以处理以下类型的任务：
    - 视频裁剪：裁剪视频片段、调整视频时长
    - 视频合并：将多个视频文件合并为一个
    - 视频调整：调整视频音量、尺寸、格式
    - 背景处理：去除绿幕、填充背景
    - 音频添加：为视频添加背景音乐或音效
    - 字幕添加：为视频添加硬字幕
    - 调整视频音量：增加或减少视频音量
    - 在视频中插入其他视频片段
    - 图片转换为静态视频
    - 缩放视频到指定尺寸
    
    请根据用户的具体需求选择合适的工具，并确保提供必要的参数。
    """
    
    agent_runnable = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        response_format = ContactInfo
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
def videocut_agent(query):
    """
    视频剪辑子智能体。
    可以处理一下任务
    - 视频裁剪：
    - 视频合并：
    - 视频调整：
    - 背景处理：去除绿幕、填充背景
    - 音频添加：
    - 字幕添加：
    - 调整视频音量：
    - 在视频中插入其他视频片段：
    - 图片转换为静态视频：
    - 缩放视频到指定尺寸：
    """
    logger.info("🚀 Agent 启动 (Function Mode)...") 
    video_agent = create_video_editor_agent()
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
    query = "帮我将'result_video\clip_video\cat_44d0b594-1ada-4d73-9f04-ed584fc9e87c.mp4'这个视频裁剪出前2秒"
    videocut_agent(query)   #测试的时候将@tool注释掉
    