#!/bin/bash

# StockOntology 完整启动脚本
# 支持远程数据库服务和本地应用服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 远程服务器配置
REMOTE_HOST="172.16.252.109"
REMOTE_USER="root"
REMOTE_SSH_KEY="$HOME/.ssh/id_rsa"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}StockOntology - 股票分析预测系统${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ 未找到 $1${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 已安装${NC}"
        return 0
    fi
}

# 检查远程服务是否运行
check_remote_service() {
    local name=$1
    local port=$2
    
    if timeout 3 nc -z "$REMOTE_HOST" "$port" 2>/dev/null; then
        echo -e "${GREEN}✓ $name 正在运行 ($REMOTE_HOST:$port)${NC}"
        return 0
    else
        echo -e "${RED}✗ $name 未运行 ($REMOTE_HOST:$port)${NC}"
        return 1
    fi
}

# 检查本地服务是否运行
check_local_service() {
    local name=$1
    local port=$2
    local host=${3:-localhost}
    
    if nc -z "$host" "$port" 2>/dev/null; then
        echo -e "${GREEN}✓ $name 正在运行 ($host:$port)${NC}"
        return 0
    else
        echo -e "${RED}✗ $name 未运行 ($host:$port)${NC}"
        return 1
    fi
}

# 显示服务状态
show_service_status() {
    echo ""
    echo -e "${BLUE}=== 服务状态检查 ===${NC}"
    echo -e "${BLUE}远程服务 ($REMOTE_HOST):${NC}"
    
    check_remote_service "Neo4j" "7687"
    check_remote_service "Redis" "6379"
    check_remote_service "PostgreSQL" "5432"
    check_remote_service "TimescaleDB" "5433"
    
    echo ""
    echo -e "${BLUE}本地服务:${NC}"
    check_local_service "后端 API" "8000"
    check_local_service "前端服务" "3000" || check_local_service "前端服务" "5173"
    
    echo ""
}

# 检查远程服务状态
check_remote_services() {
    echo -e "${BLUE}=== 检查远程数据库服务 ===${NC}"
    
    local all_running=true
    
    check_remote_service "Neo4j" "7687" || all_running=false
    check_remote_service "Redis" "6379" || all_running=false
    check_remote_service "PostgreSQL" "5432" || all_running=false
    check_remote_service "TimescaleDB" "5433" || all_running=false
    
    if [ "$all_running" = true ]; then
        echo -e "${GREEN}✓ 所有远程数据库服务正常运行${NC}"
        return 0
    else
        echo -e "${RED}✗ 部分远程服务未运行${NC}"
        echo -e "${YELLOW}请检查远程服务器: $REMOTE_HOST${NC}"
        return 1
    fi
}

# 启动远程数据库服务
start_remote_services() {
    echo -e "${BLUE}=== 启动远程数据库服务 ===${NC}"
    
    # 检查SSH连接
    if ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 $REMOTE_USER@$REMOTE_HOST "echo 'SSH连接成功'" 2>/dev/null; then
        echo -e "${RED}✗ 无法连接到远程服务器 $REMOTE_HOST${NC}"
        echo -e "${YELLOW}请检查:${NC}"
        echo -e "  1. 网络连接"
        echo -e "  2. SSH密钥配置"
        echo -e "  3. 服务器状态"
        return 1
    fi
    
    echo -e "${GREEN}✓ SSH连接成功${NC}"
    
    # 上传配置文件
    echo "上传 docker-compose 配置..."
    scp -o StrictHostKeyChecking=no docker-compose.db.yml $REMOTE_USER@$REMOTE_HOST:/root/StockOntology/ 2>/dev/null || true
    
    # 启动服务
    echo "启动远程数据库服务..."
    ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "cd /root/StockOntology && docker-compose -f docker-compose.db.yml up -d"
    
    # 等待服务启动
    echo "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_remote_services
}

# 检查环境变量
check_env_file() {
    echo -e "${BLUE}=== 环境变量检查 ===${NC}"
    
    if [ ! -f .env ]; then
        echo -e "${YELLOW}未找到 .env 文件，从 .env.example 创建...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}请编辑 .env 文件配置必要的环境变量${NC}"
        echo -e "${YELLOW}特别是:${NC}"
        echo -e "${YELLOW}  - NEO4J_PASSWORD (远程服务器密码: 12345678)${NC}"
        echo -e "${YELLOW}  - POSTGRES_PASSWORD (远程服务器密码: stock_ontology_2024)${NC}"
        echo -e "${YELLOW}  - LLM_PROVIDER (当前配置: xiaomi)${NC}"
        echo -e "${YELLOW}  - XIAOMI_API_KEY${NC}"
        echo -e "${YELLOW}  - TUSHARE_TOKEN (如需使用 Tushare 数据源)${NC}"
        return 1
    else
        echo -e "${GREEN}✓ .env 文件存在${NC}"
        
        # 检查关键配置
        if grep -q "NEO4J_URI=bolt://172.16.252.109" .env; then
            echo -e "${GREEN}✓ 已配置远程数据库服务${NC}"
        else
            echo -e "${YELLOW}⚠ 未配置远程数据库服务${NC}"
        fi
        
        if grep -q "LLM_PROVIDER=xiaomi" .env; then
            echo -e "${GREEN}✓ 已配置小米 LLM 服务${NC}"
        fi
        
        return 0
    fi
    echo ""
}

# 安装 Python 依赖
install_python_deps() {
    echo -e "${BLUE}=== 安装 Python 依赖 ===${NC}"
    
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    echo "激活虚拟环境..."
    source venv/bin/activate
    
    echo "安装依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    elif [ -f "backend/requirements.txt" ]; then
        pip install -r backend/requirements.txt
    else
        echo -e "${YELLOW}未找到 requirements.txt，跳过依赖安装${NC}"
    fi
    echo ""
}

# 安装 Node.js 依赖
install_node_deps() {
    echo -e "${BLUE}=== 安装 Node.js 依赖 ===${NC}"
    
    if [ -d "frontend" ]; then
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "安装前端依赖..."
            npm install
        else
            echo -e "${GREEN}✓ 前端依赖已安装${NC}"
        fi
        cd ..
    else
        echo -e "${YELLOW}前端目录不存在，跳过前端依赖安装${NC}"
    fi
    echo ""
}

# 启动后端服务
start_backend() {
    echo -e "${BLUE}=== 启动后端服务 ===${NC}"
    
    if check_local_service "后端 API" "8000"; then
        echo -e "${GREEN}后端服务已运行，跳过启动${NC}"
        return 0
    fi
    
    source venv/bin/activate
    
    if [ -d "backend" ]; then
        cd backend
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        cd ..
    else
        echo -e "${YELLOW}backend 目录不存在，尝试从项目根目录启动...${NC}"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
    fi
    
    echo -e "${GREEN}后端服务已启动 (PID: $BACKEND_PID)${NC}"
    echo ""
}

# 启动前端服务
start_frontend() {
    echo -e "${BLUE}=== 启动前端服务 ===${NC}"
    
    if check_local_service "前端服务" "3000" || check_local_service "前端服务" "5173"; then
        echo -e "${GREEN}前端服务已运行，跳过启动${NC}"
        return 0
    fi
    
    if [ -d "frontend" ]; then
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        
        echo -e "${GREEN}前端服务已启动 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}前端目录不存在，跳过前端启动${NC}"
    fi
    echo ""
}

# 显示访问信息
show_access_info() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}服务启动完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}本地服务:${NC}"
    echo -e "  前端:        ${GREEN}http://localhost:3000${NC}"
    echo -e "  后端 API:    ${GREEN}http://localhost:8000${NC}"
    echo -e "  API 文档:    ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${BLUE}远程服务 ($REMOTE_HOST):${NC}"
    echo -e "  Neo4j Web:   ${GREEN}http://$REMOTE_HOST:7474${NC}"
    echo -e "  Neo4j Bolt:  ${GREEN}bolt://$REMOTE_HOST:7687${NC}"
    echo -e "  PostgreSQL:  ${GREEN}$REMOTE_HOST:5432${NC}"
    echo -e "  TimescaleDB: ${GREEN}$REMOTE_HOST:5433${NC}"
    echo -e "  Redis:       ${GREEN}$REMOTE_HOST:6379${NC}"
    echo ""
    echo -e "${BLUE}LLM 服务:${NC}"
    echo -e "  小米 MiMo:   ${GREEN}https://token-plan-cn.xiaomimimo.com/v1${NC}"
    echo ""
    echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
    echo ""
}

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    fi
    
    echo -e "${GREEN}所有服务已停止${NC}"
    exit 0
}

