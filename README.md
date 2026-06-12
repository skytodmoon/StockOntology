# StockOntology - 基于本体论的股票分析预测系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-orange.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 项目简介

StockOntology 是一个基于本体论的股票分析预测系统，通过知识图谱、大语言模型和 AI 算法，提供智能化的股票分析和预测能力。系统重点分析半导体、芯片、AI、航天、机器人、算力、消费等领域的龙头股及其供应链。

### 核心特性

- **本体驱动**：基于 OWL 本体建模，系统化表示股票市场知识
- **知识图谱**：使用 Neo4j 构建大规模股票知识图谱
- **龙头战法**：智能识别和分析行业龙头股，评估技术护城河
- **多数据源**：支持通达信、腾讯、东方财富等数据源自动切换
- **智能分析**：集成 LLM 实现智能问答和文本分析
- **AI 预测**：多种机器学习模型进行股价预测
- **可视化展示**：丰富的图表和图谱可视化
- **自动化采集**：定时任务调度，自动采集市场数据

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + ECharts + Element Plus |
| 后端 | Python FastAPI |
| 图数据库 | Neo4j |
| 时序数据库 | TimescaleDB |
| 关系数据库 | PostgreSQL |
| 缓存数据库 | Redis |
| 向量数据库 | ChromaDB |
| LLM | LangChain + OpenAI |
| AI 算法 | PyTorch + Scikit-learn |
| 数据采集 | mootdx + AKShare + 自定义数据源 |
| 本体工具 | OWL API + RDFLib |

## 项目结构

```
StockOntology/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── api/               # API 路由
│   │   │   ├── dragon.py      # 龙头战法 API
│   │   │   ├── scheduler.py   # 任务调度 API
│   │   │   ├── graph.py       # 图谱查询 API
│   │   │   ├── companies.py   # 公司管理 API
│   │   │   ├── events.py      # 事件管理 API
│   │   │   └── ...
│   │   ├── core/              # 核心模块
│   │   │   ├── database/      # 数据库连接（Neo4j, PostgreSQL, Redis, Chroma）
│   │   │   ├── ontology/      # 本体引擎
│   │   │   ├── data_sources/  # 多数据源管理
│   │   │   │   ├── base.py    # 数据源基类
│   │   │   │   ├── tdx.py     # 通达信数据源
│   │   │   │   ├── tencent.py # 腾讯数据源
│   │   │   │   └── eastmoney.py # 东方财富数据源
│   │   │   ├── collectors/     # 数据采集器
│   │   │   │   ├── base.py    # 采集器基类
│   │   │   │   ├── market_collector.py  # 行情采集器
│   │   │   │   ├── news_collector.py     # 新闻采集器
│   │   │   │   └── financial_collector.py # 财务采集器
│   │   │   ├── services/      # 业务服务层
│   │   │   └── tasks/         # 定时任务
│   │   ├── models/            # 数据模型
│   │   ├── repositories/      # 数据仓库
│   │   └── utils/             # 工具函数
│   └── tests/                 # 测试
├── frontend/                   # 前端应用
│   └── src/
│       ├── views/
│       │   ├── Dashboard.vue       # 仪表盘
│       │   ├── Dragon.vue          # 龙头战法
│       │   ├── DataManagement.vue  # 数据管理
│       │   ├── Prediction.vue      # 预测分析
│       │   ├── Analysis.vue        # 智能分析
│       │   ├── GraphView.vue       # 图谱视图
│       │   ├── CompanyDetail.vue   # 公司详情
│       │   └── Events.vue          # 事件监控
│       ├── components/
│       │   ├── KLineChart.vue      # K线图表
│       │   ├── RisingStocks.vue    # 涨势股票
│       │   ├── CausalChainView.vue # 因果链视图
│       │   └── ExplainabilityPanel.vue # 可解释性面板
│       └── api/                    # API 调用
├── docker/                     # Docker 配置
│   ├── neo4j/                 # Neo4j 数据卷
│   ├── postgres/              # PostgreSQL 数据卷
│   ├── timescale/             # TimescaleDB 数据卷
│   └── redis/                 # Redis 数据卷
├── ontology/                   # 本体定义
│   └── core/                  # OWL 本体文件
├── data/                       # 数据处理
├── models/                     # AI 模型
├── scripts/                    # 脚本
│   ├── init_db_dragon.py      # 龙头战法初始化
│   ├── init_leader_strategy.py # 龙头策略初始化
│   ├── init_leader_full.py    # 完整初始化
│   ├── manage_db.sh           # 数据库管理脚本
│   └── quick_start.sh         # 快速启动脚本
├── docs/                       # 文档
├── DOCKER_DATABASE.md          # Docker 数据库文档
├── DATABASE_ARCHITECTURE.md   # 数据库架构文档
└── README.md
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd StockOntology

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置数据库连接等
```

