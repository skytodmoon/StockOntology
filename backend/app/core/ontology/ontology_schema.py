"""
本体 Schema 定义

定义股票市场本体的核心概念和关系。
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# 枚举定义

class EntityType(str, Enum):
    """实体类型"""
    COMPANY = "Company"
    INDUSTRY = "Industry"
    FINANCIAL_REPORT = "FinancialReport"
    MARKET_EVENT = "MarketEvent"
    INVESTOR = "Investor"
    STOCK = "Stock"
    INDEX = "Index"


class RelationType(str, Enum):
    """关系类型"""
    BELONGS_TO = "BELONGS_TO"
    COMPETES_WITH = "COMPETES_WITH"
    SUPPLY_TO = "SUPPLY_TO"
    IMPACTS = "IMPACTS"
    HOLDS = "HOLDS"
    HAS_REPORT = "HAS_REPORT"
    CORRELATED_WITH = "CORRELATED_WITH"
    CAUSED_BY = "CAUSED_BY"
    SUB_INDUSTRY_OF = "SUB_INDUSTRY_OF"


class PropertyType(str, Enum):
    """属性类型"""
    OBJECT = "object"
    DATA = "data"


class DataType(str, Enum):
    """数据类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"


# Schema 定义

class ClassDefinition(BaseModel):
    """类定义"""
    name: str = Field(..., description="类名")
    parent: Optional[str] = Field(None, description="父类名")
    comment: Optional[str] = Field(None, description="注释")
    properties: List[str] = Field(default_factory=list, description="关联的属性列表")


class PropertyDefinition(BaseModel):
    """属性定义"""
    name: str = Field(..., description="属性名")
    property_type: PropertyType = Field(..., description="属性类型")
    domain: List[str] = Field(..., description="定义域")
    range_type: List[str] = Field(..., description="值域")
    comment: Optional[str] = Field(None, description="注释")
    functional: bool = Field(False, description="是否为函数属性")
    inverse_functional: bool = Field(False, description="是否为反函数属性")
    transitive: bool = Field(False, description="是否为传递属性")
    symmetric: bool = Field(False, description="是否为对称属性")


class InstanceDefinition(BaseModel):
    """实例定义"""
    name: str = Field(..., description="实例名")
    class_name: str = Field(..., description="所属类名")
    properties: Dict[str, Any] = Field(default_factory=dict, description="实例属性")


class OntologySchema(BaseModel):
    """本体 Schema"""
    name: str = Field(..., description="本体名称")
    namespace: str = Field(..., description="命名空间")
    description: Optional[str] = Field(None, description="本体描述")
    classes: List[ClassDefinition] = Field(default_factory=list, description="类定义列表")
    properties: List[PropertyDefinition] = Field(default_factory=list, description="属性定义列表")
    instances: List[InstanceDefinition] = Field(default_factory=list, description="实例定义列表")

    class Config:
        """Pydantic 配置"""
        use_enum_values = True


# 预定义的本体 Schema

