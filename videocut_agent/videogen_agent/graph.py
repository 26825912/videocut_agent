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
    result_video_path: str = Field(description="生成的视频文件路径")
    audio_path: str = Field(description="音频文件路径")
    language: str = Field(description="视频语言", examples=["en", "zh"])
    duration: str = Field(description="视频时长范围")
    # success: bool = Field(description="任务是否成功完成")

@tool
def structure_tool_output(success: bool,
                        result_video_path: str,
                        theme: str,
                        language: str,
                        duration:str) -> str:
    """
    结束任务时，将最后的结构化输出返回给用户
    input:
    success: 视频是否成功生成，true或false,
    result_video_path: 结果视频路劲,
    theme: 视频主题,
    language:目标语言，中文、英文
    duration:视频时长范围,15-20
    """
    return {
        "success": success,
        "result_video_path": result_video_path,
        "theme": theme,
        "language": language,
        "duration": duration
        }


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

def _create_videogen_agent_executor():
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
                            你是一个通用tiktok短视频生成助手，你可以根据主题和时间要求生成对应的短视频
                            注意：在没有指定语言时，默认使用英文，只能选择中文或英文
                            1.根据主题和时间要求,生成对应的文案
                            2.将文案转换为语音
                            3.根据文案和语音,生成素材检索关键词和视频时长
                            4.检索素材，并合并素材视频
                            5.生成字幕文件
                            6.将语音添加到视频中
                            7.将字幕添加到视频中
                            8.最后将结果内容结构化输出
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
        # print('should_continue:', state)
        messages = state["messages"]
        last_message = messages[-1]
        print('last_message:', last_message,'/n')
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
    # Set the recursion limit
    agent = agent_builder.compile()

    return agent



_CACHED_VIDEO_AGENT = _create_videogen_agent_executor()

class VideoGenerationInput(BaseModel):
    """视频生成工具的输入参数定义"""
    theme: str = Field(description="视频主题或内容概要")
    duration: str = Field(description="视频时长范围，例如 '10-15秒'")
    target_language: str = Field(description="目标视频语言，默认值为 '英文'，可选值为（英文，中文），必须在可选值内", default="英文")


@tool(args_schema=VideoGenerationInput)
def generate_video_agent(theme: str, duration: str, target_language: str = "英文") -> str:
    """
    全自动通用视频生成智能体。
    输入参数：
    - theme: 视频主题或内容概要
    - duration: 视频时长范围，例如 '10-15秒'
    - target_language: 目标视频语言，默认值为 '英文'，可选值为（英文，中文），必须在可选值内
    返回：包含生成的视频路径的 JSON 字符串。
    """
    prompt_content = f"""帮我制作一个视频。主题是：{theme}。时间范围：{duration}。目标语言是：{target_language}。"""
    config = {"recursion_limit": 80}
    initial_messages = [HumanMessage(content=prompt_content)]
    messages = _CACHED_VIDEO_AGENT.invoke({"messages": initial_messages},config=config)
    result_content = messages["messages"][-2].content #返回结构化后的结果输出

    return result_content
# Show the agent
# display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
# print('agent graph:', agent.get_graph().draw_mermaid())

if __name__ == "__main__":
    # 测试代码
    print("Invoking Tool directly...")
    result = generate_video_agent.invoke({
        "theme": "介绍量子物理", 
        "duration": "10-15秒", 
        "target_language": "中文",
    })
    print("\nFINAL TOOL OUTPUT:", result)


# for m in messages["messages"]:
#     m.pretty_print()


