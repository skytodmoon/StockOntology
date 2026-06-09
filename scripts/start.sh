#!/bin/bash

# StockOntology 启动脚本

set -e

echo "=========================================="
echo "StockOntology - 股票分析预测系统"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js"
    exit 1
fi

# 检查 Neo4j
if ! command -v neo4j &> /dev/null; then
    echo "警告: 未找到 Neo4j，请确保 Neo4j 已安装并运行"
fi

echo ""
echo "选择启动模式:"
echo "1. 开发模式 (分别启动前后端)"
echo "2. Docker 模式 (使用 docker-compose)"
echo "3. 仅启动后端"
echo "4. 仅启动前端"
echo ""
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "启动开发模式..."

        # 安装后端依赖
        echo "安装后端依赖..."
        pip install -r requirements.txt

        # 安装前端依赖
        echo "安装前端依赖..."
        cd frontend
        npm install
        cd ..

        # 启动后端
        echo "启动后端服务..."
        uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!

        # 启动前端
        echo "启动前端服务..."
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..

        echo ""
        echo "服务已启动:"
        echo "  前端: http://localhost:3000"
        echo "  后端: http://localhost:8000"
        echo "  API 文档: http://localhost:8000/docs"
        echo ""
        echo "按 Ctrl+C 停止服务"

        # 等待中断
        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
        wait
        ;;
    2)
        echo ""
        echo "启动 Docker 模式..."
        docker-compose up -d
        echo ""
        echo "服务已启动:"
        echo "  前端: http://localhost:3000"
        echo "  后端: http://localhost:8000"
        echo "  Neo4j: http://localhost:7474"
        ;;
    3)
        echo ""
        echo "启动后端服务..."
        pip install -r requirements.txt
        uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    4)
        echo ""
        echo "启动前端服务..."
        cd frontend
        npm install
        npm run dev
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
