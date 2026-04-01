#!/bin/bash

# AgentNex Platform Docker 启动脚本
# 适用于 macOS (Darwin)

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否运行
check_docker() {
    print_info "检查 Docker 环境..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker Desktop"
        exit 1
    fi
    print_success "Docker 环境正常"
}

# 检查 .env 文件
check_env() {
    print_info "检查环境配置文件..."
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            print_warning ".env 文件不存在，从 .env.example 创建..."
            cp .env.example .env
            print_warning "请编辑 .env 文件，填入 DASHSCOPE_API_KEY 等配置"
            print_info "编辑命令: vim .env 或 nano .env"
            read -p "是否现在编辑配置文件? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ${EDITOR:-vim} .env
            fi
        else
            print_error ".env.example 文件不存在，无法创建配置"
            exit 1
        fi
    fi
    print_success "环境配置文件已就绪"
}

# 检查 DASHSCOPE_API_KEY
check_api_key() {
    print_info "检查 API Key 配置..."
    if grep -q "your-dashscope-api-key-here" .env 2>/dev/null; then
        print_warning "DASHSCOPE_API_KEY 未配置，请先在 .env 文件中填入有效的 API Key"
        print_info "获取 API Key: https://dashscope.console.aliyun.com/"
        read -p "是否继续启动? (部分功能可能不可用) (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    print_success "API Key 配置检查完成"
}

# 停止服务
stop_services() {
    print_info "停止所有服务..."
    docker-compose down
    print_success "服务已停止"
}

# 清理服务
clean_services() {
    print_info "清理所有服务和数据..."
    docker-compose down -v
    print_success "服务和数据已清理"
}

# 启动服务
start_services() {
    print_info "启动 AgentNex 平台..."
    docker-compose up -d

    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    print_info "检查服务状态..."
    docker-compose ps

    # 显示访问信息
    show_access_info
}

# 重启服务
restart_services() {
    print_info "重启服务..."
    docker-compose restart
    sleep 5
    show_access_info
}

# 查看日志
view_logs() {
    if [ -z "$1" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$1"
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    print_success "=========================================="
    print_success "  AgentNex Platform 已启动成功！"
    print_success "=========================================="
    echo ""
    echo -e "${GREEN}前端访问地址:${NC}  http://localhost:3000"
    echo -e "${GREEN}后端 API 地址:${NC}  http://localhost:8000"
    echo -e "${GREEN}API 文档地址:${NC}  http://localhost:8000/docs"
    echo -e "${GREEN}数据库地址:${NC}    localhost:5432"
    echo ""
    echo -e "${BLUE}默认管理员账号:${NC} admin@agentnex.io"
    echo -e "${BLUE}默认管理员密码:${NC} AgentNex@2026"
    echo ""
    echo -e "${YELLOW}常用命令:${NC}"
    echo "  查看日志: $0 logs"
    echo "  停止服务: $0 stop"
    echo "  重启服务: $0 restart"
    echo "  清理数据: $0 clean"
    echo ""
}

# 显示帮助
show_help() {
    echo "AgentNex Platform Docker 管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动所有服务 (默认)"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  clean     停止并清理所有服务（包括数据卷）"
    echo "  logs      查看所有服务日志"
    echo "  logs [服务名]  查看指定服务日志 (backend/frontend/postgres)"
    echo "  status    查看服务状态"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0           # 启动服务"
    echo "  $0 logs      # 查看所有日志"
    echo "  $0 logs backend  # 查看后端日志"
    echo ""
}

# 查看状态
show_status() {
    print_info "服务状态:"
    docker-compose ps
    echo ""
    print_info "端口占用:"
    lsof -i :3000 -i :8000 -i :5432 2>/dev/null | grep LISTEN || echo "无端口占用信息"
}

# 主逻辑
main() {
    case "${1:-start}" in
        start)
            check_docker
            check_env
            check_api_key
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        clean)
            clean_services
            ;;
        logs)
            view_logs "$2"
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
