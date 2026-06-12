"""
图谱构建器

提供知识图谱的构建功能。
扩展功能：
- AnalysisResult 节点（分析结果留痕）
- CausalChain 节点（因果传导链记录）
- ReasoningStep 节点（推理步骤记录）
- PredictionRecord 节点（预测记录留痕）
- SentimentRecord 节点（情感分析记录）
- TechnicalIndicator 节点（技术指标快照）
- StockPrice 节点（行情数据）
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.core.database import get_neo4j_client
from app.core.database.neo4j_schema import get_init_schema_queries


class GraphBuilder:
    """图谱构建器"""

    def __init__(self):
        """初始化图谱构建器"""
        self._neo4j = None

    @property
    def neo4j(self):
        """获取 Neo4j 客户端"""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    def init_schema(self):
        """初始化数据库 Schema"""
        queries = get_init_schema_queries()
        for query in queries:
            try:
                self.neo4j.execute_write(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Schema init warning: {e}")
        logger.info("Schema initialized")

    def create_company(self, company_data: Dict[str, Any]) -> bool:
        """
        创建公司节点

        Args:
            company_data: 公司数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (c:Company {stockCode: $stockCode})
            SET c += $properties
            RETURN c
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": company_data.get("stockCode"),
                    "properties": company_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create company: {e}")
            return False

    def create_industry(self, industry_data: Dict[str, Any]) -> bool:
        """
        创建行业节点

        Args:
            industry_data: 行业数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (i:Industry {code: $code})
            SET i += $properties
            RETURN i
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "code": industry_data.get("code"),
                    "properties": industry_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create industry: {e}")
            return False

    def create_financial_report(self, report_data: Dict[str, Any]) -> bool:
        """
        创建财务报告节点

        Args:
            report_data: 财务报告数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (f:FinancialReport {
                stockCode: $stockCode,
                reportDate: $reportDate,
                reportType: $reportType
            })
            SET f += $properties
            RETURN f
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": report_data.get("stockCode"),
                    "reportDate": report_data.get("reportDate"),
                    "reportType": report_data.get("reportType"),
                    "properties": report_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create financial report: {e}")
            return False

    def create_event(self, event_data: Dict[str, Any]) -> bool:
        """
        创建事件节点

        Args:
            event_data: 事件数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (e:MarketEvent {eventId: $eventId})
            SET e += $properties
            RETURN e
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "eventId": event_data.get("eventId"),
                    "properties": event_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return False

    def create_investor(self, investor_data: Dict[str, Any]) -> bool:
        """
        创建投资者节点

        Args:
            investor_data: 投资者数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (inv:Investor {investorId: $investorId})
            SET inv += $properties
            RETURN inv
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "investorId": investor_data.get("investorId"),
                    "properties": investor_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create investor: {e}")
            return False

    def create_company_industry_relationship(
        self,
        stock_code: str,
        industry_code: str,
    ) -> bool:
        """
        创建公司-行业关系

        Args:
            stock_code: 股票代码
            industry_code: 行业代码

        Returns:
            是否创建成功
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            MATCH (i:Industry {code: $industryCode})
            MERGE (c)-[:BELONGS_TO]->(i)
            RETURN c, i
        """
        try:
            self.neo4j.execute_write(
                query,
                {"stockCode": stock_code, "industryCode": industry_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create company-industry relationship: {e}")
            return False

    def create_company_report_relationship(
        self,
        stock_code: str,
        report_date: str,
        report_type: str,
    ) -> bool:
        """
        创建公司-报告关系

        Args:
            stock_code: 股票代码
            report_date: 报告日期
            report_type: 报告类型

        Returns:
            是否创建成功
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            MATCH (f:FinancialReport {
                stockCode: $stockCode,
                reportDate: $reportDate,
                reportType: $reportType
            })
            MERGE (c)-[:HAS_REPORT]->(f)
            RETURN c, f
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": stock_code,
                    "reportDate": report_date,
                    "reportType": report_type,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create company-report relationship: {e}")
            return False

    def create_company_competitor_relationship(
        self,
        stock_code1: str,
        stock_code2: str,
        competition_level: str = "Medium",
    ) -> bool:
        """
        创建公司竞争关系

        Args:
            stock_code1: 股票代码1
            stock_code2: 股票代码2
            competition_level: 竞争级别

        Returns:
            是否创建成功
        """
        query = """
            MATCH (c1:Company {stockCode: $stockCode1})
            MATCH (c2:Company {stockCode: $stockCode2})
            MERGE (c1)-[:COMPETES_WITH {level: $level}]->(c2)
            MERGE (c2)-[:COMPETES_WITH {level: $level}]->(c1)
            RETURN c1, c2
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode1": stock_code1,
                    "stockCode2": stock_code2,
                    "level": competition_level,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create competitor relationship: {e}")
            return False

    def create_company_supply_relationship(
        self,
        supplier_code: str,
        customer_code: str,
        supply_type: str = "Product",
    ) -> bool:
        """
        创建供应链关系

        Args:
            supplier_code: 供应商股票代码
            customer_code: 客户股票代码
            supply_type: 供应类型

        Returns:
            是否创建成功
        """
        query = """
            MATCH (supplier:Company {stockCode: $supplierCode})
            MATCH (customer:Company {stockCode: $customerCode})
            MERGE (supplier)-[:SUPPLY_TO {type: $type}]->(customer)
            RETURN supplier, customer
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "supplierCode": supplier_code,
                    "customerCode": customer_code,
                    "type": supply_type,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create supply relationship: {e}")
            return False

    def create_investor_holding_relationship(
        self,
        investor_id: str,
        stock_code: str,
        holding_data: Dict[str, Any],
    ) -> bool:
        """
        创建投资者持仓关系

        Args:
            investor_id: 投资者ID
            stock_code: 股票代码
            holding_data: 持仓数据

        Returns:
            是否创建成功
        """
        query = """
            MATCH (inv:Investor {investorId: $investorId})
            MATCH (c:Company {stockCode: $stockCode})
            MERGE (inv)-[:HOLDS]->(c)
            SET inv += $properties
            RETURN inv, c
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "investorId": investor_id,
                    "stockCode": stock_code,
                    "properties": holding_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create investor-holding relationship: {e}")
            return False

    def create_event_impact_relationship(
        self,
        event_id: str,
        target_code: str,
        target_type: str,
        impact_data: Dict[str, Any],
    ) -> bool:
        """
        创建事件影响关系

        Args:
            event_id: 事件ID
            target_code: 目标代码
            target_type: 目标类型（Company/Industry）
            impact_data: 影响数据

        Returns:
            是否创建成功
        """
        query = f"""
            MATCH (e:MarketEvent {{eventId: $eventId}})
            MATCH (t:{target_type} {{stockCode: $targetCode}})
            MERGE (e)-[:IMPACTS]->(t)
            SET e += $properties
            RETURN e, t
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "eventId": event_id,
                    "targetCode": target_code,
                    "properties": impact_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create event impact: {e}")
            return False

    def create_industry_hierarchy(
        self,
        parent_code: str,
        child_code: str,
    ) -> bool:
        """
        创建行业层级关系

        Args:
            parent_code: 上级行业代码
            child_code: 子行业代码

        Returns:
            是否创建成功
        """
        query = """
            MATCH (parent:Industry {code: $parentCode})
            MATCH (child:Industry {code: $childCode})
            MERGE (child)-[:SUB_INDUSTRY_OF]->(parent)
            RETURN parent, child
        """
        try:
            self.neo4j.execute_write(
                query,
                {"parentCode": parent_code, "childCode": child_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create industry hierarchy: {e}")
            return False

    def batch_create_companies(self, companies: List[Dict[str, Any]]) -> int:
        """
        批量创建公司

        Args:
            companies: 公司数据列表

        Returns:
            创建成功的数量
        """
        count = 0
        for company in companies:
            if self.create_company(company):
                count += 1
        return count

    def batch_create_industries(self, industries: List[Dict[str, Any]]) -> int:
        """
        批量创建行业

        Args:
            industries: 行业数据列表

        Returns:
            创建成功的数量
        """
        count = 0
        for industry in industries:
            if self.create_industry(industry):
                count += 1
        return count

    def batch_create_financial_reports(self, reports: List[Dict[str, Any]]) -> int:
        """
        批量创建财务报告

        Args:
            reports: 财务报告数据列表

        Returns:
            创建成功的数量
        """
        count = 0
        for report in reports:
            if self.create_financial_report(report):
                count += 1
        return count

    # ==================== 新增节点类型：分析推理相关 ====================

    def create_analysis_result(self, result_data: Dict[str, Any]) -> bool:
        """
        创建分析结果节点

        Args:
            result_data: 分析结果数据，应包含：
                - result_id: 结果ID
                - result_type: 结果类型（stock_analysis, event_impact 等）
                - content: 分析内容
                - confidence: 置信度
                - trace_id: 溯源ID

        Returns:
            是否创建成功
        """
        query = """
            MERGE (ar:AnalysisResult {traceId: $traceId})
            SET ar += $properties
            RETURN ar
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "traceId": result_data.get("trace_id", result_data.get("traceId")),
                    "properties": result_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create analysis result: {e}")
            return False

    def create_causal_chain(self, chain_data: Dict[str, Any]) -> bool:
        """
        创建因果传导链节点

        Args:
            chain_data: 因果链数据，应包含：
                - chain_id: 链ID
                - event_id: 源事件ID
                - event_name: 源事件名称
                - event_type: 事件类型
                - conclusion: 结论
                - overall_confidence: 综合置信度
                - total_affected_companies: 受影响公司数

        Returns:
            是否创建成功
        """
        query = """
            MERGE (cc:CausalChain {chainId: $chainId})
            SET cc += $properties
            RETURN cc
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "chainId": chain_data.get("chain_id", chain_data.get("chainId")),
                    "properties": chain_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create causal chain: {e}")
            return False

    def create_reasoning_step(self, step_data: Dict[str, Any]) -> bool:
        """
        创建推理步骤节点

        Args:
            step_data: 推理步骤数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (rs:ReasoningStep {stepId: $stepId})
            SET rs += $properties
            RETURN rs
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stepId": step_data.get("step_id", step_data.get("stepId")),
                    "properties": step_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create reasoning step: {e}")
            return False

    def create_prediction_record(self, prediction_data: Dict[str, Any]) -> bool:
        """
        创建预测记录节点

        Args:
            prediction_data: 预测记录数据，应包含：
                - record_id: 记录ID
                - stock_code: 股票代码
                - model_type: 模型类型
                - prediction: 预测结果
                - confidence: 置信度
                - features: 使用的特征

        Returns:
            是否创建成功
        """
        query = """
            MERGE (pr:PredictionRecord {recordId: $recordId})
            SET pr += $properties
            RETURN pr
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "recordId": prediction_data.get("record_id", prediction_data.get("recordId")),
                    "properties": prediction_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create prediction record: {e}")
            return False

    def create_sentiment_record(self, sentiment_data: Dict[str, Any]) -> bool:
        """
        创建情感记录节点

        Args:
            sentiment_data: 情感记录数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (sr:SentimentRecord {recordId: $recordId})
            SET sr += $properties
            RETURN sr
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "recordId": sentiment_data.get("record_id", sentiment_data.get("recordId")),
                    "properties": sentiment_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create sentiment record: {e}")
            return False

    def create_technical_indicator(self, indicator_data: Dict[str, Any]) -> bool:
        """
        创建技术指标快照节点

        Args:
            indicator_data: 技术指标数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (ti:TechnicalIndicator {
                stockCode: $stockCode,
                timestamp: $timestamp
            })
            SET ti += $properties
            RETURN ti
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": indicator_data.get("stock_code", indicator_data.get("stockCode")),
                    "timestamp": indicator_data.get("timestamp"),
                    "properties": indicator_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create technical indicator: {e}")
            return False

    def create_stock_price(self, price_data: Dict[str, Any]) -> bool:
        """
        创建行情数据节点

        Args:
            price_data: 行情数据，应包含：
                - stock_code: 股票代码
                - trade_date: 交易日期
                - open/high/low/close: OHLC
                - volume: 成交量
                - amount: 成交额

        Returns:
            是否创建成功
        """
        query = """
            MERGE (sp:StockPrice {
                stockCode: $stockCode,
                tradeDate: $tradeDate
            })
            SET sp += $properties
            RETURN sp
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": price_data.get("stock_code", price_data.get("stockCode")),
                    "tradeDate": price_data.get("trade_date", price_data.get("tradeDate")),
                    "properties": price_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create stock price: {e}")
            return False

    # ==================== 新增关系类型 ====================

    def create_chain_step_relationship(
        self,
        chain_id: str,
        step_id: str,
    ) -> bool:
        """
        创建因果链-推理步骤关系

        Args:
            chain_id: 因果链ID
            step_id: 推理步骤ID

        Returns:
            是否创建成功
        """
        query = """
            MATCH (cc:CausalChain {chainId: $chainId})
            MATCH (rs:ReasoningStep {stepId: $stepId})
            MERGE (cc)-[:HAS_STEP]->(rs)
            RETURN cc, rs
        """
        try:
            self.neo4j.execute_write(
                query, {"chainId": chain_id, "stepId": step_id}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create chain-step relationship: {e}")
            return False

    def create_step_node_relationship(
        self,
        step_id: str,
        node_id: str,
        node_type: str,
        direction: str = "from",
    ) -> bool:
        """
        创建推理步骤-实体节点关系

        Args:
            step_id: 推理步骤ID
            node_id: 实体节点ID（Neo4j element_id）
            node_type: 实体节点类型
            direction: 方向（from=源节点，to=目标节点）

        Returns:
            是否创建成功
        """
        rel_type = "FROM_NODE" if direction == "from" else "TO_NODE"
        query = f"""
            MATCH (rs:ReasoningStep {{stepId: $stepId}})
            MATCH (n) WHERE elementId(n) = $nodeId
            MERGE (rs)-[:{rel_type}]->(n)
            RETURN rs, n
        """
        try:
            self.neo4j.execute_write(
                query, {"stepId": step_id, "nodeId": node_id}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create step-node relationship: {e}")
            return False

    def create_analysis_evidence_relationship(
        self,
        trace_id: str,
        evidence_node_id: str,
    ) -> bool:
        """
        创建分析结果-依据关系

        Args:
            trace_id: 分析结果溯源ID
            evidence_node_id: 依据节点ID

        Returns:
            是否创建成功
        """
        query = """
            MATCH (ar:AnalysisResult {traceId: $traceId})
            MATCH (n) WHERE elementId(n) = $nodeId
            MERGE (ar)-[:EVIDENCED_BY]->(n)
            RETURN ar, n
        """
        try:
            self.neo4j.execute_write(
                query, {"traceId": trace_id, "nodeId": evidence_node_id}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create analysis-evidence relationship: {e}")
            return False

    def create_analysis_chain_relationship(
        self,
        trace_id: str,
        chain_id: str,
    ) -> bool:
        """
        创建分析结果-因果链关系

        Args:
            trace_id: 分析结果溯源ID
            chain_id: 因果链ID

        Returns:
            是否创建成功
        """
        query = """
            MATCH (ar:AnalysisResult {traceId: $traceId})
            MATCH (cc:CausalChain {chainId: $chainId})
            MERGE (ar)-[:BASED_ON_CHAIN]->(cc)
            RETURN ar, cc
        """
        try:
            self.neo4j.execute_write(
                query, {"traceId": trace_id, "chainId": chain_id}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create analysis-chain relationship: {e}")
            return False

    def create_prediction_company_relationship(
        self,
        record_id: str,
        stock_code: str,
    ) -> bool:
        """
        创建预测记录-公司关系

        Args:
            record_id: 预测记录ID
            stock_code: 股票代码

        Returns:
            是否创建成功
        """
        query = """
            MATCH (pr:PredictionRecord {recordId: $recordId})
            MATCH (c:Company {stockCode: $stockCode})
            MERGE (pr)-[:FOR_COMPANY]->(c)
            RETURN pr, c
        """
        try:
            self.neo4j.execute_write(
                query, {"recordId": record_id, "stockCode": stock_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create prediction-company relationship: {e}")
            return False

    def create_sentiment_company_relationship(
        self,
        record_id: str,
        stock_code: str,
    ) -> bool:
        """
        创建情感记录-公司关系

        Args:
            record_id: 情感记录ID
            stock_code: 股票代码

        Returns:
            是否创建成功
        """
        query = """
            MATCH (sr:SentimentRecord {recordId: $recordId})
            MATCH (c:Company {stockCode: $stockCode})
            MERGE (sr)-[:ABOUT]->(c)
            RETURN sr, c
        """
        try:
            self.neo4j.execute_write(
                query, {"recordId": record_id, "stockCode": stock_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create sentiment-company relationship: {e}")
            return False

    def create_stock_price_company_relationship(
        self,
        stock_code: str,
        trade_date: str,
    ) -> bool:
        """
        创建行情数据-公司关系

        Args:
            stock_code: 股票代码
            trade_date: 交易日期

        Returns:
            是否创建成功
        """
        query = """
            MATCH (sp:StockPrice {stockCode: $stockCode, tradeDate: $tradeDate})
            MATCH (c:Company {stockCode: $stockCode})
            MERGE (c)-[:HAS_PRICE]->(sp)
            RETURN c, sp
        """
        try:
            self.neo4j.execute_write(
                query, {"stockCode": stock_code, "tradeDate": trade_date}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create stock-price-company relationship: {e}")
            return False

    # ==================== 批量写入因果链 ====================

    def save_causal_chain(self, chain) -> bool:
        """
        将 CausalChain 对象完整写入图谱

        包括：
        - CausalChain 节点
        - ReasoningStep 节点
        - HAS_STEP 关系
        - FROM_NODE / TO_NODE 关系

        Args:
            chain: CausalChain 对象（来自 reasoning.causal_chain）

        Returns:
            是否写入成功
        """
        try:
            # 1. 创建 CausalChain 节点
            chain_dict = chain.to_dict()
            self.create_causal_chain({
                "chain_id": chain.chain_id,
                "chainId": chain.chain_id,
                "event_id": chain.event_id,
                "event_name": chain.event_name,
                "event_type": chain.event_type,
                "conclusion": chain.conclusion,
                "overall_confidence": chain.overall_confidence,
                "total_affected_companies": chain.total_affected_companies,
                "timestamp": chain.created_at.isoformat(),
            })

            # 2. 创建 ReasoningStep 节点和关系
            for step in chain.steps:
                self.create_reasoning_step({
                    "step_id": step.step_id,
                    "stepId": step.step_id,
                    "rule_applied": step.rule_applied,
                    "rule_id": step.rule_id,
                    "evidence": step.evidence,
                    "confidence": step.confidence,
                    "impact_direction": step.impact_direction,
                    "depth": step.depth,
                    "source_node_name": step.source_node_name,
                    "target_node_name": step.target_node_name,
                })

                # 创建 HAS_STEP 关系
                self.create_chain_step_relationship(chain.chain_id, step.step_id)

                # 创建 FROM_NODE 关系
                if step.source_node_id:
                    self.create_step_node_relationship(
                        step.step_id, step.source_node_id,
                        step.source_node_type, "from"
                    )

                # 创建 TO_NODE 关系
                if step.target_node_id:
                    self.create_step_node_relationship(
                        step.step_id, step.target_node_id,
                        step.target_node_type, "to"
                    )

            logger.info(
                f"Causal chain {chain.chain_id} saved to graph "
                f"with {len(chain.steps)} steps"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save causal chain: {e}")
            return False
