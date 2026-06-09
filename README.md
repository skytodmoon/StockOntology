# StockOntology - 基于本体论的股票分析预测系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-orange.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 项目简介

StockOntology 是一个基于本体论的股票分析预测系统，通过知识图谱、大语言模型和 AI 算法，提供智能化的股票分析和预测能力。

### 核心特性

- **本体驱动**：基于 OWL 本体建模，系统化表示股票市场知识
- **知识图谱**：使用 Neo4j 构建大规模股票知识图谱
- **智能分析**：集成 LLM 实现智能问答和文本分析
- **AI 预测**：多种机器学习模型进行股价预测
- **可视化展示**：丰富的图表和图谱可视化

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + ECharts |
| 后端 | Python FastAPI |
| 图数据库 | Neo4j |
| 时序数据库 | TimescaleDB |
| 向量数据库 | Milvus / ChromaDB |
| LLM | LangChain + OpenAI |
| AI 算法 | PyTorch + Scikit-learn |
| 本体工具 | OWL API + RDFLib |

## 项目结构

```
StockOntology/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── api/               # API 路由
│   │   ├── core/              # 核心模块
│   │   │   ├── database/      # 数据库连接
│   │   │   ├── ontology/      # 本体引擎
│   │   │   └── ...
│   │   ├── models/            # 数据模型
│   │   ├── repositories/      # 数据仓库
│   │   └── utils/             # 工具函数
│   └── tests/                 # 测试
├── frontend/                   # 前端应用
├── ontology/                   # 本体定义
│   └── core/                  # OWL 本体文件
├── data/                       # 数据处理
├── models/                     # AI 模型
├── docs/                       # 文档
└── scripts/                    # 脚本
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

### 3. 启动服务

```bash
# 启动后端服务
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 访问 API 文档
open http://localhost:8000/docs
```

### 4. 使用 Docker（可选）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

## API 接口

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

## 开发进度

### 阶段 1：项目基础设施 ✅

- [x] 项目结构初始化
- [x] 配置管理模块
- [x] 数据库连接模块（Neo4j、PostgreSQL、Redis）
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
- [x] 行情数据采集器（Tushare/AKShare）
- [x] 财务数据采集器
- [x] 新闻舆情采集器
- [x] 采集器管理器
- [x] 数据采集 API

### 阶段 4：知识图谱 ✅

- [x] 图谱构建器
- [x] 图谱查询服务
- [x] 图谱统计服务
- [x] 图谱更新器

### 阶段 5：LLM 智能分析 ✅

- [x] LLM 服务集成
- [x] RAG 问答服务
- [x] 情感分析器
- [x] LLM API

### 阶段 6：AI 预测模型 ✅

- [x] 特征工程（技术指标计算）
- [x] 预测服务（趋势、风险）
- [x] 相似模式查找
- [x] 预测 API

### 阶段 7：前端应用 ✅

- [x] Vue 3 + TypeScript 项目
- [x] Element Plus UI 框架
- [x] ECharts 图表可视化
- [x] 仪表盘页面
- [x] 知识图谱可视化
- [x] 智能分析页面（LLM 聊天）
- [x] 预测模型页面
- [x] 事件监控页面
- [x] 公司详情页面
- [x] Docker 部署配置

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
