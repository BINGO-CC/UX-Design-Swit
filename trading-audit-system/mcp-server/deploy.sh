#!/bin/bash
# ============================================================
# A股数据 MCP Server · 一键部署脚本
# 在腾讯云轻量服务器（Docker CE 镜像）上执行
# ============================================================

set -e

echo "=========================================="
echo "  A股数据 MCP Server · 一键部署"
echo "=========================================="

# 1. 创建项目目录
echo "[1/6] 创建项目目录..."
mkdir -p /opt/stock-mcp-server
cd /opt/stock-mcp-server

# 2. 确认 Docker 已安装
echo "[2/6] 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker 未安装，开始安装..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi
docker --version
docker compose version || docker-compose --version

# 3. 拉取代码（用户需将代码上传到此目录）
echo "[3/6] 请确认代码已上传到 /opt/stock-mcp-server/"
echo "       需要的文件: server.py, Dockerfile, docker-compose.yml, requirements.txt, tools/, datasource/, config/"

if [ ! -f "server.py" ]; then
    echo "❌ 未找到 server.py，请先上传代码！"
    echo "   方法1: scp -r ./stock-mcp-server/* root@YOUR_IP:/opt/stock-mcp-server/"
    echo "   方法2: git clone YOUR_REPO /opt/stock-mcp-server"
    exit 1
fi

# 4. 创建 .env 文件
echo "[4/6] 配置环境变量..."
if [ ! -f ".env" ]; then
    # 生成随机 Token
    TOKEN=$(openssl rand -hex 32)
    cat > .env << EOF
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_AUTH_TOKEN=${TOKEN}
CACHE_TTL_REALTIME=5
CACHE_TTL_TECHNICAL=60
CACHE_TTL_FUNDAMENTAL=14400
CACHE_TTL_EVENT=3600
AKSHARE_RATE_LIMIT=0.5
EOF
    echo "✅ .env 已生成，Token: ${TOKEN}"
    echo "⚠️  请妥善保存此 Token，MCP Client 连接时需要！"
else
    echo "✅ .env 已存在，跳过"
fi

# 5. 构建并启动
echo "[5/6] 构建 Docker 镜像并启动..."
docker compose up -d --build

# 6. 验证
echo "[6/6] 验证服务状态..."
sleep 3
if docker compose ps | grep -q "running"; then
    echo ""
    echo "=========================================="
    echo "  ✅ 部署成功！"
    echo "=========================================="
    echo ""
    echo "  服务地址: http://$(curl -s ifconfig.me):8000/sse"
    echo "  Token: $(grep MCP_AUTH_TOKEN .env | cut -d= -f2)"
    echo ""
    echo "  下一步:"
    echo "  1. 在安全组/防火墙确认端口 8000 已放行"
    echo "  2. 在 AI 平台配置 MCP Server 连接:"
    echo ""
    echo '  {' 
    echo '    "mcpServers": {'
    echo '      "stock-data": {'
    echo '        "type": "sse",'
    echo "        \"url\": \"http://$(curl -s ifconfig.me):8000/sse\""
    echo '      }'
    echo '    }'
    echo '  }'
    echo ""
    echo "=========================================="
else
    echo "❌ 启动失败，请检查日志: docker compose logs"
fi
