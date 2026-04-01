#!/bin/bash

# AgentNex Platform 快速启动脚本 (macOS)

echo "🚀 启动 AgentNex 平台..."

# 检查并启动 Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，正在启动 Docker Desktop..."
    open -a Docker
    echo "⏳ 等待 Docker 启动 (约 10 秒)..."
    sleep 10
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚙️  创建 .env 配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，填入 DASHSCOPE_API_KEY"
fi

# 启动服务
echo "🐳 使用 Docker Compose 启动服务..."
docker-compose up -d

# 等待服务就绪
echo "⏳ 等待服务启动..."
sleep 15

# 显示服务状态
echo ""
echo "✅ 服务状态:"
docker-compose ps

echo ""
echo "=========================================="
echo "✅ AgentNex Platform 已启动成功！"
echo "=========================================="
echo ""
echo "🌐 前端地址:  http://localhost:3000"
echo "🔧 后端 API:  http://localhost:8000"
echo "📚 API 文档:  http://localhost:8000/docs"
echo "🗄️  数据库:    localhost:5432"
echo ""
echo "👤 管理员账号: admin@agentnex.io"
echo "🔑 管理员密码: AgentNex@2026"
echo ""
echo "📝 常用命令:"
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""
