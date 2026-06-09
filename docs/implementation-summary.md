# StockOntology 实现总结

## 项目概述

基于本体论的股票分析预测系统，使用 LLM + Python + Vue + Neo4j + AI 算法构建。

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + ECharts |
| 后端 | Python FastAPI |
| 图数据库 | Neo4j |
| 本体工具 | RDFLib + OWL |
| LLM | LangChain + OpenAI |
| AI 算法 | 特征工程 + 技术指标 |

## 已完成功能

### 1. 项目基础设施 ✅

- 项目目录结构
- 配置管理（多环境支持）
- 数据库连接（Neo4j、PostgreSQL、Redis）
- 数据模型定义
- 工具函数库

### 2. 本体定义与管理 ✅

- OWL 本体文件（5个模块）
  - company.owl - 公司本体
  - industry.owl - 行业本体
  - financial.owl - 财务本体
  - event.owl - 事件本体
  - investor.owl - 投资者本体
- 本体管理器（基于 RDFLib）
- 本体验证器
- 本体 API

### 3. 数据采集 ✅

- 采集器基类框架
- 行情数据采集器（Tushare/AKShare）
- 财务数据采集器
- 新闻舆情采集器
- 采集器管理器
- 数据采集 API

### 4. 知识图谱 ✅

- 图谱构建器
- 图谱查询服务
- 图谱统计服务
- 图谱更新器
- 图谱 API

### 5. LLM 智能分析 ✅

- LLM 服务集成
- RAG 问答服务
- 情感分析器
- LLM API

### 6. AI 预测模型 ✅

- 特征工程（技术指标计算）
- 预测服务（趋势、风险）
- 相似模式查找
- 预测 API

### 7. 前端应用 ✅

- Vue 3 + TypeScript 项目
- Element Plus UI 框架
- ECharts 图表可视化
- 5个主要页面
  - 仪表盘
  - 知识图谱可视化
  - 智能分析
  - 预测模型
  - 事件监控
  - 公司详情

### 8. 部署配置 ✅

- Docker Compose 配置
- Dockerfile（前端/后端）
- Nginx 配置

## API 接口汇总

| 模块 | 接口前缀 | 功能 |
|------|---------|------|
| 本体 | /api/v1/ontology | 本体管理 |
| 图谱 | /api/v1/graph | 知识图谱 |
| 公司 | /api/v1/companies | 公司管理 |
| 行业 | /api/v1/industries | 行业管理 |
| 事件 | /api/v1/events | 事件管理 |
| 投资者 | /api/v1/investors | 投资者管理 |
| 财务 | /api/v1/financial | 财务数据 |
| 采集 | /api/v1/collectors | 数据采集 |
| LLM | /api/v1/llm | 智能分析 |
| 预测 | /api/v1/prediction | 股价预测 |

## 项目结构

```
StockOntology/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── api/               # API 路由（10个模块）
│   │   ├── core/              # 核心模块
│   │   │   ├── database/      # 数据库连接
│   │   │   ├── ontology/      # 本体引擎
│   │   │   ├── graph/         # 知识图谱
│   │   │   ├── llm/           # LLM 服务
│   │   │   ├── prediction/    # 预测服务
│   │   │   ├── collectors/    # 数据采集
│   │   │   └── pipelines/     # 数据管道
│   │   ├── models/            # 数据模型
│   │   ├── repositories/      # 数据仓库
│   │   └── utils/             # 工具函数
│   └── tests/                 # 测试
├── frontend/                   # 前端应用
│   └── src/
│       ├── views/             # 页面（6个）
│       ├── components/        # 组件
│       ├── api/               # API 客户端
│       └── router/            # 路由配置
├── ontology/                   # 本体定义
│   └── core/                  # OWL 本体文件
├── docker-compose.yml          # Docker 配置
└── docs/                       # 文档
```

## 启动方式

### 开发模式

```bash
# 后端
pip install -r requirements.txt
uvicorn backend.app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### Docker 模式

```bash
docker-compose up -d
```

## 访问地址

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- Neo4j：http://localhost:7474

## 核心特性

1. **本体驱动**：基于 OWL 本体建模，结构化表示股票市场知识
2. **知识图谱**：使用 Neo4j 构建大规模知识图谱，支持复杂关系查询
3. **智能分析**：集成 LLM 实现智能问答和文本分析
4. **AI 预测**：多种技术指标和预测算法
5. **可视化展示**：丰富的图表和图谱可视化
