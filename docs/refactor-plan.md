# 基于本体思想的股票分析预测系统——重构规划

> 版本：v1.0 | 日期：2026-06-09 | 状态：规划中

---

## 一、重构背景与目标

### 1.1 当前系统核心问题

| # | 问题 | 现状 |
|---|------|------|
| 1 | 无法自定义股票 | 硬编码 13 只股票，无用户关注列表 |
| 2 | 股票数据缺失 | 采集器有了但数据没入库，无 K 线图，预测用 `eps×20` 伪数据 |
| 3 | 股票情报缺失 | 新闻采集器存在但数据没持久化，情感分析仅关键词匹配 |
| 4 | 无真正的智能体 | LLM 只做单轮文本生成，无工具调用、无推理链、无规划能力 |
| 5 | 本体是摆设 | OWL 文件只定义静态实体关系，与分析/预测/LLM 完全割裂 |

### 1.2 重构目标

依据七大设计准则，将系统从"数据展示原型"重构为"语义统一、逻辑可控、全链路可解释的智能投研平台"。

**核心转变**：

```
当前：本体 = 数据库 ER 图（存数据）
目标：本体 = 分析引擎骨架（驱动推理、特征、LLM、可解释性）
```

---

## 二、设计准则（七大准则）

### 准则 1：领域本体标准化、语义唯一

- 同类概念唯一映射，多源异构数据必须完成本体语义对齐
- 杜绝同词异义、异词同义
- 为图谱推理、LLM 问答、AI 预测提供统一知识底座

### 准则 2：本体约束先行、推理逻辑可控

- 基于 OWL 公理 + SWRL 规则定义股票领域传导规则：
  - 政策传导：PolicyEvent → Industry → Company
  - 产业链传导：Event → CompanyA →[supplyTo] → CompanyB
  - 风险传导：Event → Company →[competesWith] → Company（竞争替代）
  - 行业层级传导：subIndustryOf 传递性
- 所有复杂业务分析结果必须支持推理路径回溯

### 准则 3：LLM 生成可控、去幻觉、本体约束

- 所有关联逻辑必须基于知识图谱数据，禁止编造
- 所有传导逻辑必须基于验证过的因果推理链
- 信息不足必须明确说明，不得猜测
- 每个结论必须标注依据来源（图谱节点 ID 或推理链 ID）

### 准则 4：AI 结果可解释、知识增强

- 时序模型（LSTM/Transformer）+ GNN 双融合
- 引入本体推理特征、产业链特征、政策舆情特征
- 禁止黑箱输出，模型结果必须接受本体业务规则校验

### 准则 5：架构低耦合、知识可迭代

- Python 后端统一封装本体推理、图谱查询、AI 预测接口
- 模块化调用，支持新业务场景扩展

### 准则 6：全链路留痕

- 推理记录、模型预测记录、LLM 问答记录全程留痕
- 所有入库数据、分析结论、推理结果、预测结果来源可信、链路可查

### 准则 7：可迭代可拓展

- 系统可长期迭代，避免硬编码
- 支持新本体模块、新传导规则、新预测模型的即插即用

---

## 三、系统架构：五层逐层对齐

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: 前后端交互层 (Vue 3 + FastAPI)                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ 因果链可视化  │ │ 可解释性面板  │ │ K线图+技术指标│         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: LLM 应用层                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │本体约束Prompt │ │ 去幻觉校验   │ │ 输出溯源留痕  │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 算法预测层 (PyTorch + Scikit-learn)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ 本体特征工程  │ │ GAT 图神经网络│ │ TransE 嵌入   │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
│  ┌──────────────┐ ┌──────────────┐                          │
│  │ LSTM 时序预测 │ │ 结果本体校验  │                          │
│  └──────────────┘ └──────────────┘                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 知识图谱层 (Neo4j)                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ 传导规则实例  │ │ 推理路径记录  │ │ 全链路留痕    │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 本体层 (OWL + RDFLib)                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ 语义标准化    │ │ 公理约束     │ │ SWRL传导规则  │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、Phase 1：本体层增强

> 目标：让本体从"静态实体关系"升级为"承载业务逻辑与公理规则的语义底座"

### 4.1 扩展 OWL 本体定义

**文件**: `ontology/core/stock_ontology.owl`

