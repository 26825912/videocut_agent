from .tools_manager import ToolManager
import os
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI

# 加载.env文件
load_dotenv()
from langchain.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage,AnyMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Annotated
from IPython.display import Image, display
import operator
from typing import Literal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://api.openai.com/v1")


# 2. 定义结构 (Pydantic) - 这就是你希望模型填充的"表格"
class ContactInfo(BaseModel):
    """提取视频生成的关键参数"""
    # success: bool = Field(description="任务是否成功完成")
    result_video_path: str = Field(description="生成的视频文件路径")
    audio_path: str = Field(description="音频文件路径")
    language: str = Field(description="视频语言", examples=["en", "zh"])
    duration: str = Field(description="视频时长范围")
    

@tool
def structure_tool_output(success: bool,
                        result_video_path: str,
                        origin_video_path: str) -> str:
    """
    结束任务时，将最后的结构化输出返回给用户
    input:
    success: 视频是否成功生成,true或false,
    result_video_path: 生成的最终视频文件路径,
    origin_video_path: 原始视频文件路径,
    """
    return {
            "success": success,
            "result_video_path": result_video_path,
            "origin_video_path": origin_video_path,
        }


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

def _create_audio_cut_agent_executor():
    model = ChatOpenAI(
        model="gemini-2.5-pro",
        openai_api_key=GEMINI_API_KEY,
        openai_api_base=GEMINI_API_BASE, 
        temperature=0
    )
    
    model.with_structured_output(ContactInfo)
    tool_manager = ToolManager()
    tools = tool_manager.get_tools()
    tools.append(structure_tool_output)
    tools_by_name = {tool.name: tool for tool in tools}
    model_with_tools = model.bind_tools(tools)


    def tool_node(state: dict):
        """Performs the tool call"""
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}
    

    def llm_call(state: dict):
        """LLM decides whether to call a tool or not"""
        return {
            "messages": [
                model_with_tools.invoke(
                    [
                        SystemMessage(
                            content="""
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
                        )
                    ]
                    + state["messages"]
                )
            ],
            "llm_calls": state.get('llm_calls', 0) + 1
        }
    
    def should_continue(state: MessagesState) -> Literal["tool_node", END]:
        """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
        print('should_continue:', state)
        messages = state["messages"]
        last_message = messages[-1]
        # If the LLM makes a tool call, then perform an action
        if last_message.tool_calls:
            return "tool_node"
        # Otherwise, we stop (reply to the user)
        return END
    

    agent_builder = StateGraph(MessagesState)
    agent_builder.add_node("llm_call", llm_call)  # Add node for llm_call
    agent_builder.add_node("tool_node", tool_node)
    
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        ["tool_node", END]
    )
    agent_builder.add_edge("tool_node", "llm_call")
    agent = agent_builder.compile()

    return agent


# def should_continue(state: MessagesState) -> Literal["tool_node", END]:
#     """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
#     print('should_continue:', state)
#     messages = state["messages"]
#     last_message = messages[-1]

#     # 检查是否调用了structure_tool_output工具
#     if last_message.tool_calls:
#         for tool_call in last_message.tool_calls:
#             if tool_call["name"] == "structure_tool_output":
#                 # 如果是structure_tool_output工具调用，直接结束
#                 return END
#         return "tool_node"

#     return END


_CACHED_ASSERT_SEARCH_AGENT = _create_audio_cut_agent_executor()


@tool
def video_cut_agent(quiry: str):
    """
    视频剪辑助手
    核心能力
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
    """

    config = {"recursion_limit": 45}
    initial_messages = [HumanMessage(content=quiry)]
    messages = _CACHED_ASSERT_SEARCH_AGENT.invoke({"messages": initial_messages},config=config)
    
    result_content = messages["messages"][-2].content

    return result_content
# Show the agent
# display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
# print('agent graph:', agent.get_graph().draw_mermaid())

if __name__ == "__main__":
    # 测试代码
    print("Invoking Tool directly...")
    result = video_cut_agent(
        "将videos\北京路步行街_298643.mp4裁剪前2秒", 
    )
    print("\nFINAL TOOL OUTPUT:", result)


# for m in messages["messages"]:
#     m.pretty_print()


