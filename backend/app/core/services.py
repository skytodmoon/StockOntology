"""
业务服务层模块

提供各数据库的业务逻辑封装，实现多数据库协作。
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime
from loguru import logger
from functools import lru_cache

from app.core.database import (
    get_neo4j_client,
    get_postgres_client,
    get_timescale_client,
    get_redis_client,
    get_chroma_client,
)


class CompanyService:
    """企业数据服务"""

    def __init__(self):
        self.neo4j = get_neo4j_client()
        self.postgres = get_postgres_client()
        self.timescale = get_timescale_client()
        self.redis = get_redis_client()

    def get_company_detail(self, stock_code: str) -> Dict[str, Any]:
        """
        获取企业完整信息（多数据库聚合）

        Args:
            stock_code: 股票代码

        Returns:
            企业完整信息字典
        """
        cache_key = f"company:{stock_code}:detail"
        cached = self.redis.get_json(cache_key)
        if cached:
            return cached

        # 1. 从 Neo4j 获取企业基本信息和关系
        neo4j_data = self._get_company_graph_data(stock_code)

        # 2. 从 TimescaleDB 获取最新行情（优雅处理表不存在的情况）
        try:
            recent_data = self.timescale.get_recent_data(stock_code, days=1)
        except Exception as e:
            logger.warning(f"Failed to get market data for {stock_code}: {e}")
            recent_data = []
        latest_price = recent_data[0] if recent_data else None

        # 3. 聚合数据
        result = {
            "stock_code": stock_code,
            **neo4j_data,
            "latest_price": latest_price,
        }

        # 缓存结果（5分钟）
        self.redis.set_json(cache_key, result, ex=300)

        return result

    def _get_company_graph_data(self, stock_code: str) -> Dict[str, Any]:
        """从 Neo4j 获取企业数据"""
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            OPTIONAL MATCH (c)-[:BELONGS_TO_CONCEPT]->(co:Concept)
            OPTIONAL MATCH (supplier:Company)-[:SUPPLIES]->(c)
            OPTIONAL MATCH (c)-[:SUPPLIES]->(customer:Company)
            RETURN 
                c {.*},
                collect(DISTINCT i {code: i.code, name: i.name}) as industries,
                collect(DISTINCT co {code: co.code, name: co.name}) as concepts,
                collect(DISTINCT supplier {stockCode: supplier.stockCode, stockName: supplier.stockName}) as suppliers,
                collect(DISTINCT customer {stockCode: customer.stockCode, stockName: customer.stockName}) as customers
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code})
        if result:
            data = result[0]
            company = data["c"]
            return {
                "stock_name": company.get("stockName"),
                "market": company.get("market"),
                "description": company.get("description"),
                "employees": company.get("employees"),
                "is_leader": company.get("isLeader"),
                "moat_level": company.get("moatLevel"),
                "moat_type": company.get("moatType"),
                "market_cap": company.get("marketCap"),
                "pe_ratio": company.get("peRatio"),
                "roe": company.get("roe"),
                "industries": data.get("industries", []),
                "concepts": data.get("concepts", []),
                "suppliers": data.get("suppliers", []),
                "customers": data.get("customers", []),
            }
        return {}

    def get_dragon_stocks(self, industry_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取龙头股列表

        Args:
            industry_code: 行业代码（可选）

        Returns:
            龙头股列表
        """
        query = """
            MATCH (c:Company {isLeader: true})
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            WHERE $industry_code IS NULL OR i.code = $industry_code
            RETURN 
                c.stockCode as stock_code,
                c.stockName as stock_name,
                i.name as industry,
                c.moatLevel as moat_level,
                c.moatType as moat_type,
                c.marketCap as market_cap,
                c.roe as roe
            ORDER BY c.marketCap DESC
        """
        result = self.neo4j.execute_query(query, {"industry_code": industry_code})
        return result

    def get_hightech_moat_companies(self, min_moat: int = 4) -> List[Dict[str, Any]]:
        """
        获取高护城河企业

        Args:
            min_moat: 最低护城河等级

        Returns:
            高护城河企业列表
        """
        query = """
            MATCH (c:Company)
            WHERE c.moatLevel >= $min_moat AND c.isLeader = true
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            RETURN 
                c.stockCode as stock_code,
                c.stockName as stock_name,
                i.name as industry,
                c.moatLevel as moat_level,
                c.moatType as moat_type,
                c.description as description
            ORDER BY c.moatLevel DESC, c.marketCap DESC
        """
        result = self.neo4j.execute_query(query, {"min_moat": min_moat})
        return result

    def get_supply_chain(self, stock_code: str, direction: str = "all") -> Dict[str, Any]:
        """
        获取供应链关系

        Args:
            stock_code: 股票代码
            direction: 方向（up/down/all）

        Returns:
            供应链数据
        """
        if direction == "up":
            query = """
                MATCH path = (supplier:Company)-[:SUPPLIES*1..2]->(c:Company {stockCode: $stockCode})
                WITH nodes(path) as ns, relationships(path) as rs
                UNWIND ns as n
                WITH collect(DISTINCT {data: n, labels: labels(n), id: elementId(n)}) as nodes, rs
                UNWIND rs as r
                WITH nodes, collect(DISTINCT {type: type(r), id: elementId(r), 
                    source: elementId(startNode(r)), target: elementId(endNode(r))}) as edges
                RETURN nodes, edges
            """
        elif direction == "down":
            query = """
                MATCH path = (c:Company {stockCode: $stockCode})-[:SUPPLIES*1..2]->(customer:Company)
                WITH nodes(path) as ns, relationships(path) as rs
                UNWIND ns as n
                WITH collect(DISTINCT {data: n, labels: labels(n), id: elementId(n)}) as nodes, rs
                UNWIND rs as r
                WITH nodes, collect(DISTINCT {type: type(r), id: elementId(r), 
                    source: elementId(startNode(r)), target: elementId(endNode(r))}) as edges
                RETURN nodes, edges
            """
        else:
            query = """
                MATCH path = (c:Company {stockCode: $stockCode})-[:SUPPLIES*1..2]-(related)
                WITH nodes(path) as ns, relationships(path) as rs
                UNWIND ns as n
                WITH collect(DISTINCT {data: n, labels: labels(n), id: elementId(n)}) as nodes, rs
                UNWIND rs as r
                WITH nodes, collect(DISTINCT {type: type(r), id: elementId(r), 
                    source: elementId(startNode(r)), target: elementId(endNode(r))}) as edges
                RETURN nodes, edges
            """

        result = self.neo4j.execute_query(query, {"stockCode": stock_code})
        return result[0] if result else {"nodes": [], "edges": []}