### 3. 启动 Docker 服务

```bash
# 启动所有数据库服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 管理数据库服务
./manage_db.sh status    # 查看状态
./manage_db.sh start     # 启动服务
./manage_db.sh stop      # 停止服务
./manage_db.sh restart   # 重启服务
```

### 4. 初始化数据库

```bash
# 初始化龙头战法数据
python init_db_dragon.py

# 或使用完整初始化
python init_leader_full.py
```

### 5. 启动服务

```bash
# 方式一：使用快速启动脚本
./quick_start.sh

# 方式二：手动启动
# 终端 1: 启动后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2: 启动前端
cd frontend
npm run dev

# 访问应用
open http://localhost:3000
```

### 6. 访问服务

- 前端页面: http://localhost:3000
- API 文档: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## API 接口

### 龙头战法 API

- `GET /api/v1/dragon/stocks` - 获取龙头股列表
- `GET /api/v1/dragon/stock/{stock_code}` - 获取龙头股详情
- `GET /api/v1/dragon/industry/{industry}` - 按行业查询龙头股
- `GET /api/v1/dragon/supply-chain/{stock_code}` - 获取供应链关系
- `GET /api/v1/dragon/moat/{stock_code}` - 获取护城河分析
- `GET /api/v1/dragon/sector/{sector}` - 获取板块龙头

### 任务调度 API

- `GET /api/v1/scheduler/status` - 获取调度器状态
- `GET /api/v1/scheduler/tasks` - 获取所有任务列表
- `POST /api/v1/scheduler/trigger/{task_name}` - 触发任务
- `GET /api/v1/scheduler/logs/{task_name}` - 获取任务日志
- `GET /api/v1/scheduler/cache/{cache_key}` - 获取缓存数据

### 本体管理

- `GET /api/v1/ontology/classes` - 获取所有类定义
- `GET /api/v1/ontology/properties` - 获取所有属性定义
- `GET /api/v1/ontology/validate` - 验证本体

### 知识图谱

- `GET /api/v1/graph/stats` - 获取图谱统计
- `POST /api/v1/graph/query` - 执行 Cypher 查询
- `GET /api/v1/graph/subgraph` - 获取子图

### 公司管理

- `GET /api/v1/companies` - 获取公司列表
- `GET /api/v1/companies/{stock_code}` - 获取公司详情
- `GET /api/v1/companies/{stock_code}/graph` - 获取公司关系图谱

### 行业管理

- `GET /api/v1/industries` - 获取行业列表
- `GET /api/v1/industries/{code}/chain` - 获取产业链

### 事件管理

- `GET /api/v1/events` - 获取事件列表
- `GET /api/v1/events/{event_id}/impact` - 获取事件影响

### 投资者管理

- `GET /api/v1/investors` - 获取投资者列表
- `GET /api/v1/investors/{investor_id}/holdings` - 获取投资者持仓

## 核心模块

### 1. 龙头战法模块 (Dragon Strategy)

基于"龙头战法"投资理念，重点分析：

- **龙头股识别**：识别各行业龙头，分析市值、ROE、技术护城河
- **供应链分析**：追踪上下游供应链关系，识别关键配套企业
- **护城河评估**：从技术壁垒、规模效应、品牌优势等维度评估
- **板块联动**：分析板块内股票的联动效应和轮动规律

**重点领域**：
- 半导体/芯片
- AI/人工智能
- 航天军工
- 机器人
- 算力/数据中心
- 消费电子

### 2. 多数据源系统 (Multi-Data Source)

统一的数据源管理系统，支持：

| 数据源 | 优先级 | 特点 |
|--------|--------|------|
| 通达信 (TDX) | 最高 | 不封IP，数据稳定 |
| 腾讯 | 中 | 不封IP，响应快 |
| 东方财富 | 低 | 数据全面，易封IP |

**特性**：
- 自动降级：优先使用稳定数据源，失败时自动切换
- 防封策略：请求间隔控制、随机抖动、指数退避
- 会话复用：保持连接减少开销

### 3. 定时任务系统 (Scheduler)

自动化的数据采集和处理任务：

- **行情数据采集**：每日自动采集 OHLCV 数据
- **新闻情报采集**：实时采集热点新闻，LLM 自动分类
- **财务数据采集**：定期采集财务报表
- **事件因果推理**：自动推理事件影响传导链
- **预测扫描**：每日扫描所有股票，筛选看涨标的