#### 新增类

| 类名 | 说明 | 父类 |
|------|------|------|
| `AnalysisResult` | 分析结果实体，所有分析结论的统一表示 | FinancialEntity |
| `CausalChain` | 因果传导链，记录完整推理路径 | — |
| `ReasoningStep` | 推理步骤，因果链中的单步 | — |
| `PredictionRecord` | 预测记录，模型预测的留痕实体 | — |
| `TechnicalIndicator` | 技术指标实体（MA/RSI/MACD 等） | — |
| `SentimentRecord` | 情感分析记录 | — |

#### 新增属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `transmitsTo` | ObjectProperty (Transitive) | 事件影响的传导关系 |
| `evidencedBy` | ObjectProperty | 分析结果的依据来源 |
| `hasReasoningStep` | ObjectProperty | 因果链包含的推理步骤 |
| `hasConfidence` | DatatypeProperty | 置信度 (0-1) |
| `hasTraceId` | DatatypeProperty | 溯源 ID |
| `hasTimestamp` | DatatypeProperty | 时间戳 |

#### 公理约束（OWL Restrictions）

```owl
<!-- Company 必须属于至少一个 Industry -->
<owl:Class rdf:about="Company">
    <rdfs:subClassOf>
        <owl:Restriction>
            <owl:onProperty rdf:resource="belongsToIndustry"/>
            <owl:someValuesFrom rdf:resource="Industry"/>
        </owl:Restriction>
    </rdfs:subClassOf>
</owl:Class>

<!-- AnalysisResult 必须有置信度和溯源ID -->
<owl:Class rdf:about="AnalysisResult">
    <rdfs:subClassOf>
        <owl:Restriction>
            <owl:onProperty rdf:resource="hasConfidence"/>
            <owl:someValuesFrom rdf:resource="xsd:decimal"/>
        </owl:Restriction>
    </rdfs:subClassOf>
</owl:Class>
```

### 4.2 SWRL 传导规则

**新建文件**: `ontology/core/rules.swrl`

| 规则名 | 逻辑 | 说明 |
|--------|------|------|
| 政策传导 | PolicyEvent(?e) ∧ impacts(?e, ?i) ∧ Industry(?i) ∧ belongsTo(?c, ?i) → impacts(?e, ?c) | 政策影响行业 → 行业内公司受影响 |
| 产业链传导 | impacts(?e, ?a) ∧ supplyTo(?a, ?b) → impacts(?e, ?b) | 事件影响上游 → 下游也被影响 |
| 竞争传导 | impacts(?e, ?a) ∧ competesWith(?a, ?b) → negatively_impacts(?e, ?b) | 利好 A → 利空竞对 B |
| 行业层级传导 | impacts(?e, ?i1) ∧ subIndustryOf(?i2, ?i1) → impacts(?e, ?i2) | 上级行业受影响 → 子行业也受影响 |

### 4.3 本体推理引擎

**新建文件**:
- `backend/app/core/reasoning/__init__.py`
- `backend/app/core/reasoning/ontology_reasoner.py`
- `backend/app/core/reasoning/causal_chain.py`

#### 核心类

```python
class OntologyReasoner:
    """本体推理引擎——将 OWL 公理和 SWRL 规则转化为可执行推理"""

    def trace_impact_chain(self, event_id: str) -> CausalChain:
        """推导事件的完整影响传导链（4 种传导）"""

    def classify_event(self, event_text: str) -> Dict:
        """基于本体约束自动分类事件类型"""

    def validate_with_ontology(self, entity_type: str, data: Dict) -> ValidationResult:
        """基于 OWL 公理约束校验数据一致性"""

    def get_accumulated_impact(self, stock_code: str, days: int = 30) -> float:
        """计算时间窗口内的累积事件影响分数"""

class CausalChain:
    """因果传导链——推理路径的结构化表示"""
    chain_id: str
    event_id: str
    steps: List[ReasoningStep]
    conclusion: str
    confidence: float

class ReasoningStep:
    """单步推理记录"""
    rule_applied: str      # 使用的规则
    source_node: str       # 源节点
    target_node: str       # 目标节点
    relationship: str      # 关系类型
    evidence: str          # 证据
    confidence: float      # 本步置信度
```

### 4.4 增强本体校验器

