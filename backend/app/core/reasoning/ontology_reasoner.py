"""
本体推理引擎

将 OWL 公理和 SWRL 规则转化为可执行推理，实现四种核心传导：
1. 直接传导：Event →[impacts]→ Company
2. 政策传导：PolicyEvent →[impacts]→ Industry →[belongsTo]⁻¹ → Company
3. 产业链传导：Event → CompanyA →[supplyTo] → CompanyB
4. 竞争传导：Event 利好 CompanyA →[competesWith] → CompanyB（竞争替代）
5. 行业层级传导：subIndustryOf 传递性

所有推理结果记录为 CausalChain + ReasoningStep，支持全链路留痕。
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from app.core.database import get_neo4j_client
from .causal_chain import CausalChain, ReasoningStep


class OntologyReasoner:
    """
    本体推理引擎

    核心职责：
    1. 基于图谱数据和传导规则，推导事件的完整影响传导链
    2. 基于本体约束，自动分类事件类型
    3. 基于 OWL 公理，校验数据一致性
    4. 计算某股票在时间窗口内的累积事件影响分数
    """

    # 影响级别到分数的映射
    IMPACT_LEVEL_SCORES = {
        "High": 1.0,
        "Medium": 0.6,
        "Low": 0.3,
    }

    # 置信度衰减系数（每传导一步）
    DEFAULT_CONFIDENCE_DECAY = 0.8

    def __init__(self):
        """初始化推理引擎"""
        self._neo4j = None

    @property
    def neo4j(self):
        """获取 Neo4j 客户端"""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    # ==================== 核心推理方法 ====================

    def trace_impact_chain(
        self,
        event_id: str,
        max_depth: int = 3,
        include_competition: bool = True,
    ) -> CausalChain:
        """
        给定事件，推导完整影响传导链。

        实现 4 种传导：
        1. 直接传导：Event →[impacts]→ Company
        2. 行业传导：Event →[impacts]→ Industry →[belongsTo]⁻¹ → Company
        3. 产业链传导：Event → CompanyA →[supplyTo] → CompanyB
        4. 竞争传导：Event 利好 CompanyA →[competesWith] → CompanyB

        Args:
            event_id: 事件 ID
            max_depth: 最大传导深度
            include_competition: 是否包含竞争传导

        Returns:
            CausalChain 对象，包含完整推理路径
        """
        # 获取事件信息
        event_info = self._get_event_info(event_id)
        if not event_info:
            logger.warning(f"Event not found: {event_id}")
            return CausalChain(event_id=event_id, conclusion="事件不存在")

        chain = CausalChain(
            event_id=event_id,
            event_name=event_info.get("title", ""),
            event_type=event_info.get("eventType", ""),
        )

        try:
            # Step 1: 直接影响
            direct_impacts = self._query_direct_impact(event_id)
            for impact in direct_impacts:
                step = ReasoningStep(
                    rule_applied="直接影响",
                    rule_id="R005",
                    source_node_id=event_id,
                    source_node_type="MarketEvent",
                    source_node_name=chain.event_name,
                    target_node_id=impact.get("node_id", ""),
                    target_node_type=impact.get("node_type", "Company"),
                    target_node_name=impact.get("name", ""),
                    relationship="IMPACTS",
                    evidence=f"事件 {chain.event_name} 直接影响 {impact.get('name', '')}",
                    confidence=1.0,
                    impact_direction=impact.get("direction", "neutral"),
                )
                chain.add_step(step)

            # Step 2: 行业传导
            industry_impacts = self._query_industry_transmission(event_id)
            for impact in industry_impacts:
                confidence = self._decay_confidence(1.0, 1)
                step = ReasoningStep(
                    rule_applied="政策传导",
                    rule_id="R001",
                    source_node_id=impact.get("industry_id", ""),
                    source_node_type="Industry",
                    source_node_name=impact.get("industry_name", ""),
                    target_node_id=impact.get("company_id", ""),
                    target_node_type="Company",
                    target_node_name=impact.get("company_name", ""),
                    relationship="BELONGS_TO",
                    evidence=(
                        f"事件影响行业 [{impact.get('industry_name', '')}]，"
                        f"公司 [{impact.get('company_name', '')}] 属于该行业"
                    ),
                    confidence=confidence,
                    impact_direction=impact.get("direction", "neutral"),
                )
                chain.add_step(step)

            # Step 3: 行业层级传导
            hierarchy_impacts = self._query_industry_hierarchy_transmission(event_id)
            for impact in hierarchy_impacts:
                confidence = self._decay_confidence(1.0, 2)
                step = ReasoningStep(
                    rule_applied="行业层级传导",
                    rule_id="R004",
                    source_node_id=impact.get("source_industry_id", ""),
                    source_node_type="Industry",
                    source_node_name=impact.get("source_industry_name", ""),
                    target_node_id=impact.get("company_id", ""),
                    target_node_type="Company",
                    target_node_name=impact.get("company_name", ""),
                    relationship="SUB_INDUSTRY_OF",
                    evidence=(
                        f"行业 [{impact.get('source_industry_name', '')}] "
                        f"→ [{impact.get('target_industry_name', '')}] 层级传导，"
                        f"影响公司 [{impact.get('company_name', '')}]"
                    ),
                    confidence=confidence,
                    impact_direction=impact.get("direction", "neutral"),
                )
                chain.add_step(step)

            # Step 4: 产业链传导
            supply_impacts = self._query_supply_chain_transmission(event_id)
            for impact in supply_impacts:
                confidence = self._decay_confidence(1.0, 1) * 0.7  # 产业链传导额外衰减
                step = ReasoningStep(
                    rule_applied="产业链传导",
                    rule_id="R002",
                    source_node_id=impact.get("source_company_id", ""),
                    source_node_type="Company",
                    source_node_name=impact.get("source_company_name", ""),
                    target_node_id=impact.get("target_company_id", ""),
                    target_node_type="Company",
                    target_node_name=impact.get("target_company_name", ""),
                    relationship="SUPPLY_TO",
                    evidence=(
                        f"事件影响 [{impact.get('source_company_name', '')}]，"
                        f"通过供应链传导至 [{impact.get('target_company_name', '')}]"
                    ),
                    confidence=confidence,
                    impact_direction=impact.get("direction", "neutral"),
                )
                chain.add_step(step)

            # Step 5: 竞争传导（可选）
            if include_competition:
                competition_impacts = self._query_competition_transmission(event_id)
                for impact in competition_impacts:
                    confidence = self._decay_confidence(1.0, 1) * 0.6  # 竞争传导额外衰减
                    step = ReasoningStep(
                        rule_applied="竞争传导",
                        rule_id="R003",
                        source_node_id=impact.get("source_company_id", ""),
                        source_node_type="Company",
                        source_node_name=impact.get("source_company_name", ""),
                        target_node_id=impact.get("target_company_id", ""),
                        target_node_type="Company",
                        target_node_name=impact.get("target_company_name", ""),
                        relationship="COMPETES_WITH",
                        evidence=(
                            f"事件影响 [{impact.get('source_company_name', '')}]，"
                            f"竞争传导至 [{impact.get('target_company_name', '')}]"
                        ),
                        confidence=confidence,
                        impact_direction=impact.get("direction", "neutral"),
                    )
                    chain.add_step(step)

            # 计算综合置信度和受影响公司数
            chain.calculate_overall_confidence()
            chain.total_affected_companies = len(chain.get_affected_companies())
            chain.conclusion = (
                f"事件 [{chain.event_name}] 通过 {len(chain.steps)} 步推理，"
                f"影响 {chain.total_affected_companies} 家公司，"
                f"综合置信度 {chain.overall_confidence:.2f}"
            )

        except Exception as e:
            logger.error(f"Error tracing impact chain for event {event_id}: {e}")
            chain.conclusion = f"推理过程出错: {str(e)}"

        return chain

    # ==================== 查询方法 ====================

    def _get_event_info(self, event_id: str) -> Optional[Dict[str, Any]]:
        """获取事件信息"""
        query = """
            MATCH (e:MarketEvent {eventId: $event_id})
            RETURN e
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})
        if result:
            return dict(result[0]["e"])
        return None

    def _query_direct_impact(self, event_id: str) -> List[Dict[str, Any]]:
        """查询事件直接影响的实体"""
        query = """
            MATCH (e:MarketEvent {eventId: $event_id})-[r:IMPACTS]->(target)
            RETURN elementId(target) AS node_id,
                   labels(target)[0] AS node_type,
                   CASE
                     WHEN target:Company THEN target.stockName
                     WHEN target:Industry THEN target.name
                     ELSE toString(target)
                   END AS name,
                   r.impactDirection AS direction
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})
        return [dict(r) for r in result]

    def _query_industry_transmission(self, event_id: str) -> List[Dict[str, Any]]:
        """查询行业传导：Event → Industry → Company"""
        query = """
            MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(i:Industry)
                  <-[:BELONGS_TO]-(c:Company)
            RETURN elementId(i) AS industry_id,
                   i.name AS industry_name,
                   elementId(c) AS company_id,
                   c.stockName AS company_name,
                   c.stockCode AS stock_code,
                   'positive' AS direction
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})
        return [dict(r) for r in result]

    def _query_industry_hierarchy_transmission(
        self, event_id: str
    ) -> List[Dict[str, Any]]:
        """查询行业层级传导：subIndustryOf 传递性"""
        query = """
            // 向上传导：事件影响子行业 → 上级行业的其他公司
            MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(child:Industry)
                  -[:SUB_INDUSTRY_OF]->(parent:Industry)
                  <-[:BELONGS_TO]-(c:Company)
            WHERE NOT (e)-[:IMPACTS]->(c)
            RETURN elementId(child) AS source_industry_id,
                   child.name AS source_industry_name,
                   elementId(parent) AS target_industry_id,
                   parent.name AS target_industry_name,
                   elementId(c) AS company_id,
                   c.stockName AS company_name,
                   c.stockCode AS stock_code,
                   'positive' AS direction
            UNION
            // 向下传导：事件影响上级行业 → 子行业公司
            MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(parent:Industry)
                  <-[:SUB_INDUSTRY_OF]-(child:Industry)
                  <-[:BELONGS_TO]-(c:Company)
            WHERE NOT (e)-[:IMPACTS]->(c)
            RETURN elementId(parent) AS source_industry_id,
                   parent.name AS source_industry_name,
                   elementId(child) AS target_industry_id,
                   child.name AS target_industry_name,
                   elementId(c) AS company_id,
                   c.stockName AS company_name,
                   c.stockCode AS stock_code,
                   'positive' AS direction
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})
        return [dict(r) for r in result]

    def _query_supply_chain_transmission(
        self, event_id: str
    ) -> List[Dict[str, Any]]:
        """查询产业链传导：Event → CompanyA →[supplyTo] → CompanyB"""
        query = """
            MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(a:Company)
                  -[:SUPPLY_TO]->(b:Company)
            RETURN elementId(a) AS source_company_id,
                   a.stockName AS source_company_name,
                   elementId(b) AS target_company_id,
                   b.stockName AS target_company_name,
                   b.stockCode AS stock_code,
                   'positive' AS direction
            UNION
            MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(b:Company)
                  <-[:SUPPLY_TO]-(a:Company)
            RETURN elementId(a) AS source_company_id,
                   a.stockName AS source_company_name,
                   elementId(b) AS target_company_id,
                   b.stockName AS target_company_name,
                   b.stockCode AS stock_code,
                   'positive' AS direction
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})
        return [dict(r) for r in result]

    def _query_competition_transmission(
        self, event_id: str
    ) -> List[Dict[str, Any]]:
        """查询竞争传导：Event → CompanyA →[competesWith] → CompanyB"""
        query = """
            MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(a:Company)
                  -[:COMPETES_WITH]->(b:Company)
            RETURN elementId(a) AS source_company_id,
                   a.stockName AS source_company_name,
                   elementId(b) AS target_company_id,
                   b.stockName AS target_company_name,
                   b.stockCode AS stock_code,
                   'negative' AS direction
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})
        return [dict(r) for r in result]

    # ==================== 事件分类 ====================

    def classify_event(self, event_text: str) -> Dict[str, Any]:
        """
        基于本体约束自动分类事件类型

        通过关键词匹配判断事件属于 PolicyEvent、CompanyEvent 还是 MacroEvent。

        Args:
            event_text: 事件文本

        Returns:
            分类结果，包含 event_type 和 confidence
        """
        # 政策事件关键词
        policy_keywords = [
            "央行", "国务院", "证监会", "银保监", "发改委", "财政部",
            "降准", "降息", "加息", "存准", "MLF", "LPR",
            "政策", "法规", "条例", "意见", "通知", "办法",
            "注册制", "退市", "监管", "整治", "规范",
        ]

        # 宏观事件关键词
        macro_keywords = [
            "GDP", "CPI", "PPI", "PMI", "M2",
            "通胀", "通缩", "利率", "汇率", "美联储",
            "贸易战", "关税", "制裁", "地缘",
            "疫情", "地震", "洪水", "自然灾害",
            "就业", "失业率", "消费", "出口", "进口",
        ]

        # 公司事件关键词
        company_keywords = [
            "财报", "季报", "年报", "业绩", "营收", "净利润",
            "并购", "重组", "收购", "增发", "回购",
            "高管", "董事长", "CEO", "辞职", "任命",
            "股权", "减持", "增持", "质押",
            "产品", "技术", "专利", "订单",
        ]

        text_lower = event_text.lower()

        policy_score = sum(1 for kw in policy_keywords if kw in text_lower)
        macro_score = sum(1 for kw in macro_keywords if kw.lower() in text_lower)
        company_score = sum(1 for kw in company_keywords if kw in text_lower)

        total = policy_score + macro_score + company_score
        if total == 0:
            return {
                "event_type": "Unknown",
                "confidence": 0.0,
                "scores": {},
            }

        scores = {
            "PolicyEvent": policy_score / total,
            "MacroEvent": macro_score / total,
            "CompanyEvent": company_score / total,
        }

        best_type = max(scores, key=scores.get)
        return {
            "event_type": best_type,
            "confidence": round(scores[best_type], 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
        }

    # ==================== 数据一致性校验 ====================

    def validate_with_ontology(
        self, entity_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于 OWL 公理约束校验数据一致性

        Args:
            entity_type: 实体类型（Company, MarketEvent, FinancialReport 等）
            data: 实体数据

        Returns:
            校验结果，包含 is_valid 和 violations 列表
        """
        violations = []

        if entity_type == "Company":
            # 公理：Company 必须属于至少一个 Industry
            if not data.get("industry") and not data.get("industry_code"):
                violations.append({
                    "constraint": "belongsToIndustry (someValuesFrom)",
                    "message": "公司必须属于至少一个行业",
                    "severity": "error",
                })

            # 公理：Company 必须有股票代码
            if not data.get("stockCode"):
                violations.append({
                    "constraint": "hasStockCode",
                    "message": "公司必须有股票代码",
                    "severity": "error",
                })

        elif entity_type == "MarketEvent":
            # 公理：MarketEvent 必须有事件日期
            if not data.get("eventDate"):
                violations.append({
                    "constraint": "hasEventDate (someValuesFrom)",
                    "message": "市场事件必须有事件日期",
                    "severity": "error",
                })

            # 公理：影响级别必须是 High/Medium/Low
            impact_level = data.get("impactLevel")
            if impact_level and impact_level not in ("High", "Medium", "Low"):
                violations.append({
                    "constraint": "hasImpactLevel (enumeration)",
                    "message": f"影响级别必须是 High/Medium/Low，当前值: {impact_level}",
                    "severity": "warning",
                })

        elif entity_type == "FinancialReport":
            # 公理：FinancialReport 必须有报告日期
            if not data.get("reportDate"):
                violations.append({
                    "constraint": "hasReportDate (someValuesFrom)",
                    "message": "财务报告必须有报告日期",
                    "severity": "error",
                })

            # 数据合理性：ROE 不能超过 100%
            roe = data.get("roe")
            if roe is not None and abs(roe) > 1.0:
                violations.append({
                    "constraint": "hasROE (range check)",
                    "message": f"ROE 值异常: {roe}，通常应在 -1 到 1 之间",
                    "severity": "warning",
                })

        is_valid = not any(v["severity"] == "error" for v in violations)
        return {
            "is_valid": is_valid,
            "entity_type": entity_type,
            "violations": violations,
        }

    # ==================== 累积影响分数 ====================

    def get_accumulated_impact(
        self,
        stock_code: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        计算某股票在时间窗口内的累积事件影响分数

        Args:
            stock_code: 股票代码
            days: 时间窗口（天）

        Returns:
            累积影响信息，包含 score、events、breakdown
        """
        query = """
            MATCH (e:MarketEvent)-[r:IMPACTS]->(c:Company {stockCode: $stock_code})
            WHERE e.eventDate >= date() - duration({days: $days})
            RETURN e.eventId AS event_id,
                   e.title AS title,
                   e.eventType AS event_type,
                   e.impactLevel AS impact_level,
                   e.eventDate AS event_date,
                   r.impactDirection AS direction
            ORDER BY e.eventDate DESC
        """
        result = self.neo4j.execute_query(
            query, {"stock_code": stock_code, "days": days}
        )

        events = []
        total_score = 0.0
        breakdown = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        for record in result:
            event = dict(record)
            impact_level = event.get("impact_level", "Low")
            direction = event.get("direction", "neutral")

            # 计算单事件分数
            base_score = self.IMPACT_LEVEL_SCORES.get(impact_level, 0.3)
            if direction == "negative":
                score = -base_score
            elif direction == "positive":
                score = base_score
            else:
                score = 0.0

            event["impact_score"] = round(score, 2)
            events.append(event)

            total_score += score
            breakdown[direction] = round(breakdown.get(direction, 0) + score, 2)

        return {
            "stock_code": stock_code,
            "period_days": days,
            "accumulated_score": round(total_score, 2),
            "event_count": len(events),
            "breakdown": breakdown,
            "events": events,
        }

    # ==================== 工具方法 ====================

    def _decay_confidence(self, base_confidence: float, depth: int) -> float:
        """计算衰减后的置信度"""
        return round(
            base_confidence * (self.DEFAULT_CONFIDENCE_DECAY ** depth), 4
        )

    def get_all_chains_for_stock(
        self,
        stock_code: str,
        days: int = 30,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        查询影响某股票的所有因果链（从图谱中读取已记录的链）

        Args:
            stock_code: 股票代码
            days: 时间窗口
            limit: 返回数量

        Returns:
            因果链列表
        """
        query = """
            MATCH (cc:CausalChain)-[:HAS_STEP]->(rs:ReasoningStep)
                  -[:TO_NODE]->(c:Company {stockCode: $stock_code})
            WHERE cc.timestamp >= datetime() - duration({days: $days})
            RETURN cc, collect(rs) AS steps
            ORDER BY cc.timestamp DESC
            LIMIT $limit
        """
        try:
            result = self.neo4j.execute_query(
                query, {"stock_code": stock_code, "days": days, "limit": limit}
            )
            chains = []
            for record in result:
                chain_data = dict(record["cc"])
                chain_data["steps"] = [dict(s) for s in record["steps"]]
                chains.append(chain_data)
            return chains
        except Exception as e:
            logger.warning(f"Failed to query causal chains: {e}")
            return []

    def predict_with_ontology_rules(
        self,
        stock_code: str,
        prediction: str,
    ) -> Dict[str, Any]:
        """
        基于本体规则校验预测结果的合理性

        Args:
            stock_code: 股票代码
            prediction: 预测方向（up/down/neutral）

        Returns:
            校验结果，包含是否合理和矛盾点
        """
        contradictions = []

        # 获取累积影响
        impact = self.get_accumulated_impact(stock_code, days=30)
        accumulated_score = impact.get("accumulated_score", 0)

        # 矛盾检测
        if prediction == "up" and accumulated_score < -0.5:
            contradictions.append({
                "type": "event_contradiction",
                "message": (
                    f"预测看涨，但近30天累积事件影响为负 ({accumulated_score})，"
                    f"共 {impact.get('event_count', 0)} 个负面事件"
                ),
                "severity": "warning",
            })

        if prediction == "down" and accumulated_score > 0.5:
            contradictions.append({
                "type": "event_contradiction",
                "message": (
                    f"预测看跌，但近30天累积事件影响为正 ({accumulated_score})，"
                    f"共 {impact.get('event_count', 0)} 个正面事件"
                ),
                "severity": "warning",
            })

        # 检查是否有 High 级别事件
        high_impact_events = [
            e for e in impact.get("events", [])
            if e.get("impact_level") == "High"
        ]
        if high_impact_events:
            contradictions.append({
                "type": "high_impact_alert",
                "message": (
                    f"存在 {len(high_impact_events)} 个高影响事件，"
                    f"预测需谨慎: {[e.get('title', '') for e in high_impact_events[:3]]}"
                ),
                "severity": "info",
            })

        is_consistent = not any(c["severity"] == "warning" for c in contradictions)
        return {
            "stock_code": stock_code,
            "prediction": prediction,
            "is_consistent": is_consistent,
            "accumulated_impact_score": accumulated_score,
            "contradictions": contradictions,
        }