STOCK_ONTOLOGY_SCHEMA = OntologySchema(
    name="StockOntology",
    namespace="http://stock-ontology.org/",
    description="股票市场本体",
    classes=[
        # 基础类
        ClassDefinition(
            name="FinancialEntity",
            comment="金融实体基类",
        ),
        ClassDefinition(
            name="Company",
            parent="FinancialEntity",
            comment="上市公司",
            properties=["hasStockCode", "hasStockName", "hasMarketCap", "hasListDate"],
        ),
        ClassDefinition(
            name="Industry",
            parent="FinancialEntity",
            comment="行业",
            properties=["hasIndustryCode", "hasIndustryName", "hasIndustryLevel"],
        ),
        ClassDefinition(
            name="FinancialReport",
            parent="FinancialEntity",
            comment="财务报告",
            properties=["hasReportDate", "hasReportType", "hasRevenue", "hasNetProfit"],
        ),
        ClassDefinition(
            name="MarketEvent",
            parent="FinancialEntity",
            comment="市场事件",
            properties=["hasEventId", "hasEventType", "hasEventDate", "hasImpactLevel"],
        ),
        ClassDefinition(
            name="Investor",
            parent="FinancialEntity",
            comment="投资者",
            properties=["hasInvestorId", "hasInvestorName", "hasInvestorType"],
        ),
        ClassDefinition(
            name="Stock",
            parent="FinancialEntity",
            comment="股票",
            properties=["hasStockCode", "hasCurrentPrice", "hasVolume"],
        ),
        ClassDefinition(
            name="Index",
            parent="FinancialEntity",
            comment="指数",
            properties=["hasIndexCode", "hasIndexName", "hasIndexValue"],
        ),
    ],
    properties=[
        # 数据属性
        PropertyDefinition(
            name="hasStockCode",
            property_type=PropertyType.DATA,
            domain=["Company", "Stock"],
            range_type=["string"],
            comment="股票代码",
        ),
        PropertyDefinition(
            name="hasStockName",
            property_type=PropertyType.DATA,
            domain=["Company"],
            range_type=["string"],
            comment="股票名称",
        ),
        PropertyDefinition(
            name="hasMarketCap",
            property_type=PropertyType.DATA,
            domain=["Company"],
            range_type=["float"],
            comment="市值",
        ),
        PropertyDefinition(
            name="hasListDate",
            property_type=PropertyType.DATA,
            domain=["Company"],
            range_type=["date"],
            comment="上市日期",
        ),
        PropertyDefinition(
            name="hasIndustryCode",
            property_type=PropertyType.DATA,
            domain=["Industry"],
            range_type=["string"],
            comment="行业代码",
        ),
        PropertyDefinition(
            name="hasIndustryName",
            property_type=PropertyType.DATA,
            domain=["Industry"],
            range_type=["string"],
            comment="行业名称",
        ),
        PropertyDefinition(
            name="hasIndustryLevel",
            property_type=PropertyType.DATA,
            domain=["Industry"],
            range_type=["integer"],
            comment="行业级别",
        ),
        PropertyDefinition(
            name="hasReportDate",
            property_type=PropertyType.DATA,
            domain=["FinancialReport"],
            range_type=["date"],
            comment="报告日期",
        ),
        PropertyDefinition(
            name="hasReportType",
            property_type=PropertyType.DATA,
            domain=["FinancialReport"],
            range_type=["string"],
            comment="报告类型",
        ),
        PropertyDefinition(
            name="hasRevenue",
            property_type=PropertyType.DATA,
            domain=["FinancialReport"],
            range_type=["float"],
            comment="营业收入",
        ),
        PropertyDefinition(
            name="hasNetProfit",
            property_type=PropertyType.DATA,
            domain=["FinancialReport"],
            range_type=["float"],
            comment="净利润",
        ),
        PropertyDefinition(
            name="hasEventId",
            property_type=PropertyType.DATA,
            domain=["MarketEvent"],
            range_type=["string"],
            comment="事件ID",
        ),
        PropertyDefinition(
            name="hasEventType",
            property_type=PropertyType.DATA,
            domain=["MarketEvent"],
            range_type=["string"],
            comment="事件类型",
        ),
        PropertyDefinition(
            name="hasEventDate",
            property_type=PropertyType.DATA,
            domain=["MarketEvent"],
            range_type=["date"],
            comment="事件日期",
        ),
        PropertyDefinition(
            name="hasImpactLevel",
            property_type=PropertyType.DATA,
            domain=["MarketEvent"],
            range_type=["string"],
            comment="影响级别",
        ),
        PropertyDefinition(
            name="hasInvestorId",
            property_type=PropertyType.DATA,
            domain=["Investor"],
            range_type=["string"],
            comment="投资者ID",
        ),
        PropertyDefinition(
            name="hasInvestorName",
            property_type=PropertyType.DATA,
            domain=["Investor"],
            range_type=["string"],
            comment="投资者名称",
        ),
        PropertyDefinition(
            name="hasInvestorType",
            property_type=PropertyType.DATA,
            domain=["Investor"],
            range_type=["string"],
            comment="投资者类型",
        ),
        PropertyDefinition(
            name="hasCurrentPrice",
            property_type=PropertyType.DATA,
            domain=["Stock"],
            range_type=["float"],
            comment="当前价格",
        ),
        PropertyDefinition(
            name="hasVolume",
            property_type=PropertyType.DATA,
            domain=["Stock"],
            range_type=["float"],
            comment="成交量",
        ),
        PropertyDefinition(
            name="hasIndexCode",
            property_type=PropertyType.DATA,
            domain=["Index"],
            range_type=["string"],
            comment="指数代码",
        ),
        PropertyDefinition(
            name="hasIndexName",
            property_type=PropertyType.DATA,
            domain=["Index"],
            range_type=["string"],
            comment="指数名称",
        ),
        PropertyDefinition(
            name="hasIndexValue",
            property_type=PropertyType.DATA,
            domain=["Index"],
            range_type=["float"],
            comment="指数值",
        ),
        # 对象属性
        PropertyDefinition(
            name="belongsToIndustry",
            property_type=PropertyType.OBJECT,
            domain=["Company"],
            range_type=["Industry"],
            comment="所属行业",
        ),
        PropertyDefinition(
            name="subIndustryOf",
            property_type=PropertyType.OBJECT,
            domain=["Industry"],
            range_type=["Industry"],
            comment="上级行业",
            transitive=True,
        ),
        PropertyDefinition(
            name="competesWith",
            property_type=PropertyType.OBJECT,
            domain=["Company"],
            range_type=["Company"],
            comment="竞争关系",
            symmetric=True,
        ),
        PropertyDefinition(
            name="supplyTo",
            property_type=PropertyType.OBJECT,
            domain=["Company"],
            range_type=["Company"],
            comment="供应关系",
        ),
        PropertyDefinition(
            name="impacts",
            property_type=PropertyType.OBJECT,
            domain=["MarketEvent"],
            range_type=["Company", "Industry"],
            comment="影响",
        ),
        PropertyDefinition(
            name="holds",
            property_type=PropertyType.OBJECT,
            domain=["Investor"],
            range_type=["Company"],
            comment="持有",
        ),
        PropertyDefinition(
            name="hasFinancialReport",
            property_type=PropertyType.OBJECT,
            domain=["Company"],
            range_type=["FinancialReport"],
            comment="财务报告",
        ),
        PropertyDefinition(
            name="correlatedWith",
            property_type=PropertyType.OBJECT,
            domain=["Company"],
            range_type=["Company"],
            comment="相关性",
            symmetric=True,
        ),
        PropertyDefinition(
            name="causedBy",
            property_type=PropertyType.OBJECT,
            domain=["MarketEvent"],
            range_type=["MarketEvent"],
            comment="由...引起",
        ),
    ],
)


def get_default_schema() -> OntologySchema:
    """获取默认的本体 Schema"""
    return STOCK_ONTOLOGY_SCHEMA


def validate_schema(schema: OntologySchema) -> List[str]:
    """
    验证本体 Schema

    Args:
        schema: 本体 Schema

    Returns:
        错误信息列表
    """
    errors = []

    # 检查类定义的父类是否存在
    class_names = {cls.name for cls in schema.classes}
    for cls in schema.classes:
        if cls.parent and cls.parent not in class_names:
            errors.append(f"Class '{cls.name}' has undefined parent '{cls.parent}'")

    # 检查属性定义的定义域和值域
    for prop in schema.properties:
        for domain in prop.domain:
            if domain not in class_names:
                errors.append(f"Property '{prop.name}' has undefined domain '{domain}'")
        for range_type in prop.range_type:
            if prop.property_type == PropertyType.OBJECT:
                if range_type not in class_names:
                    errors.append(f"Property '{prop.name}' has undefined range '{range_type}'")

    # 检查实例定义的类是否存在
    for instance in schema.instances:
        if instance.class_name not in class_names:
            errors.append(f"Instance '{instance.name}' has undefined class '{instance.class_name}'")

    return errors
