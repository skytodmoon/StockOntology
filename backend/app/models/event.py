"""
市场事件数据模型

定义市场事件的数据结构。
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """事件类型"""
    POLICY = "PolicyEvent"  # 政策事件
    COMPANY = "CompanyEvent"  # 公司事件
    MACRO = "MacroEvent"  # 宏观事件
    INDUSTRY = "IndustryEvent"  # 行业事件
    MARKET = "MarketEvent"  # 市场事件


class ImpactLevel(str, Enum):
    """影响级别"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ImpactDirection(str, Enum):
    """影响方向"""
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"


class MarketEventBase(BaseModel):
    """市场事件基础模型"""
    event_id: str = Field(..., description="事件ID", min_length=1, max_length=50)
    title: str = Field(..., description="事件标题", min_length=1, max_length=200)
    event_type: EventType = Field(..., description="事件类型")
    event_date: date = Field(..., description="事件日期")
    event_time: Optional[datetime] = Field(None, description="事件时间")
    source: Optional[str] = Field(None, description="事件来源")
    content: Optional[str] = Field(None, description="事件内容")
    impact_level: ImpactLevel = Field(ImpactLevel.MEDIUM, description="影响级别")
    tags: List[str] = Field(default_factory=list, description="标签")


class MarketEventCreate(MarketEventBase):
    """创建市场事件请求模型"""
    pass


class MarketEventUpdate(BaseModel):
    """更新市场事件请求模型"""
    title: Optional[str] = Field(None, description="事件标题")
    content: Optional[str] = Field(None, description="事件内容")
    impact_level: Optional[ImpactLevel] = Field(None, description="影响级别")
    tags: Optional[List[str]] = Field(None, description="标签")


class MarketEvent(MarketEventBase):
    """市场事件完整模型"""
    id: Optional[str] = Field(None, description="Neo4j 节点ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 关联数据
    impacted_companies: List[str] = Field(default_factory=list, description="受影响的公司")
    impacted_industries: List[str] = Field(default_factory=list, description="受影响的行业")
    related_events: List[str] = Field(default_factory=list, description="相关事件")

    class Config:
        """Pydantic 配置"""
        from_attributes = True


class MarketEventResponse(BaseModel):
    """市场事件响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: Optional[MarketEvent] = Field(None, description="事件数据")


class MarketEventListResponse(BaseModel):
    """市场事件列表响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: List[MarketEvent] = Field(default_factory=list, description="事件列表")
    total: int = Field(0, description="总数")


class EventImpact(BaseModel):
    """事件影响模型"""
    event_id: str = Field(..., description="事件ID")
    event_title: str = Field(..., description="事件标题")

    # 直接影响
    direct_impact: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="直接影响列表"
    )

    # 间接影响
    indirect_impact: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="间接影响列表"
    )

    # 影响链
    impact_chain: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="影响传播链"
    )

    # 影响评估
    total_impact_score: float = Field(0, description="总影响分数")
    confidence: float = Field(0.5, description="置信度", ge=0, le=1)


class EventChain(BaseModel):
    """事件链模型"""
    root_event: MarketEvent = Field(..., description="根事件")
    chain: List[Dict[str, Any]] = Field(default_factory=list, description="事件链")
    depth: int = Field(0, description="链深度")


class EventAlert(BaseModel):
    """事件预警模型"""
    alert_id: str = Field(..., description="预警ID")
    event: MarketEvent = Field(..., description="触发事件")
    alert_type: str = Field(..., description="预警类型")
    alert_level: ImpactLevel = Field(..., description="预警级别")
    message: str = Field(..., description="预警消息")
    affected_assets: List[str] = Field(default_factory=list, description="受影响资产")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    is_read: bool = Field(False, description="是否已读")


def event_to_neo4j(event: MarketEvent) -> Dict[str, Any]:
    """
    将市场事件模型转换为 Neo4j 节点属性

    Args:
        event: 市场事件模型

    Returns:
        Neo4j 节点属性字典
    """
    return {
        "eventId": event.event_id,
        "title": event.title,
        "eventType": event.event_type.value if isinstance(event.event_type, EventType) else event.event_type,
        "eventDate": event.event_date.isoformat(),
        "eventTime": event.event_time.isoformat() if event.event_time else None,
        "source": event.source,
        "content": event.content,
        "impactLevel": event.impact_level.value if isinstance(event.impact_level, ImpactLevel) else event.impact_level,
        "tags": event.tags,
    }


def neo4j_to_event(properties: Dict[str, Any]) -> MarketEvent:
    """
    将 Neo4j 节点属性转换为市场事件模型

    Args:
        properties: Neo4j 节点属性

    Returns:
        市场事件模型
    """
    event_date = date.today()
    if properties.get("eventDate"):
        try:
            event_date = date.fromisoformat(properties["eventDate"])
        except ValueError:
            pass

    event_time = None
    if properties.get("eventTime"):
        try:
            event_time = datetime.fromisoformat(properties["eventTime"])
        except ValueError:
            pass

    event_type = EventType.MARKET
    if properties.get("eventType"):
        try:
            event_type = EventType(properties["eventType"])
        except ValueError:
            pass

    impact_level = ImpactLevel.MEDIUM
    if properties.get("impactLevel"):
        try:
            impact_level = ImpactLevel(properties["impactLevel"])
        except ValueError:
            pass

    return MarketEvent(
        event_id=properties.get("eventId", ""),
        title=properties.get("title", ""),
        event_type=event_type,
        event_date=event_date,
        event_time=event_time,
        source=properties.get("source"),
        content=properties.get("content"),
        impact_level=impact_level,
        tags=properties.get("tags", []),
    )
