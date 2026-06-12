#!/bin/bash
# 数据库服务管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

show_status() {
    echo -e "${BLUE}=== 数据库服务状态 ===${NC}"
    docker ps --filter "name=stock_ontology" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

start_services() {
    echo -e "${BLUE}=== 启动数据库服务 ===${NC}"
    docker-compose up -d
    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 20
    show_status
}

stop_services() {
    echo -e "${BLUE}=== 停止数据库服务 ===${NC}"
    docker-compose down
    echo -e "${GREEN}✓ 所有服务已停止${NC}"
}

restart_services() {
    echo -e "${BLUE}=== 重启数据库服务 ===${NC}"
    stop_services
    sleep 2
    start_services
}

test_connections() {
    echo -e "${BLUE}=== 测试数据库连接 ===${NC}"
    
    # 测试 Neo4j
    echo -ne "Neo4j: "
    if curl -s http://localhost:7474 &>/dev/null; then
        echo -e "${GREEN}✓ 连接成功${NC}"
    else
        echo -e "${RED}✗ 连接失败${NC}"
    fi
    
    # 测试 PostgreSQL
    echo -ne "PostgreSQL: "
    if docker exec stock_ontology_postgres pg_isready -U postgres &>/dev/null; then
        echo -e "${GREEN}✓ 连接成功${NC}"
    else
        echo -e "${RED}✗ 连接失败${NC}"
    fi
    
    # 测试 TimescaleDB
    echo -ne "TimescaleDB: "
    if docker exec stock_ontology_timescale pg_isready -U postgres &>/dev/null; then
        echo -e "${GREEN}✓ 连接成功${NC}"
    else
        echo -e "${RED}✗ 连接失败${NC}"
    fi
    
    # 测试 Redis
    echo -ne "Redis: "
    if docker exec stock_ontology_redis redis-cli ping &>/dev/null; then
        echo -e "${GREEN}✓ 连接成功${NC}"
    else
        echo -e "${RED}✗ 连接失败${NC}"
    fi
}

case "${1:-status}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    test)
        test_connections
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|test}"
        exit 1
        ;;
esac