**修改文件**: `backend/app/core/ontology/ontology_validator.py`

新增校验维度：
- 公理约束校验：检查实例是否满足 OWL Restriction
- 传导规则完整性：检查 SWRL 规则覆盖度
- 语义对齐校验：多源数据是否映射到统一概念

---

## 五、Phase 2：知识图谱层扩展

> 目标：图谱从"存实体"扩展为"记录推理过程、支持全链路留痕"

### 5.1 新增节点类型

| 节点类型 | 关键属性 | 说明 |
|----------|----------|------|
| `AnalysisResult` | resultType, content, confidence, traceId, timestamp | 分析结论 |
| `CausalChain` | chainId, eventType, conclusion, confidence, timestamp | 因果传导链 |
| `ReasoningStep` | stepId, ruleApplied, evidence, confidence | 推理单步 |
| `PredictionRecord` | modelType, prediction, confidence, features, timestamp | 预测记录 |
| `SentimentRecord` | source, text, score, label, timestamp | 情感记录 |
| `TechnicalIndicator` | stockCode, ma5, ma10, ma20, rsi, macd, timestamp | 技术指标 |

### 5.2 新增关系类型

```
(:CausalChain)-[:HAS_STEP]->(:ReasoningStep)
(:ReasoningStep)-[:FROM_NODE]->(:FinancialEntity)
(:ReasoningStep)-[:TO_NODE]->(:FinancialEntity)
(:AnalysisResult)-[:EVIDENCED_BY]->(:FinancialEntity)
(:AnalysisResult)-[:BASED_ON_CHAIN]->(:CausalChain)
(:PredictionRecord)-[:FOR_COMPANY]->(:Company)
(:PredictionRecord)-[:USED_FEATURE]->(:TechnicalIndicator)
(:SentimentRecord)-[:ABOUT]->(:Company)
(:SentimentRecord)-[:FROM_SOURCE]->(:MarketEvent)
```

### 5.3 行情数据入库

**问题**: MarketDataCollector 采集了数据但没入库，预测用 `eps×20` 伪数据

**方案**:
- 在 Neo4j 新增 `StockPrice` 节点（日频数据）
- 或使用 TimescaleDB 存储高频数据，Neo4j 只存聚合指标
- 采集器采集后自动写入存储层
- 预测 API 从存储层读取真实历史数据

### 5.4 推理路径记录

所有 OntologyReasoner 产生的推理结果，自动写入 Neo4j 为 CausalChain + ReasoningStep 节点。

---

## 六、Phase 3：算法预测层

> 目标：从"黑箱预测"到"知识增强 + 可解释 + 接受本体校验"

### 6.1 本体特征工程

**修改文件**: `backend/app/core/prediction/feature_engineering.py`

新增 `OntologyFeatureExtractor`：

| 特征 | 来源 | 说明 |
|------|------|------|
| `industry_level` | 本体 Industry 层级 | 公司在行业层级中的位置 |
| `event_impact_score` | OntologyReasoner | 时间窗口内累积事件影响 |
| `supply_chain_risk` | 图谱 supplyTo 关系 | 上下游公司健康度 |
| `competition_pressure` | 图谱 competesWith 关系 | 同行业竞对对比 |
| `institutional_sentiment` | 图谱 HOLDS 关系变化 | 机构持仓变化趋势 |
| `graph_centrality` | 图谱 PageRank | 公司在知识图谱中的重要性 |

### 6.2 GNN 模型

**新建文件**: `backend/app/core/models/gnn/stock_gat.py`

- 输入：节点特征（基本面 + 技术指标 + 本体特征）+ 边（本体定义的关系）
- 关系类型来自本体：belongs_to, competes_with, supply_to, impacts
- 输出：节点级别的涨跌预测

### 6.3 KG Embedding

**新建文件**: `backend/app/core/models/kg_embedding/transe.py`

- 训练数据来自 Neo4j 三元组
- 用途：实体相似度计算、链接预测、GNN 输入特征

### 6.4 预测服务重构

**修改文件**: `backend/app/core/prediction/prediction_service.py`