### 4. 知识图谱 (Knowledge Graph)

基于 Neo4j 构建的股票知识图谱：

- **实体类型**：公司、行业、概念、事件、投资者
- **关系类型**：供应链、竞争、参股、上下游
- **图查询**：支持 Cypher 查询，可视化展示

## 数据库架构

### Neo4j - 图数据库
- 核心知识图谱
- 公司关系网络
- 事件传导链

### PostgreSQL - 关系数据库
- 用户数据
- 系统配置
- 业务日志

### TimescaleDB - 时序数据库
- 行情历史数据
- 财务指标时序
- 预测结果存储

### Redis - 缓存数据库
- 会话缓存
- 实时行情缓存
- 查询结果缓存

### ChromaDB - 向量数据库
- 文本向量化存储
- 语义搜索
- RAG 知识库

## 开发进度

### 阶段 1：项目基础设施 ✅

- [x] 项目结构初始化
- [x] 配置管理模块
- [x] 数据库连接模块（Neo4j、PostgreSQL、Redis、TimescaleDB、ChromaDB）
- [x] 数据模型定义
- [x] 本体 Schema 定义
- [x] 数据仓库层
- [x] API 路由框架
- [x] 工具函数库

### 阶段 2：本体定义与管理 ✅

- [x] OWL 本体文件（company.owl, industry.owl, financial.owl, event.owl, investor.owl）
- [x] 本体管理引擎（基于 RDFLib）
- [x] 本体验证器
- [x] 本体 API
- [x] 图谱构建器
- [x] 图谱查询服务
- [x] 图谱统计服务
- [x] 采集器框架
- [x] 数据处理管道

### 阶段 3：数据采集 ✅

- [x] 采集器基类框架
- [x] 多数据源系统（通达信、腾讯、东方财富）
- [x] 防封策略实现
- [x] 行情数据采集器
- [x] 财务数据采集器
- [x] 新闻舆情采集器
- [x] 采集器管理器
- [x] 数据采集 API

### 阶段 4：知识图谱 ✅

- [x] 图谱构建器
- [x] 图谱查询服务
- [x] 图谱统计服务
- [x] 图谱更新器

### 阶段 5：龙头战法 ✅

- [x] 龙头股识别算法
- [x] 供应链分析
- [x] 护城河评估模型
- [x] 板块联动分析
- [x] 龙头战法 API
- [x] 龙头战法前端页面

### 阶段 6：任务调度 ✅

- [x] 调度器框架
- [x] 定时任务配置
- [x] 任务触发 API
- [x] 日志管理
- [x] 缓存管理
- [x] 数据管理前端页面

### 阶段 7：LLM 智能分析 ✅

- [x] LLM 服务集成
- [x] RAG 问答服务
- [x] 情感分析器
- [x] LLM API

### 阶段 8：AI 预测模型 ✅

- [x] 特征工程（技术指标计算）
- [x] 预测服务（趋势、风险）
- [x] 相似模式查找
- [x] 预测 API

### 阶段 9：前端应用 ✅

- [x] Vue 3 + TypeScript 项目
- [x] Element Plus UI 框架
- [x] ECharts 图表可视化
- [x] 仪表盘页面
- [x] 龙头战法页面
- [x] 数据管理页面
- [x] 知识图谱可视化
- [x] K线图表组件
- [x] 因果链视图组件
- [x] 智能分析页面（LLM 聊天）
- [x] 预测模型页面
- [x] 事件监控页面
- [x] 公司详情页面
- [x] Docker 部署配置

### 阶段 10：Docker 部署 ✅

- [x] Docker Compose 配置
- [x] Neo4j 容器化
- [x] PostgreSQL 容器化
- [x] TimescaleDB 容器化
- [x] Redis 容器化
- [x] 服务健康检查
- [x] 数据卷管理

## 环境变量配置

```bash
# 数据库连接
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=stock_ontology
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

TIMESCALE_HOST=localhost
TIMESCALE_PORT=5433
TIMESCALE_DB=stock_timeseries
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=your_password

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# LLM 配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目链接：https://github.com/your-username/StockOntology
- 问题反馈：Issues

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Neo4j](https://neo4j.com/)
- [PyTorch](https://pytorch.org/)
- [LangChain](https://langchain.com/)
- [mootdx](https://github.com/mootdx/mootdx) - 通达信数据接口
- [AKShare](https://akshare.akfamily.xyz/) - A股数据采集
