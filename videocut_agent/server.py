import os
import json
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from main_agent2 import MainAgent

# 1. 保持原有导入
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agents_manager import AgentManager

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://api.openai.com/v1")

# --- 数据模型 ---
class QueryRequest(BaseModel):
    """请求数据模型"""
    query: str
    model: Optional[str] = "gemini-2.5-pro"
    stream: Optional[bool] = False  # 新增字段控制是否流式

class AgentResponse(BaseModel):
    """普通非流式响应数据模型"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MainAgent_Executor:
    def __init__(self):
        self.default_model = "gemini-2.5-pro"

        self.agents_manager = AgentManager()
        self.agents = self.agents_manager.agents

        self.main_agent = MainAgent()

    async def run(self, query: str):
        """普通运行模式 (非流式)"""
        try:
            agent = self.main_agent

            response = await asyncio.to_thread(agent.run, query)
            # 处理返回结果
            if isinstance(response, dict):
                if "output" in response:
                    return response["output"]
                elif "messages" in response:
                    return response["messages"][-1].content

            return str(response)

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Agent执行失败: {str(e)}")

    async def stream_run(self, query: str) -> AsyncGenerator[str, None]:
        """
        流式运行模式
        返回 SSE (Server-Sent Events) 格式的数据流
        """
        agent = self.main_agent

        for chunk in agent.stream_run(query):

            for step, data in chunk.items():
                if "messages" not in data or not data['messages']:
                    continue

                last_msg = data['messages'][-1]
                if not hasattr(last_msg, 'content_blocks'):

                    yield self._format_sse({
                        "type": "text",
                        "text": str(last_msg.content),
                        "description": "Processing..."
                    })
                    continue

                deal_data = last_msg.content_blocks
                if step == "model":
                    for subdata in deal_data:
                        return_type = subdata.get('type') # 使用 .get 防止报错
                        if return_type == "tool_call":
                            tool_name = subdata.get('name')
                            yield self._format_sse({
                                "type": return_type,
                                "tools_name": tool_name,
                                "args": subdata.get('args'),
                                "description": f"正在调用工具处理",
                            })
                        elif return_type == "text":
                            yield self._format_sse({
                                "type": return_type,
                                "text": subdata.get('text'),
                                "description": f"agent正在处理"
                            })
                elif step == "tools":
                    for subdata in deal_data:
                        return_type = subdata.get('type', 'text')
                        yield self._format_sse({
                            "type": return_type,
                            "text": subdata.get('text', ''),
                        })

    def _format_sse(self, data: Dict[str, Any]) -> str:
        """格式化为 SSE (Server-Sent Events) 字符串"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# --- FastAPI 应用 ---
app = FastAPI(
    title="视频制作智能体API (Streaming)",
    description="支持流式输出 Agent 思考过程和工具调用的服务",
    version="2.0.0"
)

# 挂载静态文件目录，供前端预览/下载生成的视频、音频、字幕
_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if os.path.isdir(_data_dir):
    app.mount("/data", StaticFiles(directory=_data_dir), name="data")

# 全局Agent实例
main_agent_instance = None

@app.on_event("startup")
async def startup_event():
    global main_agent_instance
    try:
        main_agent_instance = MainAgent_Executor()
        print("🚀 Agent 启动成功 (Async/Streaming Ready)...")
    except Exception as e:
        print(f"❌ Agent 启动失败: {e}")
        raise

@app.get("/health")
async def health_check():
    if main_agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    return {"status": "healthy", "mode": "streaming_enabled"}

@app.post("/query")
async def query_agent(request: QueryRequest):
    """
    统一查询接口
    Args:
        request: 包含 query 和 stream 参数
                如果 stream=True，返回 StreamingResponse
                如果 stream=False，返回 JSON
    """
    if main_agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    # --- 1. 流式响应处理 ---
    if request.stream:
        async def event_generator():
            try:
                # 发送开始信号
                yield f"data: {json.dumps({'type': 'start'})}\n\n"

                # 迭代生成器
                async for chunk in main_agent_instance.stream_run(
                    query=request.query
                ):
                    yield chunk

                # 发送结束信号
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                # 发送错误信号
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    # --- 2. 普通响应处理 (保持兼容) ---
    try:
        result = await main_agent_instance.run(
            query=request.query,
        )

        return AgentResponse(
            success=True,
            result=result,
            metadata={
                "model": request.model,
            }
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            error=str(e),
            metadata={"error_type": type(e).__name__}
        )

@app.get("/agents/list")
async def list_agents():
    if main_agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    agents_list = [
        {"name": agent.name, "description": agent.description}
        for agent in main_agent_instance.agents
    ]
    return {"success": True, "agents": agents_list}

if __name__ == "__main__":
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)