# 一键启动
one_click_start() {
    echo -e "${BLUE}开始一键启动...${NC}"
    echo ""
    
    # 检查环境变量
    if ! check_env_file; then
        echo -e "${RED}请先配置 .env 文件${NC}"
        exit 1
    fi
    
    # 检查远程服务
    if ! check_remote_services; then
        echo -e "${YELLOW}尝试启动远程服务...${NC}"
        if ! start_remote_services; then
            echo -e "${RED}远程服务启动失败，请手动检查${NC}"
            exit 1
        fi
    fi
    
    # 安装依赖
    install_python_deps
    install_node_deps
    
    # 启动应用服务
    start_backend
    start_frontend
    
    # 设置清理
    trap cleanup INT TERM
    
    # 显示访问信息
    show_access_info
    
    # 等待
    wait
}

# 主函数
main() {
    # 检查基础工具
    echo -e "${BLUE}=== 基础工具检查 ===${NC}"
    check_command python3 || exit 1
    check_command node || exit 1
    check_command npm || exit 1
    check_command ssh || {
        echo -e "${YELLOW}警告: 未找到 ssh，无法连接远程服务器${NC}"
    }
    check_command nc || {
        echo -e "${YELLOW}警告: 未找到 nc (netcat)，服务检查可能不准确${NC}"
    }
    echo ""
    
    # 显示启动选项
    echo -e "${BLUE}=== 选择启动模式 ===${NC}"
    echo "1. 一键启动 (推荐) - 自动检查并启动所有服务"
    echo "2. 仅启动远程数据库服务"
    echo "3. 仅启动本地应用服务"
    echo "4. 检查服务状态"
    echo "5. 安装依赖"
    echo ""
    read -p "请选择 [1-5] (默认: 1): " choice
    
    # 默认选择1
    choice=${choice:-1}
    
    case $choice in
        1)
            one_click_start
            ;;
        2)
            echo ""
            echo -e "${BLUE}启动远程数据库服务...${NC}"
            echo ""
            start_remote_services
            show_service_status
            ;;
        3)
            echo ""
            echo -e "${BLUE}启动本地应用服务...${NC}"
            echo ""
            
            if ! check_env_file; then
                echo -e "${RED}请先配置 .env 文件${NC}"
                exit 1
            fi
            
            check_remote_services
            install_python_deps
            install_node_deps
            
            start_backend
            start_frontend
            
            trap cleanup INT TERM
            show_access_info
            wait
            ;;
        4)
            show_service_status
            ;;
        5)
            echo ""
            echo -e "${BLUE}安装依赖...${NC}"
            echo ""
            install_python_deps
            install_node_deps
            echo -e "${GREEN}依赖安装完成${NC}"
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            exit 1
            ;;
    esac
}

# 运行主函数
main