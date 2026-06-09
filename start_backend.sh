#!/bin/bash

# 后端服务启动脚本

cd /Users/sunqi/Documents/trae_projects/StockOntology

# 加载环境变量
set -a
source .env
set +a

# 激活虚拟环境并启动后端
source venv/bin/activate
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
