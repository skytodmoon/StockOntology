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
REMOTE_HOST="localhost"

echo -e "${BLUE}=== 检查环境 ===${NC}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 已安装${NC}"

# 检查 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose 已安装${NC}"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}✗ 未找到 .env 文件${NC}"
    exit 1
fi
echo -e "${GREEN}✓ .env 文件存在${NC}"

# 启动 Docker 数据库服务
echo -e "${BLUE}=== 启动 Docker 数据库服务 ===${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Docker 服务已启动${NC}"

# 等待数据库服务就绪
echo -e "${YELLOW}等待数据库服务就绪...${NC}"
sleep 20

echo ""
echo -e "${BLUE}=== 检查 Docker 服务 ===${NC}"
docker ps

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

# 启动 Celery Worker
echo -e "${YELLOW}启动 Celery Worker...${NC}"
cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=4 &
CELERY_WORKER_PID=$!
cd ..
echo -e "${GREEN}✓ Celery Worker 已启动 (PID: $CELERY_WORKER_PID)${NC}"

# 启动 Celery Beat
echo -e "${YELLOW}启动 Celery Beat...${NC}"
cd backend
celery -A app.celery_app beat --loglevel=info &
CELERY_BEAT_PID=$!
cd ..
echo -e "${GREEN}✓ Celery Beat 已启动 (PID: $CELERY_BEAT_PID)${NC}"

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
echo -e "  数据管理:    ${GREEN}http://localhost:3000/data${NC}"
echo ""
echo -e "${BLUE}数据库服务:${NC}"
echo -e "  Neo4j:       ${GREEN}bolt://localhost:7687${NC}"
echo -e "  PostgreSQL:  ${GREEN}localhost:5432${NC}"
echo -e "  Redis:       ${GREEN}localhost:6379${NC}"
echo -e "  TimescaleDB: ${GREEN}localhost:5433${NC}"
echo ""
echo -e "${BLUE}定时任务:${NC}"
echo -e "  行情采集:    每日 18:00"
echo -e "  新闻采集:    每小时 9-23 点"
echo -e "  事件推理:    每小时 30 分"
echo -e "  预测扫描:    每日 20:00"
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

    if [ ! -z "$CELERY_WORKER_PID" ]; then
        kill $CELERY_WORKER_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Celery Worker 已停止${NC}"
    fi

    if [ ! -z "$CELERY_BEAT_PID" ]; then
        kill $CELERY_BEAT_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Celery Beat 已停止${NC}"
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