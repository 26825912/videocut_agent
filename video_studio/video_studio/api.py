"""Agent 后端 API 客户端（运行在 Reflex 后端，服务器到服务器，无需 CORS）。

对接 videocut_agent/server.py 的：
  GET  /health
  GET  /agents/list
  POST /query  (stream=true 返回 SSE；stream=false 返回 JSON)
"""
import json
from typing import AsyncIterator

import httpx

from .config import AGENT_API_URL


async def health() -> bool:
    """检查 agent 服务是否在线。"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{AGENT_API_URL}/health")
            return r.status_code == 200
    except Exception:
        return False


async def list_agents() -> list:
    """获取可用智能体列表。"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{AGENT_API_URL}/agents/list")
            if r.status_code == 200:
                return r.json().get("agents", [])
    except Exception:
        pass
    return []


async def stream_query(query: str) -> AsyncIterator[dict]:
    """流式查询 agent，逐个 yield SSE 事件字典。

    server.py 的 SSE 行格式为 `data: <json>\\n\\n`，
    事件 type 取值：start / done / error / text / tool_call，
    以及 tools step 产生的 {type:'text', text:'<字符串化的dict>'}。
    """
    payload = {"query": query, "stream": True}
    # 流式请求不设总超时（视频生成可能很久），单读超时由默认值控制
    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as client:
        async with client.stream("POST", f"{AGENT_API_URL}/query", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[len("data: "):]
                try:
                    yield json.loads(data_str)
                except json.JSONDecodeError:
                    continue


async def query(query: str) -> str:
    """非流式查询，返回最终结果文本。"""
    payload = {"query": query, "stream": False}
    async with httpx.AsyncClient(timeout=300.0) as client:
        r = await client.post(f"{AGENT_API_URL}/query", json=payload)
        r.raise_for_status()
        data = r.json()
        if data.get("success"):
            return data.get("result", "") or ""
        raise RuntimeError(data.get("error") or "未知错误")