class MarketService:
    """行情数据服务"""

    def __init__(self):
        self.timescale = get_timescale_client()
        self.redis = get_redis_client()

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取股票日K线数据"""
        try:
            return self.timescale.get_daily_data(stock_code, start_date, end_date, limit)
        except Exception as e:
            logger.warning(f"Failed to get daily data for {stock_code}: {e}")
            return []

    def get_minute_data(
        self,
        stock_code: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取股票分钟K线数据"""
        try:
            return self.timescale.get_minute_data(stock_code, start_time, end_time, limit)
        except Exception as e:
            logger.warning(f"Failed to get minute data for {stock_code}: {e}")
            return []

    def get_index_data(
        self,
        index_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取大盘指数数据"""
        try:
            return self.timescale.get_index_data(index_code, start_date, end_date, limit)
        except Exception as e:
            logger.warning(f"Failed to get index data for {index_code}: {e}")
            return []

    def get_price_statistics(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """获取股票价格统计"""
        return self.timescale.get_price_statistics(stock_code, start_date, end_date)

    def get_moving_average(
        self,
        stock_code: str,
        window: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """获取移动平均线"""
        return self.timescale.get_moving_average(stock_code, window, start_date, end_date)

    def get_recent_data(self, stock_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取最近N天数据"""
        cache_key = f"market:{stock_code}:recent:{days}"
        cached = self.redis.get_json(cache_key)
        if cached:
            return cached

        data = self.timescale.get_recent_data(stock_code, days)
        self.redis.set_json(cache_key, data, ex=600)  # 10分钟缓存
        return data

    def batch_get_recent_data(
        self,
        stock_codes: List[str],
        days: int = 30,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """批量获取多只股票最近N天数据"""
        return self.timescale.batch_get_recent_data(stock_codes, days)


class ConceptService:
    """概念板块服务"""

    def __init__(self):
        self.neo4j = get_neo4j_client()
        self.redis = get_redis_client()

    def get_all_concepts(self) -> List[Dict[str, Any]]:
        """获取所有概念板块"""
        query = """
            MATCH (co:Concept)
            RETURN co.code as code, co.name as name, co.hotLevel as hot_level, co.description as description
            ORDER BY co.hotLevel DESC
        """
        result = self.neo4j.execute_query(query)
        return result

    def get_concept_stocks(self, concept_code: str) -> List[Dict[str, Any]]:
        """获取概念成分股"""
        query = """
            MATCH (c:Company)-[:BELONGS_TO_CONCEPT]->(co:Concept {code: $concept_code})
            RETURN 
                c.stockCode as stock_code,
                c.stockName as stock_name,
                co.name as concept,
                c.isLeader as is_leader,
                c.marketCap as market_cap
            ORDER BY c.isLeader DESC, c.marketCap DESC
        """
        result = self.neo4j.execute_query(query, {"concept_code": concept_code})
        return result

    def get_related_concepts(self, stock_code: str) -> List[Dict[str, Any]]:
        """获取股票所属概念"""
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:BELONGS_TO_CONCEPT]->(co:Concept)
            RETURN co.code as code, co.name as name, co.hotLevel as hot_level
            ORDER BY co.hotLevel DESC
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code})
        return result