```
输入特征融合：
  ├─→ 技术指标特征 (MA, MACD, RSI, BOLL) ─────┐
  ├─→ 基本面特征 (PE, PB, ROE, Revenue) ───────┤
  ├─→ 本体特征 (行业层级, 事件影响, 供应链风险) ┼─→ 融合模型 ─→ 预测
  ├─→ 图谱特征 (PageRank, 社区, 中心性) ───────┤
  └─→ 情感特征 (新闻情感, 研报情感) ───────────┘
                                              │
                                      ┌───────┴───────┐
                                      │  本体规则校验   │
                                      │  (禁止黑箱输出) │
                                      └───────────────┘
```

### 6.5 预测结果本体校验

- 预测看涨，但所在行业被多个 High 级事件负面影响 → 标记矛盾
- 预测看涨，但机构持仓连续减持 → 标记需解释
- 校验结果附在预测输出中

---

## 七、Phase 4：LLM 应用层

> 目标：从"自由文本生成"到"本体约束 + 去幻觉 + 全链路可溯源"

### 7.1 本体约束 Prompt

**修改文件**: `backend/app/core/llm/llm_service.py`

System Prompt 约束：
1. 所有关联逻辑必须基于提供的知识图谱数据，禁止编造
2. 所有传导逻辑必须基于提供的因果推理链
3. 信息不足必须明确说明，不得猜测
4. 每个结论必须标注依据来源（图谱节点 ID 或推理链 ID）
5. 输出格式必须包含：结论、依据、推理链、置信度

### 7.2 RAG 增强

**修改文件**: `backend/app/core/llm/rag_service.py`

- 注入因果推理链作为上下文
- 注入本体 schema 告知 LLM 数据的语义类型
- 注入历史分析结果作为参考

### 7.3 LLM 输出溯源

所有 LLM 输出记录为 `AnalysisResult` 节点写入 Neo4j：
- prompt → 输入
- response → 输出
- referenced_nodes → 引用的图谱节点
- causal_chains_used → 使用的推理链
- timestamp → 时间戳

---

## 八、Phase 5：前后端交互层

> 目标：因果链可视化 + 可解释性面板 + K 线图 + 溯源跳转

### 8.1 新增组件

| 组件 | 说明 |
|------|------|
| `CausalChainView.vue` | 因果传导链可视化（节点=实体，边=传导关系，标注规则+置信度） |
| `ExplainabilityPanel.vue` | 可解释性面板（展示推理链路，支持溯源跳转） |
| `KLineChart.vue` | K 线图组件（ECharts，叠加技术指标+预测结果+置信区间） |
| `SentimentTrend.vue` | 情感趋势图（时间轴+正负面情感分数） |

### 8.2 页面改造

| 页面 | 改造内容 |
|------|----------|
| `Prediction.vue` | 去硬编码 → 动态股票列表；新增 K 线图 + 可解释性面板 + 本体特征展示 |
| `Analysis.vue` | LLM 回答展示图谱节点引用 + 因果链 + 置信度 + 溯源跳转 |
| `GraphView.vue` | 新增"传导链模式"（点击事件→展示推理路径）+ 分析结果图层 |
| `CompanyDetail.vue` | 新增 K 线图 + 情感趋势 + 因果链面板 |
| `Dashboard.vue` | 行业分布饼图改用真实数据 |

### 8.3 API 扩展

**新建**: `backend/app/api/reasoning.py`

| 端点 | 方法 | 说明 |
|------|------|------|
| `POST /reasoning/trace-chain` | trace_chain | 推导因果链 |
| `GET /reasoning/chains/{stock_code}` | get_chains | 查询历史因果链 |
| `POST /reasoning/validate` | validate | 校验预测结果 |

---

## 九、实施顺序

```
Phase 1: 本体层增强 (基础，必须先完成)
  1.1 扩展 OWL 定义（新增类、属性、公理约束）
  1.2 SWRL 传导规则
  1.3 推理引擎 (OntologyReasoner + CausalChain)
  1.4 增强校验器
       │
       ▼
Phase 2: 知识图谱层扩展
  2.1 扩展 Schema（新增节点/关系类型）
  2.2 行情数据入库
  2.3 推理路径记录
       │
       ▼
Phase 3: 算法预测层
  3.1 本体特征工程
  3.2 GNN 模型 (StockGAT)
  3.3 KG Embedding (TransE)
  3.4 预测服务重构
  3.5 结果本体校验
       │
       ▼
Phase 4: LLM 应用层
  4.1 本体约束 Prompt
  4.2 RAG 增强
  4.3 输出溯源留痕
       │
       ▼
Phase 5: 前后端交互层
  5.1 因果链可视化组件
  5.2 可解释性面板
  5.3 K 线图组件
  5.4 页面改造
```

