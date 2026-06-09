"""
财务数据模型

定义财务报告的数据结构。
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ReportType(str, Enum):
    """报告类型"""
    Q1 = "Q1"  # 一季报
    Q2 = "Q2"  # 中报
    Q3 = "Q3"  # 三季报
    ANNUAL = "Annual"  # 年报


class FinancialReportBase(BaseModel):
    """财务报告基础模型"""
    stock_code: str = Field(..., description="股票代码")
    report_date: date = Field(..., description="报告日期")
    report_type: ReportType = Field(..., description="报告类型")

    # 利润表
    revenue: Optional[float] = Field(None, description="营业收入（元）")
    revenue_yoy: Optional[float] = Field(None, description="营收同比增长率")
    net_profit: Optional[float] = Field(None, description="净利润（元）")
    net_profit_yoy: Optional[float] = Field(None, description="净利润同比增长率")
    gross_profit: Optional[float] = Field(None, description="毛利润（元）")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    net_margin: Optional[float] = Field(None, description="净利率")

    # 资产负债表
    total_assets: Optional[float] = Field(None, description="总资产（元）")
    total_liabilities: Optional[float] = Field(None, description="总负债（元）")
    total_equity: Optional[float] = Field(None, description="股东权益（元）")
    debt_ratio: Optional[float] = Field(None, description="资产负债率")

    # 现金流量表
    operating_cashflow: Optional[float] = Field(None, description="经营活动现金流（元）")
    investing_cashflow: Optional[float] = Field(None, description="投资活动现金流（元）")
    financing_cashflow: Optional[float] = Field(None, description="筹资活动现金流（元）")

    # 每股指标
    eps: Optional[float] = Field(None, description="每股收益（元）")
    bps: Optional[float] = Field(None, description="每股净资产（元）")
    cfps: Optional[float] = Field(None, description="每股现金流（元）")

    # 盈利能力指标
    roe: Optional[float] = Field(None, description="净资产收益率")
    roa: Optional[float] = Field(None, description="总资产收益率")
    roic: Optional[float] = Field(None, description="投入资本回报率")

    # 成长性指标
    revenue_growth_3y: Optional[float] = Field(None, description="3年营收复合增长率")
    profit_growth_3y: Optional[float] = Field(None, description="3年利润复合增长率")

    # 估值指标
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    ps_ratio: Optional[float] = Field(None, description="市销率")


class FinancialReportCreate(FinancialReportBase):
    """创建财务报告请求模型"""
    pass


class FinancialReportUpdate(BaseModel):
    """更新财务报告请求模型"""
    revenue: Optional[float] = Field(None, description="营业收入")
    net_profit: Optional[float] = Field(None, description="净利润")
    total_assets: Optional[float] = Field(None, description="总资产")
    total_liabilities: Optional[float] = Field(None, description="总负债")
    total_equity: Optional[float] = Field(None, description="股东权益")
    eps: Optional[float] = Field(None, description="每股收益")
    roe: Optional[float] = Field(None, description="净资产收益率")


class FinancialReport(FinancialReportBase):
    """财务报告完整模型"""
    id: Optional[str] = Field(None, description="Neo4j 节点ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        """Pydantic 配置"""
        from_attributes = True


class FinancialReportResponse(BaseModel):
    """财务报告响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: Optional[FinancialReport] = Field(None, description="财务报告数据")


class FinancialReportListResponse(BaseModel):
    """财务报告列表响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: List[FinancialReport] = Field(default_factory=list, description="财务报告列表")
    total: int = Field(0, description="总数")


class FinancialAnalysis(BaseModel):
    """财务分析模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")

    # 盈利能力分析
    profitability: Dict[str, Any] = Field(default_factory=dict, description="盈利能力分析")

    # 成长性分析
    growth: Dict[str, Any] = Field(default_factory=dict, description="成长性分析")

    # 偿债能力分析
    solvency: Dict[str, Any] = Field(default_factory=dict, description="偿债能力分析")

    # 营运能力分析
    efficiency: Dict[str, Any] = Field(default_factory=dict, description="营运能力分析")

    # 现金流分析
    cashflow: Dict[str, Any] = Field(default_factory=dict, description="现金流分析")

    # 综合评分
    total_score: float = Field(0, description="综合评分")
    rating: str = Field("", description="评级")


