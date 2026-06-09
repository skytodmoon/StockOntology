"""
投资者数据模型

定义投资者的数据结构。
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field
from enum import Enum


class InvestorType(str, Enum):
    """投资者类型"""
    FUND = "Fund"  # 基金
    QFII = "QFII"  # 合格境外机构投资者
    SOCIAL_SECURITY = "SocialSecurity"  # 社保
    INSURANCE = "Insurance"  # 保险
    BROKER = "Broker"  # 券商
    TRUST = "Trust"  # 信托
    BANK = "Bank"  # 银行
    PRIVATE = "Private"  # 私募
    RETAIL = "Retail"  # 散户
    OTHER = "Other"  # 其他


class InvestorBase(BaseModel):
    """投资者基础模型"""
    investor_id: str = Field(..., description="投资者ID", min_length=1, max_length=50)
    name: str = Field(..., description="投资者名称", min_length=1, max_length=100)
    investor_type: InvestorType = Field(..., description="投资者类型")
    description: Optional[str] = Field(None, description="投资者描述")
    website: Optional[str] = Field(None, description="网站")


class InvestorCreate(InvestorBase):
    """创建投资者请求模型"""
    pass


class InvestorUpdate(BaseModel):
    """更新投资者请求模型"""
    name: Optional[str] = Field(None, description="投资者名称")
    description: Optional[str] = Field(None, description="投资者描述")
    website: Optional[str] = Field(None, description="网站")


class Investor(InvestorBase):
    """投资者完整模型"""
    id: Optional[str] = Field(None, description="Neo4j 节点ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 关联数据
    holdings: List[Dict[str, Any]] = Field(default_factory=list, description="持仓列表")
    total_assets: Optional[float] = Field(None, description="总资产")

    class Config:
        """Pydantic 配置"""
        from_attributes = True


class InvestorResponse(BaseModel):
    """投资者响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: Optional[Investor] = Field(None, description="投资者数据")


class InvestorListResponse(BaseModel):
    """投资者列表响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: List[Investor] = Field(default_factory=list, description="投资者列表")
    total: int = Field(0, description="总数")


class Holding(BaseModel):
    """持仓模型"""
    investor_id: str = Field(..., description="投资者ID")
    investor_name: str = Field(..., description="投资者名称")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    shares: float = Field(..., description="持股数量", ge=0)
    ratio: float = Field(..., description="持股比例", ge=0, le=1)
    market_value: Optional[float] = Field(None, description="持仓市值")
    report_date: date = Field(..., description="报告日期")
    change_shares: Optional[float] = Field(None, description="持股变化")
    change_ratio: Optional[float] = Field(None, description="变化比例")


class HoldingResponse(BaseModel):
    """持仓响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: List[Holding] = Field(default_factory=list, description="持仓列表")
    total: int = Field(0, description="总数")


class InvestorBehavior(BaseModel):
    """投资者行为分析模型"""
    investor_id: str = Field(..., description="投资者ID")
    investor_name: str = Field(..., description="投资者名称")

    # 持仓特征
    holding_count: int = Field(0, description="持仓股票数量")
    total_market_value: float = Field(0, description="总持仓市值")
    concentration: float = Field(0, description="持仓集中度")

    # 行业偏好
    industry_preferences: Dict[str, float] = Field(
        default_factory=dict,
        description="行业偏好（行业->配置比例）"
    )

    # 交易风格
    trading_style: str = Field("", description="交易风格")
    holding_period: str = Field("", description="平均持仓周期")

    # 业绩表现
    return_rate: Optional[float] = Field(None, description="收益率")
    benchmark_return: Optional[float] = Field(None, description="基准收益率")
    excess_return: Optional[float] = Field(None, description="超额收益率")


def investor_to_neo4j(investor: Investor) -> Dict[str, Any]:
    """
    将投资者模型转换为 Neo4j 节点属性

    Args:
        investor: 投资者模型

    Returns:
        Neo4j 节点属性字典
    """
    return {
        "investorId": investor.investor_id,
        "name": investor.name,
        "investorType": investor.investor_type.value if isinstance(investor.investor_type, InvestorType) else investor.investor_type,
        "description": investor.description,
        "website": investor.website,
    }


def neo4j_to_investor(properties: Dict[str, Any]) -> Investor:
    """
    将 Neo4j 节点属性转换为投资者模型

    Args:
        properties: Neo4j 节点属性

    Returns:
        投资者模型
    """
    investor_type = InvestorType.OTHER
    if properties.get("investorType"):
        try:
            investor_type = InvestorType(properties["investorType"])
        except ValueError:
            pass

    return Investor(
        investor_id=properties.get("investorId", ""),
        name=properties.get("name", ""),
        investor_type=investor_type,
        description=properties.get("description"),
        website=properties.get("website"),
    )


def holding_to_neo4j(holding: Holding) -> Dict[str, Any]:
    """
    将持仓模型转换为 Neo4j 关系属性

    Args:
        holding: 持仓模型

    Returns:
        Neo4j 关系属性字典
    """
    return {
        "shares": holding.shares,
        "ratio": holding.ratio,
        "marketValue": holding.market_value,
        "reportDate": holding.report_date.isoformat(),
        "changeShares": holding.change_shares,
        "changeRatio": holding.change_ratio,
    }
