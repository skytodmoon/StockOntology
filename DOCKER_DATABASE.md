# StockOntology 本地数据库服务

## 概述

本项目使用 Docker Compose 启动和管理所有本地数据库服务，包括：
- **Neo4j** - 图数据库
- **PostgreSQL** - 关系数据库
- **TimescaleDB** - 时序数据库（基于 PostgreSQL）
- **Redis** - 缓存数据库

## 快速开始

### 1. 启动所有服务

```bash
# 使用 docker-compose 直接启动
docker-compose up -d

# 或使用管理脚本
./manage_db.sh start

# 或使用快速启动脚本（会启动所有服务）
./quick_start.sh
```

### 2. 检查服务状态

```bash
# 查看运行状态
docker ps

# 或使用管理脚本
./manage_db.sh status
```

### 3. 测试连接

```bash
./manage_db.sh test
```

### 4. 停止所有服务

```bash
# 使用 docker-compose 停止
docker-compose down

# 或使用管理脚本
./manage_db.sh stop
```

## 访问地址

| 服务 | 地址 | 默认用户 | 默认密码 |
|------|------|---------|---------|
| Neo4j HTTP | http://localhost:7474 | neo4j | password |
| Neo4j Bolt | bolt://localhost:7687 | neo4j | password |
| PostgreSQL | localhost:5432 | postgres | password |
| TimescaleDB | localhost:5433 | postgres | password |
| Redis | localhost:6379 | - | - |

## 配置说明

### Docker Compose 配置

```yaml
# 文件位置: docker-compose.yml

services:
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt

  postgres:
    image: postgres:latest
    ports:
      - "5432:5432"

  timescale:
    image: timescale/timescaledb:latest-pg18
    ports:
      - "5433:5432"

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
```

### 应用配置

配置文件位置: `.env`

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# TimescaleDB
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5433
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 数据持久化

所有数据库数据都存储在 `docker/` 目录下：

```
docker/
├── neo4j/
│   ├── data/      # Neo4j 数据
│   ├── logs/      # Neo4j 日志
│   └── plugins/   # Neo4j 插件
├── postgres/      # PostgreSQL 数据
├── timescale/     # TimescaleDB 数据
└── redis/
    └── data/      # Redis 数据
```

## 管理脚本

`manage_db.sh` 提供便捷的管理命令：

```bash
# 查看状态
./manage_db.sh status

# 启动服务
./manage_db.sh start

# 停止服务
./manage_db.sh stop

# 重启服务
./manage_db.sh restart

# 测试连接
./manage_db.sh test
```

## 初始化数据库

后端启动时会自动初始化 Neo4j 数据库，包括创建约束和索引。

### 手动初始化

```bash
# 清理数据库
source venv/bin/activate
python clear_db.py

# 初始化数据
python init_db_standalone.py
```

## 常见问题

### 1. PostgreSQL/TimescaleDB 启动失败

检查日志：
```bash
docker logs stock_ontology_postgres
docker logs stock_ontology_timescale
```

常见原因：
- 数据目录不兼容（PostgreSQL 18+ 需要新的目录结构）
- 端口冲突

解决方法：
```bash
docker-compose down
rm -rf docker/postgres docker/timescale
mkdir docker/postgres docker/timescale
docker-compose up -d
```

### 2. 连接被拒绝

检查服务状态：
```bash
docker ps
```

检查端口：
```bash
lsof -i :5432  # PostgreSQL
lsof -i :5433  # TimescaleDB
lsof -i :6379  # Redis
lsof -i :7687  # Neo4j
```

### 3. 内存不足

Docker 默认内存限制可能导致服务启动失败。调整 Docker 设置或在 `docker-compose.yml` 中限制内存使用。

## 生产环境建议

- 使用 Docker Compose 的 `--scale` 参数实现高可用
- 配置数据备份策略
- 使用 Docker 网络实现服务隔离
- 定期更新镜像版本
- 监控容器健康状态

## 更多信息

- [Neo4j 文档](https://neo4j.com/docs/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [TimescaleDB 文档](https://docs.timescale.com/)
- [Redis 文档](https://redis.io/documentation)
