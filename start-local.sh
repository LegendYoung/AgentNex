#!/bin/bash

# AgentNex Platform 本地启动脚本 (不使用 Docker)

echo "🚀 启动 AgentNex 平台 (本地模式)..."

# 检查环境
echo "📋 检查环境..."
python3 --version || { echo "❌ Python 未安装"; exit 1; }
node --version || { echo "❌ Node.js 未安装"; exit 1; }

# 启动后端
echo ""
echo "🔧 启动后端服务..."
cd /Users/legend-macos/Documents/AgentNex/agent

# 安装后端依赖
if [ ! -d "venv" ]; then
    echo "📦 安装后端依赖..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
else
    source venv/bin/activate
fi

# 检查环境变量
if [ ! -f .env ]; then
    echo "⚙️  创建 .env 文件..."
    cp .env.example .env 2>/dev/null || echo "DASHSCOPE_API_KEY=placeholder" > .env
fi

# 启动后端服务 (后台运行)
echo "🚀 启动后端 API 服务..."
nohup python3 main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"
echo $BACKEND_PID > /tmp/agentnex_backend.pid

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 10

# 检查后端是否启动成功
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ 后端服务启动成功"
    tail -20 /tmp/backend.log
else
    echo "❌ 后端服务启动失败，请检查日志:"
    cat /tmp/backend.log
    exit 1
fi

# 启动前端
echo ""
echo "🎨 启动前端服务..."
cd /Users/legend-macos/Documents/AgentNex/apps/web

# 安装前端依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端服务 (后台运行)
echo "🚀 启动前端开发服务器..."
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"
echo $FRONTEND_PID > /tmp/agentnex_frontend.pid

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 10

# 检查前端是否启动成功
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ 前端服务启动成功"
    tail -20 /tmp/frontend.log
else
    echo "❌ 前端服务启动失败，请检查日志:"
    cat /tmp/frontend.log
    exit 1
fi

# 显示访问信息
echo ""
echo "=========================================="
echo "✅ AgentNex Platform 已启动成功！"
echo "=========================================="
echo ""
echo "🌐 前端地址:  http://localhost:5173"
echo "🔧 后端 API:  http://localhost:8000"
echo "📚 API 文档:  http://localhost:8000/docs"
echo ""
echo "📝 后端日志: tail -f /tmp/backend.log"
echo "📝 前端日志: tail -f /tmp/frontend.log"
echo ""
echo "🛑 停止服务: kill $BACKEND_PID $FRONTEND_PID"
echo "           或运行: kill \$(cat /tmp/agentnex_backend.pid) \$(cat /tmp/agentnex_frontend.pid)"
echo ""
