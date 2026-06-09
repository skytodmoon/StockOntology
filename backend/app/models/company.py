"""
公司数据模型

定义上市公司的数据结构。
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator


class CompanyBase(BaseModel):
    """公司基础模型"""
    stock_code: str = Field(..., description="股票代码", min_length=6, max_length=10)
    stock_name: str = Field(..., description="股票名称", min_length=1, max_length=50)
    market: str = Field(..., description="市场（SH/SZ/BJ）")
    industry: Optional[str] = Field(None, description="所属行业")
    list_date: Optional[date] = Field(None, description="上市日期")
    market_cap: Optional[float] = Field(None, description="市值（元）", ge=0)
    total_share: Optional[float] = Field(None, description="总股本（股）", ge=0)
    float_share: Optional[float] = Field(None, description="流通股本（股）", ge=0)
    description: Optional[str] = Field(None, description="公司简介")
    website: Optional[str] = Field(None, description="公司网站")
    address: Optional[str] = Field(None, description="公司地址")

    @validator("stock_code")
    def validate_stock_code(cls, v):
        """验证股票代码格式"""
        if not v.isdigit():
            raise ValueError("Stock code must be numeric")
        return v

    @validator("market")
    def validate_market(cls, v):
        """验证市场代码"""
        valid_markets = ["SH", "SZ", "BJ"]
        if v.upper() not in valid_markets:
            raise ValueError(f"Market must be one of {valid_markets}")
        return v.upper()


class CompanyCreate(CompanyBase):
    """创建公司请求模型"""
    pass


class CompanyUpdate(BaseModel):
    """更新公司请求模型"""
    stock_name: Optional[str] = Field(None, description="股票名称")
    industry: Optional[str] = Field(None, description="所属行业")
    market_cap: Optional[float] = Field(None, description="市值")
    total_share: Optional[float] = Field(None, description="总股本")
    float_share: Optional[float] = Field(None, description="流通股本")
    description: Optional[str] = Field(None, description="公司简介")
    website: Optional[str] = Field(None, description="公司网站")
    address: Optional[str] = Field(None, description="公司地址")


class Company(CompanyBase):
    """公司完整模型"""
    id: Optional[str] = Field(None, description="Neo4j 节点ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 计算属性
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    roe: Optional[float] = Field(None, description="净资产收益率")

    class Config:
        """Pydantic 配置"""
        from_attributes = True


class CompanyResponse(BaseModel):
    """公司响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: Optional[Company] = Field(None, description="公司数据")


class CompanyListResponse(BaseModel):
    """公司列表响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: List[Company] = Field(default_factory=list, description="公司列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")


class CompanyGraph(BaseModel):
    """公司关系图谱模型"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点列表")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边列表")


class CompanyAnalysis(BaseModel):
    """公司分析模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    financial_summary: Dict[str, Any] = Field(default_factory=dict, description="财务摘要")
    industry_position: Dict[str, Any] = Field(default_factory=dict, description="行业地位")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素")
    investment_rating: Optional[str] = Field(None, description="投资评级")
    target_price: Optional[float] = Field(None, description="目标价格")


class CompanyPrediction(BaseModel):
    """公司预测模型"""
    stock_code: str = Field(..., description="股票代码")
    prediction_date: date = Field(..., description="预测日期")
    predicted_price: float = Field(..., description="预测价格")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    factors: List[Dict[str, Any]] = Field(default_factory=list, description="影响因素")
    model_name: str = Field(..., description="使用的模型名称")


def company_to_neo4j(company: Company) -> Dict[str, Any]:
    """
    将公司模型转换为 Neo4j 节点属性

    Args:
        company: 公司模型

    Returns:
        Neo4j 节点属性字典
    """
    return {
        "stockCode": company.stock_code,
        "stockName": company.stock_name,
        "market": company.market,
        "industry": company.industry,
        "listDate": company.list_date.isoformat() if company.list_date else None,
        "marketCap": company.market_cap,
        "totalShare": company.total_share,
        "floatShare": company.float_share,
        "description": company.description,
        "website": company.website,
        "address": company.address,
    }


def neo4j_to_company(properties: Dict[str, Any]) -> Company:
    """
    将 Neo4j 节点属性转换为公司模型

    Args:
        properties: Neo4j 节点属性

    Returns:
        公司模型
    """
    list_date = None
    if properties.get("listDate"):
        try:
            list_date = date.fromisoformat(properties["listDate"])
        except ValueError:
            pass

    return Company(
        stock_code=properties.get("stockCode", ""),
        stock_name=properties.get("stockName", ""),
        market=properties.get("market", ""),
        industry=properties.get("industry"),
        list_date=list_date,
        market_cap=properties.get("marketCap"),
        total_share=properties.get("totalShare"),
        float_share=properties.get("floatShare"),
        description=properties.get("description"),
        website=properties.get("website"),
        address=properties.get("address"),
    )
