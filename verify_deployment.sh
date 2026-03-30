#!/bin/bash
# AgentNex Platform 部署验证脚本

set -e

echo "=========================================="
echo "AgentNex Platform 部署验证"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker
echo -e "\n${GREEN}[1/8] 检查 Docker 环境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 已安装${NC}"

# 检查 Docker Compose
echo -e "\n${GREEN}[2/8] 检查 Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose 已安装${NC}"

# 检查环境变量文件
echo -e "\n${GREEN}[3/8] 检查环境变量配置...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 文件不存在，正在从模板创建...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ 已创建 .env 文件，请编辑填入实际配置${NC}"
    exit 1
fi
echo -e "${GREEN}✅ .env 文件存在${NC}"

# 检查必填环境变量
echo -e "\n${GREEN}[4/8] 检查必填环境变量...${NC}"
source .env

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo -e "${RED}❌ DASHSCOPE_API_KEY 未配置${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 必填环境变量已配置${NC}"

# 启动服务
echo -e "\n${GREEN}[5/8] 启动 Docker 服务...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "\n${GREEN}[6/8] 等待服务启动（30秒）...${NC}"
sleep 30

# 检查容器状态
echo -e "\n${GREEN}[7/8] 检查容器状态...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ 所有容器正常运行${NC}"
else
    echo -e "${RED}❌ 容器启动失败${NC}"
    docker-compose logs
    exit 1
fi

# 健康检查
echo -e "\n${GREEN}[8/8] 执行健康检查...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/)

if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✅ API 服务正常${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ API 服务异常${NC}"
    echo "$HEALTH_RESPONSE"
    docker-compose logs backend
    exit 1
fi

echo -e "\n${GREEN}=========================================="
echo "✅ 部署验证通过！"
echo "==========================================${NC}"
echo -e "\n访问地址："
echo "  前端界面: http://localhost:3000"
echo "  API 文档: http://localhost:8000/docs"
echo "  默认账号: admin@agentnex.io"
echo "  默认密码: AgentNex@2026"
echo -e "\n${RED}⚠️  重要：首次登录后请立即修改密码！${NC}"
