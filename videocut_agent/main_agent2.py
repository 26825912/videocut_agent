import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 1. 导入新的统一构建函数
from langchain.agents import create_agent, AgentState
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.agents.middleware import before_model
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from typing import Any
from agents_manager import AgentManager 

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://api.openai.com/v1")



@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]

    if len(messages) <= 5:
        return None  # No changes needed

    first_msg = messages[0]
    recent_messages = messages[-5:] if len(messages) % 2 == 0 else messages[-6:]
    new_messages = [first_msg] + recent_messages

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }


class MainAgent:
    def __init__(self,model="gpt-5.1"):#gemini-2.5-pro
        # --- 1. 初始化 LLM ---
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=GEMINI_API_KEY,
            openai_api_base=GEMINI_API_BASE, 
            temperature=0
        )
        # --- 2. 获取工具 ---
        self.agents_manager = AgentManager()
        self.agents = self.agents_manager.agents
        # --- 3. 初始化 Agent (LangChain 1.2 新标准) ---
        # create_agent 替代了 旧版agent + agent_executor 的组合
        # 它内置了循环、错误处理和工具调用逻辑
        self.main_agent = create_agent(
            model=self.llm,
            tools=self.agents,
            system_prompt="""
                        你是一名管理者，能够清晰的理解用户意图，并根据意图将任务分配给旗下的智能体团队。
                        注意：
                        1. 你只能指挥旗下的智能体团队完成任务，不能直接与用户交互。
                        2. 用户没有指定语言的话默认使用英文(必须注意)，默认使用英文(必须注意)，默认使用英文(必须注意)
                        你的核心能力包括：
                        1.`generate_video_agent` 通用生成视频。
                        例如：帮我创作一个如何学习的15-20秒以内的文案

                        2.generate_copywrite_video_agent 爆款视频仿写
                        例如:https://www.youtube.com/shorts/m_OoEFR0uwI?feature=share仿写一个以早期为主题的视频，视频时长15秒左右

                        3.assert_search_agent 素材检索助手
                        例如：帮我检索一下关于如何学习的视频素材

                        4.videocut_agent 视频剪辑助手
                        例如：帮我剪辑一下videos\打开窗_186714.mp4视频，截取10秒到20秒的内容
                        
                        5.audiocut_agent 音频剪辑助手
                        例如：帮我剪辑一下音频，截取10秒到20秒的内容
                        
                        6.subtitle_editor_agent 字幕助手
                        例如：帮我把videos\打开窗_186714.mp4这个视频转成转换成字幕文件
                        
                        7.videoscript_agent 视频文案助手
                        例如：帮我创作一个以早期为主题的15秒左右的文案
                        """,
            # middleware=[trim_messages],
            # checkpointer=InMemorySaver(),
                                )
    
    def run(self, query: str):
        """运行 Agent"""
        config: RunnableConfig = {"configurable": {"thread_id": "1"}}
        response = self.main_agent.invoke({
            "messages": [("user", query)]
        },config=config)
        if "output" in response:
            
            return response["output"]
        elif "messages" in response:
            return response["messages"][-1].content
        return str(response)
    

    def stream_run(self, query: str):
        """流式运行 Agent"""
        # config: RunnableConfig = {"configurable": {"thread_id": "1"}}
        response = self.main_agent.stream({"messages": [("user", query)]},stream_mode="updates")
        for chunk in response:
            yield chunk
    
# === 运行示例 ===
if __name__ == "__main__":    
    agent = MainAgent()
    
    print("🚀 Agent 启动 (LangChain 1.2)...")
    query = """帮我仿照这个爆款视频"https://www.youtube.com/shorts/D096pdUIzYw?t=4&feature=share"仿写一个以如何广州游玩为主题的视频，视频时长20秒左右"""
    # result = agent.run("帮我生成一个如何学习的15-20秒以内的文案")
    # 流式输出
    # for chunk in agent.stream_run("帮我创作一个如何学习的15-20秒以内的文案"):
    for chunk in agent.stream_run(query):
        for step, data in chunk.items():
            print(f"step: {step}")
            print(f"content: {data['messages'][-1].content_blocks}")
    # print("\n✅ 最终结果:")
    # print(result) 
        