Phase 2-3 可部分并行。Phase 4 依赖 Phase 1+2。Phase 5 依赖 Phase 3+4。

---

## 十、关键文件清单

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 修改 | `ontology/core/stock_ontology.owl` | 新增 6 个类、6 个属性、公理约束 |
| 新建 | `ontology/core/rules.swrl` | 4 条 SWRL 传导规则 |
| 新建 | `backend/app/core/reasoning/__init__.py` | 推理模块初始化 |
| 新建 | `backend/app/core/reasoning/ontology_reasoner.py` | 核心推理引擎 |
| 新建 | `backend/app/core/reasoning/causal_chain.py` | 因果链数据结构 |
| 修改 | `backend/app/core/ontology/ontology_validator.py` | 新增公理约束校验 |
| 修改 | `backend/app/core/graph/graph_builder.py` | 新增 6 种节点 + 8 种关系 |
| 修改 | `backend/app/core/prediction/feature_engineering.py` | 新增 OntologyFeatureExtractor |
| 修改 | `backend/app/core/prediction/prediction_service.py` | 融合本体特征 + 校验 |
| 新建 | `backend/app/core/models/gnn/stock_gat.py` | GAT 模型 |
| 新建 | `backend/app/core/models/gnn/__init__.py` | GNN 模块初始化 |
| 新建 | `backend/app/core/models/kg_embedding/transe.py` | TransE 嵌入 |
| 新建 | `backend/app/core/models/kg_embedding/__init__.py` | KG Embedding 初始化 |
| 修改 | `backend/app/core/llm/llm_service.py` | 本体约束 Prompt |
| 修改 | `backend/app/core/llm/rag_service.py` | 注入推理链上下文 |
| 修改 | `backend/app/api/prediction.py` | 使用真实数据 |
| 新建 | `backend/app/api/reasoning.py` | 推理 API |
| 新建 | `frontend/src/components/CausalChainView.vue` | 因果链可视化 |
| 新建 | `frontend/src/components/ExplainabilityPanel.vue` | 可解释性面板 |
| 新建 | `frontend/src/components/KLineChart.vue` | K 线图组件 |
| 新建 | `frontend/src/components/SentimentTrend.vue` | 情感趋势图 |
| 修改 | `frontend/src/views/Prediction.vue` | 去硬编码 + 可解释性 |
| 修改 | `frontend/src/views/Analysis.vue` | 溯源展示 |
| 修改 | `frontend/src/views/GraphView.vue` | 传导链模式 |
| 修改 | `frontend/src/views/CompanyDetail.vue` | K 线图 + 情感趋势 |
| 修改 | `frontend/src/views/Dashboard.vue` | 真实数据 |

---

## 十一、验证方式

### Phase 1 验证
- [ ] 创建 PolicyEvent（如"央行降准"），调用 `trace_impact_chain()`，自动推导出受影响行业和公司
- [ ] 创建无 `belongsToIndustry` 的 Company，`validate_with_ontology()` 报错
- [ ] SWRL 规则文件可被解析和执行

### Phase 2 验证
- [ ] 采集器采集真实行情数据后自动写入 Neo4j/TimescaleDB
- [ ] 查询 CausalChain 节点，推理路径完整
- [ ] 查询 PredictionRecord 节点，预测记录可追溯

### Phase 3 验证
- [ ] 对比"纯技术指标" vs "技术指标+本体特征"的预测效果
- [ ] 预测结果通过本体校验（矛盾检测）
- [ ] GNN 模型可训练并输出节点嵌入

### Phase 4 验证
- [ ] LLM 输出包含图谱节点引用
- [ ] 故意编造关系时，输出校验拦截
- [ ] 问答记录可从图谱追溯

### Phase 5 验证
- [ ] 因果链动画展示完整传导路径
- [ ] 点击预测结论可追溯到完整推理链
- [ ] K 线图展示真实历史数据 + 预测结果
