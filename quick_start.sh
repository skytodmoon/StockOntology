#!/bin/bash

# StockOntology 快速启动脚本
# 直接启动本地应用服务，假设远程数据库服务已运行

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}StockOntology - 股票分析预测系统${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 远程服务器配置
REMOTE_HOST="172.16.252.109"

echo -e "${BLUE}=== 检查环境 ===${NC}"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}✗ 未找到 .env 文件${NC}"
    exit 1
fi
echo -e "${GREEN}✓ .env 文件存在${NC}"

# 检查 Python 环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}创建 Python 虚拟环境...${NC}"
    python3 -m venv venv
fi
echo -e "${GREEN}✓ Python 虚拟环境存在${NC}"

# 检查后端依赖
echo -e "${YELLOW}检查后端依赖...${NC}"
source venv/bin/activate
pip install -q -r backend/requirements.txt 2>/dev/null || pip install -q -r requirements.txt 2>/dev/null || echo -e "${YELLOW}跳过依赖安装${NC}"

# 检查前端依赖
if [ -d "frontend" ]; then
    echo -e "${YELLOW}检查前端依赖...${NC}"
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    cd ..
fi

echo ""
echo -e "${BLUE}=== 启动服务 ===${NC}"

# 启动后端服务
echo -e "${YELLOW}启动后端服务...${NC}"
source venv/bin/activate
# 加载环境变量
set -a
source .env
set +a
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"

# 启动前端服务
if [ -d "frontend" ]; then
    echo -e "${YELLOW}启动前端服务...${NC}"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}服务启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "  前端:        ${GREEN}http://localhost:3000${NC}"
echo -e "  后端 API:    ${GREEN}http://localhost:8000${NC}"
echo -e "  API 文档:    ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}远程服务 ($REMOTE_HOST):${NC}"
echo -e "  Neo4j:       ${GREEN}bolt://$REMOTE_HOST:7687${NC}"
echo -e "  PostgreSQL:  ${GREEN}$REMOTE_HOST:5432${NC}"
echo -e "  Redis:       ${GREEN}$REMOTE_HOST:6379${NC}"
echo -e "  TimescaleDB: ${GREEN}$REMOTE_HOST:5433${NC}"
echo ""
echo -e "${BLUE}LLM 服务:${NC}"
echo -e "  小米 MiMo:   ${GREEN}https://token-plan-cn.xiaomimimo.com/v1${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

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

# 设置清理
trap cleanup INT TERM

# 等待
wait