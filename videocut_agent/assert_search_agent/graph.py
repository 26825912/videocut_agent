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
                        serach_results: str,
                        keywords: str,
                        durations:str) -> str:
    """
    结束任务时，将最后的结构化输出返回给用户
    input:
    success: 视频是否成功生成，true或false,
    serach_result: 搜索结果列表,
    keywords: 搜索关键词列表,
    duration:视频时长列表,15-20
    """
    return {
            "success": success,
            "serach_result": serach_results,
            "keywords": keywords,
            "duration": durations
        }


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

def _create_assert_search_agent_executor():
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
                            你是一个专业的素材检索助手，专门处理图像和视频素材的搜索和获取。
                            你可以处理以下类型的任务：
                            - 图像搜索：根据关键词搜索相关图片素材
                            - 视频搜索：根据关键词搜索相关视频素材
                            注意：如果关键词检索不到替换一个同义关键词进行检索
                            例如：
                            关键词：“cat”检索不到结果的时候，则替换为"small cat"
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


_CACHED_ASSERT_SEARCH_AGENT = _create_assert_search_agent_executor()

class AssertSearchInput(BaseModel):
    """视频生成工具的输入参数定义"""
    serach_keywards: str = Field(description="用于搜索素材的关键词，例如 '量子物理'")
    duration: str = Field(description="视频时长范围，例如 '10-15秒'")


@tool(args_schema=AssertSearchInput)
def assert_search_agent(serach_keywards: str, duration: str) -> str:
    """
    素材检索智能体
    """
    prompt_content = f"""帮我检索素材。关键词是：{serach_keywards},该素材的时间长度是：{duration}。"""
    
    initial_messages = [HumanMessage(content=prompt_content)]

    messages = _CACHED_ASSERT_SEARCH_AGENT.invoke({"messages": initial_messages})
    result_content = messages["messages"][-2].content

    return result_content
# Show the agent
# display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
# print('agent graph:', agent.get_graph().draw_mermaid())

if __name__ == "__main__":
    # 测试代码
    print("Invoking Tool directly...")
    result = assert_search_agent.invoke({
        "serach_keywards": " 量子计算", 
        "duration": " 20秒", 
    })
    print("\nFINAL TOOL OUTPUT:", result)


# for m in messages["messages"]:
#     m.pretty_print()


