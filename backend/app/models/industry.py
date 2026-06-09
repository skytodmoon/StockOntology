"""
行业数据模型

定义行业的数据结构。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class IndustryBase(BaseModel):
    """行业基础模型"""
    code: str = Field(..., description="行业代码", min_length=1, max_length=20)
    name: str = Field(..., description="行业名称", min_length=1, max_length=100)
    level: int = Field(..., description="行业级别", ge=1, le=5)
    parent_code: Optional[str] = Field(None, description="上级行业代码")
    description: Optional[str] = Field(None, description="行业描述")


class IndustryCreate(IndustryBase):
    """创建行业请求模型"""
    pass


class IndustryUpdate(BaseModel):
    """更新行业请求模型"""
    name: Optional[str] = Field(None, description="行业名称")
    description: Optional[str] = Field(None, description="行业描述")


class Industry(IndustryBase):
    """行业完整模型"""
    id: Optional[str] = Field(None, description="Neo4j 节点ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 关联数据
    company_count: Optional[int] = Field(None, description="公司数量")
    total_market_cap: Optional[float] = Field(None, description="总市值")

    class Config:
        """Pydantic 配置"""
        from_attributes = True


class IndustryResponse(BaseModel):
    """行业响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: Optional[Industry] = Field(None, description="行业数据")


class IndustryListResponse(BaseModel):
    """行业列表响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: List[Industry] = Field(default_factory=list, description="行业列表")
    total: int = Field(0, description="总数")


class IndustryGraph(BaseModel):
    """行业关系图谱模型"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点列表")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边列表")


class IndustryComparison(BaseModel):
    """行业对比模型"""
    industries: List[str] = Field(..., description="行业代码列表")
    metrics: Dict[str, List[float]] = Field(default_factory=dict, description="对比指标")
    rankings: Dict[str, int] = Field(default_factory=dict, description="排名")


class IndustryChain(BaseModel):
    """产业链模型"""
    industry_code: str = Field(..., description="行业代码")
    industry_name: str = Field(..., description="行业名称")
    upstream: List[Dict[str, Any]] = Field(default_factory=list, description="上游行业")
    downstream: List[Dict[str, Any]] = Field(default_factory=list, description="下游行业")
    competitors: List[Dict[str, Any]] = Field(default_factory=list, description="竞争行业")


def industry_to_neo4j(industry: Industry) -> Dict[str, Any]:
    """
    将行业模型转换为 Neo4j 节点属性

    Args:
        industry: 行业模型

    Returns:
        Neo4j 节点属性字典
    """
    return {
        "code": industry.code,
        "name": industry.name,
        "level": industry.level,
        "parentCode": industry.parent_code,
        "description": industry.description,
    }


def neo4j_to_industry(properties: Dict[str, Any]) -> Industry:
    """
    将 Neo4j 节点属性转换为行业模型

    Args:
        properties: Neo4j 节点属性

    Returns:
        行业模型
    """
    return Industry(
        code=properties.get("code", ""),
        name=properties.get("name", ""),
        level=properties.get("level", 1),
        parent_code=properties.get("parentCode"),
        description=properties.get("description"),
    )
