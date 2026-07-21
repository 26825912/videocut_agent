"""前端配置：从 .env 读取 agent 后端地址。"""
import os
from dotenv import load_dotenv

load_dotenv()

AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000").rstrip("/")
DATA_BASE_URL = os.getenv("DATA_BASE_URL", AGENT_API_URL).rstrip("/")