class EventService:
    """市场事件服务"""

    def __init__(self):
        self.neo4j = get_neo4j_client()

    def get_all_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取所有市场事件"""
        query = """
            MATCH (e:MarketEvent)
            RETURN e.eventId as event_id, e.title as title, e.eventType as event_type,
                   e.eventDate as event_date, e.impactLevel as impact_level, e.description as description
            ORDER BY e.eventDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"limit": limit})
        return result

    def get_event_impacts(self, event_id: str) -> List[Dict[str, Any]]:
        """获取事件影响的股票"""
        query = """
            MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(c:Company)
            RETURN c.stockCode as stock_code, c.stockName as stock_name
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})
        return result

    def get_stock_events(self, stock_code: str) -> List[Dict[str, Any]]:
        """获取影响股票的事件"""
        query = """
            MATCH (e:MarketEvent)-[:IMPACTS]->(c:Company {stockCode: $stock_code})
            RETURN e.eventId as event_id, e.title as title, e.eventType as event_type,
                   e.eventDate as event_date, e.impactLevel as impact_level
            ORDER BY e.eventDate DESC
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code})
        return result


class GraphService:
    """图谱服务"""

    def __init__(self):
        self.neo4j = get_neo4j_client()

    def get_company_graph(self, stock_code: str, depth: int = 2) -> Dict[str, Any]:
        """获取企业关联图谱"""
        query = f"""
            MATCH path = (c:Company {{stockCode: $stockCode}})-[*1..{depth}]-(related)
            WITH nodes(path) as ns, relationships(path) as rs
            UNWIND ns as n
            WITH collect(DISTINCT {{data: n, labels: labels(n), id: elementId(n)}}) as nodes, rs
            UNWIND rs as r
            WITH nodes, collect(DISTINCT {{type: type(r), id: elementId(r), 
                source: elementId(startNode(r)), target: elementId(endNode(r))}}) as edges
            RETURN nodes, edges
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code})
        return result[0] if result else {"nodes": [], "edges": []}

    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行自定义Cypher查询"""
        return self.neo4j.execute_query(query, parameters or {})

    def get_industry_hierarchy(self) -> List[Dict[str, Any]]:
        """获取行业层级关系"""
        query = """
            MATCH (child:Industry)-[:BELONGS_TO]->(parent:Industry)
            RETURN parent.name as parent, collect(child.name) as children
            ORDER BY parent.name
        """
        result = self.neo4j.execute_query(query)
        return result


class CacheService:
    """缓存服务"""

    def __init__(self):
        self.redis = get_redis_client()

    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        return self.redis.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """设置缓存值"""
        return self.redis.set(key, value, ex=ex)

    def get_json(self, key: str) -> Optional[Any]:
        """获取JSON缓存"""
        return self.redis.get_json(key)

    def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置JSON缓存"""
        return self.redis.set_json(key, value, ex=ex)

    def delete(self, key: str) -> int:
        """删除缓存"""
        return self.redis.delete(key)

    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        return self.redis.clear_pattern(pattern)

    def publish(self, channel: str, message: str) -> int:
        """发布消息到频道"""
        return self.redis.publish(channel, message)


# 全局服务实例
_company_service = None
_market_service = None
_concept_service = None
_event_service = None
_graph_service = None
_cache_service = None


def get_company_service() -> CompanyService:
    """获取企业服务实例"""
    global _company_service
    if _company_service is None:
        _company_service = CompanyService()
    return _company_service


def get_market_service() -> MarketService:
    """获取行情服务实例"""
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service


def get_concept_service() -> ConceptService:
    """获取概念服务实例"""
    global _concept_service
    if _concept_service is None:
        _concept_service = ConceptService()
    return _concept_service


def get_event_service() -> EventService:
    """获取事件服务实例"""
    global _event_service
    if _event_service is None:
        _event_service = EventService()
    return _event_service


def get_graph_service() -> GraphService:
    """获取图谱服务实例"""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service


def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


__all__ = [
    "CompanyService",
    "get_company_service",
    "MarketService",
    "get_market_service",
    "ConceptService",
    "get_concept_service",
    "EventService",
    "get_event_service",
    "GraphService",
    "get_graph_service",
    "CacheService",
    "get_cache_service",
]