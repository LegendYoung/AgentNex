#!/bin/bash

# AgentNex Platform 本地启动脚本 (使用 Python 3.11 虚拟环境)

echo "🚀 启动 AgentNex 平台 (Python 3.11 + 虚拟环境)..."

# 设置 Python 3.11 路径
PYTHON311="$HOME/.pyenv/versions/3.11.11/bin/python3.11"
VENV_DIR="$HOME/.pyenv/versions/3.11.11"

# 检查 Python 3.11
if [ ! -f "$PYTHON311" ]; then
    echo "❌ Python 3.11 未找到: $PYTHON311"
    exit 1
fi

echo "📋 Python 版本:"
$PYTHON311 --version
node --version || { echo "❌ Node.js 未安装"; exit 1; }

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENT_DIR="$SCRIPT_DIR/agent"
WEB_DIR="$SCRIPT_DIR/apps/web"

# ==================== 后端服务 ====================
echo ""
echo "🔧 设置后端服务..."
cd "$AGENT_DIR"

# 创建虚拟环境
if [ ! -d "venv311" ]; then
    echo "📦 创建 Python 3.11 虚拟环境..."
    $PYTHON311 -m venv venv311 --clear
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv311/bin/activate

# 验证 Python 版本
PYTHON_IN_VENV=$(python --version)
echo "虚拟环境中的 Python: $PYTHON_IN_VENV"

# 升级 pip
echo "📦 升级 pip..."
pip install --upgrade pip -q

# 检查并安装依赖
echo "📦 检查后端依赖..."
if ! pip show fastapi > /dev/null 2>&1; then
    echo "📥 安装后端依赖 (这可能需要几分钟)..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，尝试安装核心依赖..."
        pip install fastapi uvicorn python-dotenv pydantic pydantic-settings
    fi
else
    echo "✅ 依赖已安装"
fi

# 显示已安装的核心包
echo ""
echo "📋 已安装的核心包:"
pip list | grep -E "fastapi|uvicorn|pydantic|python-dotenv|agno" || echo "正在检查..."

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚙️  创建 .env 配置文件..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        cat > .env << 'EOF'
# AgentNex Platform 环境变量配置
POSTGRES_USER=agentnex
POSTGRES_PASSWORD=agentnex123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentnex
JWT_SECRET_KEY=change-this-secret-key-in-production
SUPER_ADMIN_EMAIL=admin@agentnex.io
SUPER_ADMIN_PASSWORD=AgentNex@2026
DASHSCOPE_API_KEY=placeholder-api-key
VITE_API_URL=http://localhost:8000
MODEL_ID=qwen-plus
MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDER_ID=text-embedding-v3
EMBEDDER_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CHROMA_COLLECTION_NAME=agentnex_knowledge
EOF
    fi
    echo "⚠️  请编辑 .env 文件，填入真实的 DASHSCOPE_API_KEY"
fi

# 启动后端服务
echo ""
echo "🚀 启动后端 API 服务..."
# 检查端口是否被占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 8000 已被占用，正在停止现有服务..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 使用 PYTHONPATH 解决导入问题 (从项目根目录运行)
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 使用 nohup 后台运行 (从项目根目录运行)
cd "$SCRIPT_DIR"
nohup python -m agent.main > /tmp/agentnex_backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"
echo $BACKEND_PID > /tmp/agentnex_backend.pid

# 等待后端启动
echo "⏳ 等待后端服务启动 (最多 30 秒)..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ 后端服务启动成功！"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  后端服务启动超时，显示日志..."
    fi
    sleep 1
done

# 显示后端日志
echo ""
echo "📝 后端服务日志 (最后 10 行):"
tail -10 /tmp/agentnex_backend.log

# ==================== 前端服务 ====================
echo ""
echo "🎨 设置前端服务..."
cd "$WEB_DIR"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📥 安装前端依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 前端依赖安装失败"
        exit 1
    fi
else
    echo "✅ 前端依赖已安装"
fi

# 检查端口是否被占用
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 5173 已被占用，正在停止现有服务..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 启动前端服务
echo "🚀 启动前端开发服务器..."
nohup npm run dev > /tmp/agentnex_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"
echo $FRONTEND_PID > /tmp/agentnex_frontend.pid

# 等待前端启动
echo "⏳ 等待前端服务启动 (最多 20 秒)..."
sleep 8

# 显示前端日志
echo ""
echo "📝 前端服务日志 (最后 10 行):"
tail -10 /tmp/agentnex_frontend.log

# ==================== 显示访问信息 ====================
echo ""
echo "=========================================="
echo "✅ AgentNex Platform 已启动成功！"
echo "=========================================="
echo ""
echo "🐍 Python 版本: 3.11.11 (虚拟环境)"
echo "🌐 前端地址:    http://localhost:5173"
echo "🔧 后端 API:    http://localhost:8000"
echo "📚 API 文档:    http://localhost:8000/docs"
echo ""
echo "📝 实时日志:"
echo "   后端: tail -f /tmp/agentnex_backend.log"
echo "   前端: tail -f /tmp/agentnex_frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   后端: kill $BACKEND_PID 或 kill \$(cat /tmp/agentnex_backend.pid)"
echo "   前端: kill $FRONTEND_PID 或 kill \$(cat /tmp/agentnex_frontend.pid)"
echo ""
echo "🔄 重启服务:"
echo "   后端: cd $AGENT_DIR && source venv311/bin/activate && python main.py &"
echo "   前端: cd $WEB_DIR && npm run dev &"
echo ""
echo "👤 默认管理员账号:"
echo "   邮箱: admin@agentnex.io"
echo "   密码: AgentNex@2026"
echo ""
