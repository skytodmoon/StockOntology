"""
图谱统计服务

提供知识图谱的统计分析功能。
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.core.database import get_neo4j_client


class GraphStatistics:
    """图谱统计服务"""

    def __init__(self):
        """初始化图谱统计服务"""
        self._neo4j = None

    @property
    def neo4j(self):
        """获取 Neo4j 客户端"""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    def get_overview(self) -> Dict[str, Any]:
        """
        获取图谱概览

        Returns:
            概览信息
        """
        stats = self.neo4j.get_database_stats()
        return {
            "node_counts": stats.get("node_counts", {}),
            "relationship_counts": stats.get("relationship_counts", {}),
            "total_nodes": sum(stats.get("node_counts", {}).values()),
            "total_relationships": sum(stats.get("relationship_counts", {}).values()),
        }

    def get_company_statistics(self) -> Dict[str, Any]:
        """
        获取公司统计信息

        Returns:
            统计信息
        """
        query = """
            MATCH (c:Company)
            RETURN
                count(c) as total_count,
                avg(c.marketCap) as avg_market_cap,
                min(c.marketCap) as min_market_cap,
                max(c.marketCap) as max_market_cap,
                count(CASE WHEN c.market = 'SH' THEN 1 END) as sh_count,
                count(CASE WHEN c.market = 'SZ' THEN 1 END) as sz_count,
                count(CASE WHEN c.market = 'BJ' THEN 1 END) as bj_count
        """
        result = self.neo4j.execute_query(query)
        if result:
            return dict(result[0])
        return {}

    def get_industry_statistics(self) -> List[Dict[str, Any]]:
        """
        获取行业统计信息

        Returns:
            行业统计列表
        """
        query = """
            MATCH (i:Industry)<-[:BELONGS_TO]-(c:Company)
            RETURN
                i.code as industry_code,
                i.name as industry_name,
                count(c) as company_count,
                sum(c.marketCap) as total_market_cap,
                avg(c.marketCap) as avg_market_cap
            ORDER BY total_market_cap DESC
        """
        result = self.neo4j.execute_query(query)
        return [dict(r) for r in result]

    def get_investor_statistics(self) -> Dict[str, Any]:
        """
        获取投资者统计信息

        Returns:
            统计信息
        """
        query = """
            MATCH (inv:Investor)
            RETURN
                count(inv) as total_count,
                count(CASE WHEN inv.investorType = 'Fund' THEN 1 END) as fund_count,
                count(CASE WHEN inv.investorType = 'QFII' THEN 1 END) as qfii_count,
                count(CASE WHEN inv.investorType = 'SocialSecurity' THEN 1 END) as social_security_count,
                count(CASE WHEN inv.investorType = 'Insurance' THEN 1 END) as insurance_count
        """
        result = self.neo4j.execute_query(query)
        if result:
            return dict(result[0])
        return {}

    def get_event_statistics(self) -> Dict[str, Any]:
        """
        获取事件统计信息

        Returns:
            统计信息
        """
        query = """
            MATCH (e:MarketEvent)
            RETURN
                count(e) as total_count,
                count(CASE WHEN e.eventType = 'PolicyEvent' THEN 1 END) as policy_count,
                count(CASE WHEN e.eventType = 'CompanyEvent' THEN 1 END) as company_count,
                count(CASE WHEN e.eventType = 'MacroEvent' THEN 1 END) as macro_count,
                count(CASE WHEN e.impactLevel = 'High' THEN 1 END) as high_impact_count,
                count(CASE WHEN e.impactLevel = 'Medium' THEN 1 END) as medium_impact_count,
                count(CASE WHEN e.impactLevel = 'Low' THEN 1 END) as low_impact_count
        """
        result = self.neo4j.execute_query(query)
        if result:
            return dict(result[0])
        return {}

    def get_relationship_statistics(self) -> List[Dict[str, Any]]:
        """
        获取关系统计信息

        Returns:
            关系统计列表
        """
        query = """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
        """
        result = self.neo4j.execute_query(query)
        return [dict(r) for r in result]

    def get_top_companies(
        self,
        metric: str = "marketCap",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取顶级公司

        Args:
            metric: 排序指标
            limit: 返回数量

        Returns:
            公司列表
        """
        query = f"""
            MATCH (c:Company)
            RETURN c
            ORDER BY c.{metric} DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"limit": limit})
        return [dict(r["c"]) for r in result]

    def get_top_investors(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取顶级投资者

        Args:
            limit: 返回数量

        Returns:
            投资者列表
        """
        query = """
            MATCH (inv:Investor)-[h:HOLDS]->(c:Company)
            WITH inv, sum(h.marketValue) as total_value
            RETURN inv, total_value
            ORDER BY total_value DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"limit": limit})
        investors = []
        for r in result:
            investor = dict(r["inv"])
            investor["total_value"] = r["total_value"]
            investors.append(investor)
        return investors

    def get_recent_events(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取最近事件

        Args:
            days: 天数
            limit: 返回数量

        Returns:
            事件列表
        """
        query = """
            MATCH (e:MarketEvent)
            WHERE e.eventDate >= date() - duration({days: $days})
            RETURN e
            ORDER BY e.eventDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"days": days, "limit": limit})
        return [dict(r["e"]) for r in result]

    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览

        Returns:
            市场概览信息
        """
        # 公司统计
        company_stats = self.get_company_statistics()

        # 行业统计
        industry_stats = self.get_industry_statistics()

        # 投资者统计
        investor_stats = self.get_investor_statistics()

        # 事件统计
        event_stats = self.get_event_statistics()

        return {
            "companies": company_stats,
            "industries": {
                "count": len(industry_stats),
                "top_5": industry_stats[:5] if industry_stats else [],
            },
            "investors": investor_stats,
            "events": event_stats,
        }
