"""
事件数据仓库

提供市场事件数据的访问方法。
"""

from typing import Any, Dict, List, Optional
from datetime import date
from loguru import logger

from .base_repository import BaseRepository
from app.models.event import (
    MarketEvent,
    MarketEventCreate,
    EventType,
    ImpactLevel,
    event_to_neo4j,
    neo4j_to_event,
)


class EventRepository(BaseRepository[MarketEvent]):
    """事件数据仓库"""

    def __init__(self):
        super().__init__("MarketEvent")

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        order_desc: bool = False,
    ) -> List[MarketEvent]:
        """
        查找所有事件并转换为 MarketEvent 模型
        """
        results = super().find_all(skip=skip, limit=limit, order_by=order_by, order_desc=order_desc)
        return [neo4j_to_event(r) for r in results]

    def find_by_event_id(self, event_id: str) -> Optional[MarketEvent]:
        """
        根据事件ID查找事件

        Args:
            event_id: 事件ID

        Returns:
            事件模型
        """
        result = self.find_one_by_property("eventId", event_id)
        if result:
            return neo4j_to_event(result)
        return None

    def find_by_type(
        self,
        event_type: EventType,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketEvent]:
        """
        根据类型查找事件

        Args:
            event_type: 事件类型
            skip: 跳过数量
            limit: 返回数量

        Returns:
            事件列表
        """
        results = self.find_by_property("eventType", event_type.value)
        return [neo4j_to_event(r) for r in results[skip:skip + limit]]

    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        event_type: EventType = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketEvent]:
        """
        根据日期范围查找事件

        Args:
            start_date: 开始日期
            end_date: 结束日期
            event_type: 事件类型
            skip: 跳过数量
            limit: 返回数量

        Returns:
            事件列表
        """
        where_clauses = [
            "e.eventDate >= $start_date",
            "e.eventDate <= $end_date",
        ]
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "skip": skip,
            "limit": limit,
        }

        if event_type:
            where_clauses.append("e.eventType = $event_type")
            params["event_type"] = event_type.value

        where_clause = " AND ".join(where_clauses)

        query = f"""
            MATCH (e:{self.node_label})
            WHERE {where_clause}
            RETURN e
            ORDER BY e.eventDate DESC
            SKIP $skip
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, params)
        return [neo4j_to_event(r["e"]) for r in result]

    def find_by_impact_level(
        self,
        impact_level: ImpactLevel,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketEvent]:
        """
        根据影响级别查找事件

        Args:
            impact_level: 影响级别
            skip: 跳过数量
            limit: 返回数量

        Returns:
            事件列表
        """
        results = self.find_by_property("impactLevel", impact_level.value)
        return [neo4j_to_event(r) for r in results[skip:skip + limit]]

    def find_recent_events(
        self,
        days: int = 7,
        event_type: EventType = None,
        limit: int = 50,
    ) -> List[MarketEvent]:
        """
        查找最近的事件

        Args:
            days: 天数
            event_type: 事件类型
            limit: 返回数量

        Returns:
            事件列表
        """
        where_clauses = ["e.eventDate >= date() - duration({days: $days})"]
        params = {"days": days, "limit": limit}

        if event_type:
            where_clauses.append("e.eventType = $event_type")
            params["event_type"] = event_type.value

        where_clause = " AND ".join(where_clauses)

        query = f"""
            MATCH (e:{self.node_label})
            WHERE {where_clause}
            RETURN e
            ORDER BY e.eventDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, params)
        return [neo4j_to_event(r["e"]) for r in result]

    def search_events(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MarketEvent]:
        """
        搜索事件

        Args:
            keyword: 搜索关键词
            skip: 跳过数量
            limit: 返回数量

        Returns:
            事件列表
        """
        results = self.search(keyword, ["title", "content"], skip, limit)
        return [neo4j_to_event(r) for r in results]

    def get_event_impact(self, event_id: str) -> Dict[str, Any]:
        """
        获取事件影响

        Args:
            event_id: 事件ID

        Returns:
            影响信息
        """
        query = """
            MATCH (e:MarketEvent {eventId: $event_id})-[r:IMPACTS]->(target)
            RETURN target, r
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})

        impacts = []
        for record in result:
            target = dict(record["target"])
            relationship = dict(record["r"])
            impacts.append({
                "target": target,
                "impact_type": relationship.get("impactType"),
                "impact_direction": relationship.get("impactDirection"),
                "confidence": relationship.get("confidence"),
            })

        return {
            "event_id": event_id,
            "impacts": impacts,
        }

    def get_event_chain(self, event_id: str) -> Dict[str, Any]:
        """
        获取事件链

        Args:
            event_id: 事件ID

        Returns:
            事件链信息
        """
        query = """
            MATCH path = (e:MarketEvent {eventId: $event_id})-[:CAUSED_BY*]->(root:MarketEvent)
            RETURN nodes(path) as events, relationships(path) as relations
        """
        result = self.neo4j.execute_query(query, {"event_id": event_id})

        if not result:
            event = self.find_by_event_id(event_id)
            return {
                "root_event": event,
                "chain": [],
                "depth": 0,
            }

        events = [neo4j_to_event(dict(e)) for e in result[0]["events"]]
        relations = [dict(r) for r in result[0]["relations"]]

        return {
            "root_event": events[0] if events else None,
            "chain": [
                {
                    "event": event,
                    "relation": relation,
                }
                for event, relation in zip(events[1:], relations)
            ],
            "depth": len(events) - 1,
        }

    def get_events_by_company(
        self,
        stock_code: str,
        days: int = 30,
        limit: int = 20,
    ) -> List[MarketEvent]:
        """
        获取影响公司的事件

        Args:
            stock_code: 股票代码
            days: 天数
            limit: 返回数量

        Returns:
            事件列表
        """
        query = """
            MATCH (e:MarketEvent)-[:IMPACTS]->(c:Company {stockCode: $stock_code})
            WHERE e.eventDate >= date() - duration({days: $days})
            RETURN e
            ORDER BY e.eventDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(
            query,
            {"stock_code": stock_code, "days": days, "limit": limit}
        )
        return [neo4j_to_event(r["e"]) for r in result]

    def get_events_by_industry(
        self,
        industry: str,
        days: int = 30,
        limit: int = 20,
    ) -> List[MarketEvent]:
        """
        获取影响行业的事件

        Args:
            industry: 行业名称
            days: 天数
            limit: 返回数量

        Returns:
            事件列表
        """
        query = """
            MATCH (e:MarketEvent)-[:IMPACTS]->(i:Industry {name: $industry})
            WHERE e.eventDate >= date() - duration({days: $days})
            RETURN e
            ORDER BY e.eventDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(
            query,
            {"industry": industry, "days": days, "limit": limit}
        )
        return [neo4j_to_event(r["e"]) for r in result]

    def create_event(self, event: MarketEventCreate) -> Optional[MarketEvent]:
        """
        创建事件

        Args:
            event: 事件创建模型

        Returns:
            创建的事件模型
        """
        # 检查是否已存在
        if self.exists(eventId=event.event_id):
            logger.warning(f"Event {event.event_id} already exists")
            return self.find_by_event_id(event.event_id)

        properties = event_to_neo4j(MarketEvent(**event.dict()))
        result = self.create(properties)
        if result:
            return neo4j_to_event(result)
        return None

    def create_impact_relationship(
        self,
        event_id: str,
        target_code: str,
        target_type: str,
        impact_type: str,
        impact_direction: str,
        confidence: float = 0.5,
    ) -> bool:
        """
        创建事件影响关系

        Args:
            event_id: 事件ID
            target_code: 目标代码
            target_type: 目标类型（Company/Industry）
            impact_type: 影响类型
            impact_direction: 影响方向
            confidence: 置信度

        Returns:
            是否创建成功
        """
        query = f"""
            MATCH (e:MarketEvent {{eventId: $event_id}})
            MATCH (t:{target_type} {{stockCode: $target_code}})
            CREATE (e)-[:IMPACTS {{
                impactType: $impact_type,
                impactDirection: $impact_direction,
                confidence: $confidence
            }}]->(t)
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "event_id": event_id,
                    "target_code": target_code,
                    "impact_type": impact_type,
                    "impact_direction": impact_direction,
                    "confidence": confidence,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create impact relationship: {e}")
            return False

    def create_causal_relationship(
        self,
        cause_event_id: str,
        effect_event_id: str,
    ) -> bool:
        """
        创建因果关系

        Args:
            cause_event_id: 原因事件ID
            effect_event_id: 结果事件ID

        Returns:
            是否创建成功
        """
        query = """
            MATCH (cause:MarketEvent {eventId: $cause_id})
            MATCH (effect:MarketEvent {eventId: $effect_id})
            CREATE (effect)-[:CAUSED_BY]->(cause)
        """
        try:
            self.neo4j.execute_write(
                query,
                {"cause_id": cause_event_id, "effect_id": effect_event_id}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create causal relationship: {e}")
            return False

    def batch_import(self, events: List[MarketEventCreate]) -> int:
        """
        批量导入事件

        Args:
            events: 事件列表

        Returns:
            导入的事件数量
        """
        count = 0
        for event in events:
            if self.create_event(event):
                count += 1
        return count
