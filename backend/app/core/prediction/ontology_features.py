"""
本体特征提取器

从知识图谱和本体推理结果中提取预测特征，用于增强 AI 预测模型。
这些特征是本体系统的独特价值——传统量化模型无法获取的结构化知识。

特征类别：
1. 行业层级特征：公司在行业层级中的位置
2. 事件影响特征：时间窗口内的累积事件影响
3. 供应链风险特征：上下游公司的健康度
4. 竞争压力特征：同行业竞对的对比
5. 机构情绪特征：机构持仓变化趋势
6. 图谱中心性特征：公司在知识图谱中的重要性
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.core.database import get_neo4j_client
from app.core.reasoning import OntologyReasoner


class OntologyFeatureExtractor:
    """
    本体特征提取器

    从 Neo4j 知识图谱中提取结构化特征，用于增强预测模型。
    这些特征体现了本体在预测中的独特价值。
    """

    def __init__(self):
        """初始化特征提取器"""
        self._neo4j = None
        self._reasoner = None

    @property
    def neo4j(self):
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    @property
    def reasoner(self):
        if self._reasoner is None:
            self._reasoner = OntologyReasoner()
        return self._reasoner

    def extract_all(self, stock_code: str, days: int = 30) -> Dict[str, Any]:
        """
        提取所有本体特征

        Args:
            stock_code: 股票代码
            days: 事件影响的时间窗口

        Returns:
            所有本体特征的字典
        """
        features = {
            "stock_code": stock_code,
            "industry_level": self.extract_industry_level(stock_code),
            "event_impact": self.extract_event_impact_score(stock_code, days),
            "supply_chain_risk": self.extract_supply_chain_risk(stock_code),
            "competition_pressure": self.extract_competition_pressure(stock_code),
            "institutional_sentiment": self.extract_institutional_sentiment(stock_code),
            "graph_centrality": self.extract_graph_centrality(stock_code),
            "industry_momentum": self.extract_industry_momentum(stock_code),
        }
        return features

    def extract_industry_level(self, stock_code: str) -> Dict[str, Any]:
        """
        提取行业层级特征

        公司在行业层级中的位置：
        - level 1: 一级行业（如"消费"）
        - level 2: 二级行业（如"食品饮料"）
        - level 3: 三级行业（如"白酒"）

        行业龙头（市值最大）标记为 is_leader=True
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:BELONGS_TO]->(i:Industry)
            OPTIONAL MATCH (i)-[:SUB_INDUSTRY_OF*]->(parent:Industry)
            WITH c, i, parent
            RETURN i.name AS industry_name,
                   i.code AS industry_code,
                   i.level AS industry_level,
                   collect(parent.name) AS parent_industries,
                   c.marketCap AS market_cap
        """
        try:
            result = self.neo4j.execute_query(query, {"stockCode": stock_code})
            if not result:
                return {"level": 0, "is_leader": False, "industry_name": ""}

            record = dict(result[0])
            industry_name = record.get("industry_name", "")
            level = record.get("industry_level", 1)

            # 检查是否是行业内龙头（市值最大）
            leader_query = """
                MATCH (c:Company)-[:BELONGS_TO]->(i:Industry {name: $industry})
                RETURN c.stockCode AS code, c.marketCap AS cap
                ORDER BY c.marketCap DESC
                LIMIT 1
            """
            leader_result = self.neo4j.execute_query(
                leader_query, {"industry": industry_name}
            )
            is_leader = False
            if leader_result:
                is_leader = dict(leader_result[0]).get("code") == stock_code

            return {
                "level": level,
                "is_leader": is_leader,
                "industry_name": industry_name,
                "parent_industries": record.get("parent_industries", []),
            }
        except Exception as e:
            logger.warning(f"Failed to extract industry level: {e}")
            return {"level": 0, "is_leader": False, "industry_name": ""}

    def extract_event_impact_score(
        self, stock_code: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        提取事件影响特征

        计算时间窗口内所有事件对公司的累积影响分数。
        正面事件加分，负面事件减分。
        """
        try:
            impact = self.reasoner.get_accumulated_impact(stock_code, days)
            return {
                "accumulated_score": impact.get("accumulated_score", 0),
                "event_count": impact.get("event_count", 0),
                "positive_score": impact.get("breakdown", {}).get("positive", 0),
                "negative_score": impact.get("breakdown", {}).get("negative", 0),
                "high_impact_count": len([
                    e for e in impact.get("events", [])
                    if e.get("impact_level") == "High"
                ]),
            }
        except Exception as e:
            logger.warning(f"Failed to extract event impact: {e}")
            return {"accumulated_score": 0, "event_count": 0}

    def extract_supply_chain_risk(self, stock_code: str) -> Dict[str, Any]:
        """
        提取供应链风险特征

        分析上下游公司的健康度：
        - 上游供应商数量和集中度
        - 下游客户数量和集中度
        - 供应链中是否有高风险公司
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            OPTIONAL MATCH (supplier:Company)-[:SUPPLY_TO]->(c)
            OPTIONAL MATCH (c)-[:SUPPLY_TO]->(customer:Company)
            RETURN
                collect(DISTINCT supplier.stockCode) AS suppliers,
                collect(DISTINCT customer.stockCode) AS customers,
                count(DISTINCT supplier) AS supplier_count,
                count(DISTINCT customer) AS customer_count
        """
        try:
            result = self.neo4j.execute_query(query, {"stockCode": stock_code})
            if not result:
                return {"supplier_count": 0, "customer_count": 0, "risk_score": 0}

            record = dict(result[0])
            supplier_count = record.get("supplier_count", 0)
            customer_count = record.get("customer_count", 0)

            # 集中度风险：供应商/客户越少，集中度越高，风险越大
            concentration_risk = 0
            if supplier_count > 0:
                concentration_risk += 1.0 / supplier_count
            if customer_count > 0:
                concentration_risk += 1.0 / customer_count

            return {
                "supplier_count": supplier_count,
                "customer_count": customer_count,
                "suppliers": record.get("suppliers", []),
                "customers": record.get("customers", []),
                "concentration_risk": round(concentration_risk, 4),
                "risk_score": round(min(1.0, concentration_risk), 4),
            }
        except Exception as e:
            logger.warning(f"Failed to extract supply chain risk: {e}")
            return {"supplier_count": 0, "customer_count": 0, "risk_score": 0}

    def extract_competition_pressure(self, stock_code: str) -> Dict[str, Any]:
        """
        提取竞争压力特征

        分析同行业竞争对手的情况：
        - 竞争对手数量
        - 自身市值排名
        - 竞争压力指数
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:BELONGS_TO]->(i:Industry)
                  <-[:BELONGS_TO]-(competitor:Company)
            WHERE competitor <> c
            RETURN
                collect({
                    code: competitor.stockCode,
                    name: competitor.stockName,
                    cap: competitor.marketCap
                }) AS competitors,
                c.marketCap AS my_cap
            ORDER BY competitor.marketCap DESC
        """
        try:
            result = self.neo4j.execute_query(query, {"stockCode": stock_code})
            if not result:
                return {"competitor_count": 0, "rank": 0, "pressure_score": 0}

            record = dict(result[0])
            competitors = record.get("competitors", [])
            my_cap = record.get("my_cap", 0) or 0
            competitor_count = len(competitors)

            # 计算市值排名
            rank = 1
            for comp in competitors:
                comp_cap = comp.get("cap", 0) or 0
                if comp_cap > my_cap:
                    rank += 1

            # 竞争压力指数：竞争对手越多、排名越靠后，压力越大
            pressure_score = 0
            if competitor_count > 0:
                pressure_score = rank / (competitor_count + 1)

            return {
                "competitor_count": competitor_count,
                "rank": rank,
                "total_in_industry": competitor_count + 1,
                "pressure_score": round(pressure_score, 4),
                "top_competitors": [
                    {"code": c.get("code"), "name": c.get("name")}
                    for c in competitors[:5]
                ],
            }
        except Exception as e:
            logger.warning(f"Failed to extract competition pressure: {e}")
            return {"competitor_count": 0, "rank": 0, "pressure_score": 0}

    def extract_institutional_sentiment(self, stock_code: str) -> Dict[str, Any]:
        """
        提取机构情绪特征

        分析机构投资者的持仓情况：
        - 机构投资者数量
        - 机构持仓比例
        - 是否有知名机构
        """
        query = """
            MATCH (inv:Investor)-[h:HOLDS]->(c:Company {stockCode: $stockCode})
            RETURN
                collect({
                    name: inv.name,
                    type: inv.type,
                    shares: h.shares,
                    ratio: h.ratio
                }) AS investors,
                count(inv) AS investor_count,
                sum(h.ratio) AS total_ratio
        """
        try:
            result = self.neo4j.execute_query(query, {"stockCode": stock_code})
            if not result:
                return {"investor_count": 0, "total_ratio": 0, "sentiment": "neutral"}

            record = dict(result[0])
            investor_count = record.get("investor_count", 0)
            total_ratio = record.get("total_ratio", 0) or 0
            investors = record.get("investors", [])

            # 机构持仓比例越高，通常表示机构看好
            sentiment = "neutral"
            if total_ratio > 0.3:
                sentiment = "positive"
            elif total_ratio < 0.05 and investor_count > 0:
                sentiment = "negative"

            return {
                "investor_count": investor_count,
                "total_ratio": round(float(total_ratio), 4),
                "sentiment": sentiment,
                "top_investors": investors[:5],
            }
        except Exception as e:
            logger.warning(f"Failed to extract institutional sentiment: {e}")
            return {"investor_count": 0, "total_ratio": 0, "sentiment": "neutral"}

    def extract_graph_centrality(self, stock_code: str) -> Dict[str, Any]:
        """
        提取图谱中心性特征

        计算公司在知识图谱中的重要性：
        - 度中心性：直接关系数量
        - 关系类型多样性
        - 间接关系覆盖范围
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            OPTIONAL MATCH (c)-[r]-()
            WITH c, count(r) AS degree
            OPTIONAL MATCH (c)-[r]-()
            WITH c, degree, type(r) AS rel_type
            RETURN degree, collect(DISTINCT rel_type) AS relation_types
        """
        try:
            result = self.neo4j.execute_query(query, {"stockCode": stock_code})
            if not result:
                return {"degree": 0, "relation_types": [], "centrality_score": 0}

            record = dict(result[0])
            degree = record.get("degree", 0)
            relation_types = record.get("relation_types", [])

            # 中心性分数：关系数量 * 关系类型多样性
            centrality_score = degree * len(relation_types) if relation_types else 0

            return {
                "degree": degree,
                "relation_types": relation_types,
                "relation_type_count": len(relation_types),
                "centrality_score": centrality_score,
            }
        except Exception as e:
            logger.warning(f"Failed to extract graph centrality: {e}")
            return {"degree": 0, "relation_types": [], "centrality_score": 0}

    def extract_industry_momentum(self, stock_code: str) -> Dict[str, Any]:
        """
        提取行业动量特征

        分析公司所在行业的整体动量：
        - 行业内公司数量
        - 行业平均市值
        - 行业近期事件数量
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:BELONGS_TO]->(i:Industry)
            OPTIONAL MATCH (i)<-[:BELONGS_TO]-(peer:Company)
            OPTIONAL MATCH (e:MarketEvent)-[:IMPACTS]->(i)
            WHERE e.eventDate >= date() - duration({days: 30})
            RETURN
                i.name AS industry_name,
                count(DISTINCT peer) AS peer_count,
                avg(peer.marketCap) AS avg_market_cap,
                count(DISTINCT e) AS recent_event_count
        """
        try:
            result = self.neo4j.execute_query(query, {"stockCode": stock_code})
            if not result:
                return {"peer_count": 0, "avg_market_cap": 0, "recent_event_count": 0}

            record = dict(result[0])
            return {
                "industry_name": record.get("industry_name", ""),
                "peer_count": record.get("peer_count", 0),
                "avg_market_cap": record.get("avg_market_cap", 0),
                "recent_event_count": record.get("recent_event_count", 0),
            }
        except Exception as e:
            logger.warning(f"Failed to extract industry momentum: {e}")
            return {"peer_count": 0, "avg_market_cap": 0, "recent_event_count": 0}

    def to_flat_dict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        将嵌套特征字典展平为单层浮点数字典（用于模型输入）

        Args:
            features: extract_all() 返回的嵌套特征

        Returns:
            展平的浮点数特征字典
        """
        flat = {}

        # 行业层级
        il = features.get("industry_level", {})
        flat["industry_level"] = float(il.get("level", 0))
        flat["is_industry_leader"] = 1.0 if il.get("is_leader") else 0.0

        # 事件影响
        ei = features.get("event_impact", {})
        flat["event_impact_score"] = float(ei.get("accumulated_score", 0))
        flat["event_count"] = float(ei.get("event_count", 0))
        flat["high_impact_count"] = float(ei.get("high_impact_count", 0))

        # 供应链风险
        sc = features.get("supply_chain_risk", {})
        flat["supplier_count"] = float(sc.get("supplier_count", 0))
        flat["customer_count"] = float(sc.get("customer_count", 0))
        flat["supply_chain_risk"] = float(sc.get("risk_score", 0))

        # 竞争压力
        cp = features.get("competition_pressure", {})
        flat["competitor_count"] = float(cp.get("competitor_count", 0))
        flat["industry_rank"] = float(cp.get("rank", 0))
        flat["competition_pressure"] = float(cp.get("pressure_score", 0))

        # 机构情绪
        inst = features.get("institutional_sentiment", {})
        flat["institutional_count"] = float(inst.get("investor_count", 0))
        flat["institutional_ratio"] = float(inst.get("total_ratio", 0))
        sentiment_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        flat["institutional_sentiment"] = sentiment_map.get(inst.get("sentiment", "neutral"), 0.0)

        # 图谱中心性
        gc = features.get("graph_centrality", {})
        flat["graph_degree"] = float(gc.get("degree", 0))
        flat["relation_type_count"] = float(gc.get("relation_type_count", 0))
        flat["centrality_score"] = float(gc.get("centrality_score", 0))

        # 行业动量
        im = features.get("industry_momentum", {})
        flat["industry_peer_count"] = float(im.get("peer_count", 0))
        flat["industry_recent_events"] = float(im.get("recent_event_count", 0))

        return flat
