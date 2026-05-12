"""
A股数据 MCP Server - 配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Server
SERVER_NAME = "stock-data-mcp"
SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("MCP_PORT", "8000"))
AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

# Cache TTL (seconds)
CACHE_TTL_REALTIME = int(os.getenv("CACHE_TTL_REALTIME", "30"))         # 实时行情 30秒（审计场景不需要秒级刷新）
CACHE_TTL_TECHNICAL = int(os.getenv("CACHE_TTL_TECHNICAL", "300"))      # 技术指标 5分钟
CACHE_TTL_FUNDAMENTAL = int(os.getenv("CACHE_TTL_FUNDAMENTAL", "14400"))  # 基本面 4小时
CACHE_TTL_EVENT = int(os.getenv("CACHE_TTL_EVENT", "3600"))             # 事件面 1小时

# 后台预加载
PRELOAD_ENABLED = os.getenv("PRELOAD_ENABLED", "true").lower() == "true"
PRELOAD_INTERVAL = int(os.getenv("PRELOAD_INTERVAL", "25"))             # 预加载间隔(秒)，略小于 realtime TTL

# AKShare 请求限流
AKSHARE_RATE_LIMIT = float(os.getenv("AKSHARE_RATE_LIMIT", "0.3"))     # 请求间隔(秒)