class FinancialIndicator(BaseModel):
    """财务指标模型"""
    name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    unit: str = Field("", description="单位")
    change: Optional[float] = Field(None, description="变化值")
    change_rate: Optional[float] = Field(None, description="变化率")
    benchmark: Optional[float] = Field(None, description="基准值")
    status: str = Field("normal", description="状态（normal/warning/danger）")


def financial_report_to_neo4j(report: FinancialReport) -> Dict[str, Any]:
    """
    将财务报告模型转换为 Neo4j 节点属性

    Args:
        report: 财务报告模型

    Returns:
        Neo4j 节点属性字典
    """
    return {
        "stockCode": report.stock_code,
        "reportDate": report.report_date.isoformat(),
        "reportType": report.report_type.value if isinstance(report.report_type, ReportType) else report.report_type,
        "revenue": report.revenue,
        "revenueYoy": report.revenue_yoy,
        "netProfit": report.net_profit,
        "netProfitYoy": report.net_profit_yoy,
        "grossProfit": report.gross_profit,
        "grossMargin": report.gross_margin,
        "netMargin": report.net_margin,
        "totalAssets": report.total_assets,
        "totalLiabilities": report.total_liabilities,
        "totalEquity": report.total_equity,
        "debtRatio": report.debt_ratio,
        "operatingCashflow": report.operating_cashflow,
        "investingCashflow": report.investing_cashflow,
        "financingCashflow": report.financing_cashflow,
        "eps": report.eps,
        "bps": report.bps,
        "cfps": report.cfps,
        "roe": report.roe,
        "roa": report.roa,
        "roic": report.roic,
        "peRatio": report.pe_ratio,
        "pbRatio": report.pb_ratio,
        "psRatio": report.ps_ratio,
    }


def neo4j_to_financial_report(properties: Dict[str, Any]) -> FinancialReport:
    """
    将 Neo4j 节点属性转换为财务报告模型

    Args:
        properties: Neo4j 节点属性

    Returns:
        财务报告模型
    """
    report_date = date.today()
    if properties.get("reportDate"):
        try:
            report_date = date.fromisoformat(properties["reportDate"])
        except ValueError:
            pass

    report_type = ReportType.ANNUAL
    if properties.get("reportType"):
        try:
            report_type = ReportType(properties["reportType"])
        except ValueError:
            pass

    return FinancialReport(
        stock_code=properties.get("stockCode", ""),
        report_date=report_date,
        report_type=report_type,
        revenue=properties.get("revenue"),
        revenue_yoy=properties.get("revenueYoy"),
        net_profit=properties.get("netProfit"),
        net_profit_yoy=properties.get("netProfitYoy"),
        gross_profit=properties.get("grossProfit"),
        gross_margin=properties.get("grossMargin"),
        net_margin=properties.get("netMargin"),
        total_assets=properties.get("totalAssets"),
        total_liabilities=properties.get("totalLiabilities"),
        total_equity=properties.get("totalEquity"),
        debt_ratio=properties.get("debtRatio"),
        operating_cashflow=properties.get("operatingCashflow"),
        investing_cashflow=properties.get("investingCashflow"),
        financing_cashflow=properties.get("financingCashflow"),
        eps=properties.get("eps"),
        bps=properties.get("bps"),
        cfps=properties.get("cfps"),
        roe=properties.get("roe"),
        roa=properties.get("roa"),
        roic=properties.get("roic"),
        pe_ratio=properties.get("peRatio"),
        pb_ratio=properties.get("pbRatio"),
        ps_ratio=properties.get("psRatio"),
    )
