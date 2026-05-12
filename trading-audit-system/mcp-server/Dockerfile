FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 环境变量
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000

# 启动命令：SSE 远程模式
CMD ["python", "server.py", "--transport", "sse", "--port", "8000"]
