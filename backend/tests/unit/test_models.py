"""
数据模型测试
"""

import pytest
from datetime import date, datetime

from app.models.company import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    company_to_neo4j,
    neo4j_to_company,
)
from app.models.industry import (
    Industry,
    IndustryCreate,
    industry_to_neo4j,
    neo4j_to_industry,
)
from app.models.financial import (
    FinancialReport,
    FinancialReportCreate,
    ReportType,
    financial_report_to_neo4j,
    neo4j_to_financial_report,
)
from app.models.event import (
    MarketEvent,
    MarketEventCreate,
    EventType,
    ImpactLevel,
    event_to_neo4j,
    neo4j_to_event,
)
from app.models.investor import (
    Investor,
    InvestorCreate,
    InvestorType,
    investor_to_neo4j,
    neo4j_to_investor,
)


class TestCompanyModel:
    """公司模型测试"""

    def test_create_company(self):
        """测试创建公司"""
        company = CompanyCreate(
            stock_code="600519",
            stock_name="贵州茅台",
            market="SH",
            industry="白酒",
        )
        assert company.stock_code == "600519"
        assert company.stock_name == "贵州茅台"
        assert company.market == "SH"

    def test_company_validation(self):
        """测试公司验证"""
        # 无效的股票代码
        with pytest.raises(ValueError):
            CompanyCreate(
                stock_code="abc",
                stock_name="测试",
                market="SH",
            )

        # 无效的市场代码
        with pytest.raises(ValueError):
            CompanyCreate(
                stock_code="600519",
                stock_name="测试",
                market="XX",
            )

    def test_company_to_neo4j(self):
        """测试公司转 Neo4j 属性"""
        company = Company(
            stock_code="600519",
            stock_name="贵州茅台",
            market="SH",
            industry="白酒",
            list_date=date(2001, 8, 27),
            market_cap=2100000000000,
        )
        neo4j_props = company_to_neo4j(company)
        assert neo4j_props["stockCode"] == "600519"
        assert neo4j_props["stockName"] == "贵州茅台"
        assert neo4j_props["market"] == "SH"

    def test_neo4j_to_company(self):
        """测试 Neo4j 属性转公司"""
        props = {
            "stockCode": "600519",
            "stockName": "贵州茅台",
            "market": "SH",
            "industry": "白酒",
            "listDate": "2001-08-27",
            "marketCap": 2100000000000,
        }
        company = neo4j_to_company(props)
        assert company.stock_code == "600519"
        assert company.stock_name == "贵州茅台"
        assert company.list_date == date(2001, 8, 27)

    def test_company_update(self):
        """测试公司更新"""
        update = CompanyUpdate(stock_name="茅台", market_cap=2200000000000)
        assert update.stock_name == "茅台"
        assert update.market_cap == 2200000000000


class TestIndustryModel:
    """行业模型测试"""

    def test_create_industry(self):
        """测试创建行业"""
        industry = IndustryCreate(
            code="C1511",
            name="白酒制造",
            level=3,
        )
        assert industry.code == "C1511"
        assert industry.name == "白酒制造"
        assert industry.level == 3

    def test_industry_to_neo4j(self):
        """测试行业转 Neo4j 属性"""
        industry = Industry(
            code="C1511",
            name="白酒制造",
            level=3,
            parent_code="C15",
        )
        neo4j_props = industry_to_neo4j(industry)
        assert neo4j_props["code"] == "C1511"
        assert neo4j_props["name"] == "白酒制造"
        assert neo4j_props["level"] == 3

    def test_neo4j_to_industry(self):
        """测试 Neo4j 属性转行业"""
        props = {
            "code": "C1511",
            "name": "白酒制造",
            "level": 3,
            "parentCode": "C15",
        }
        industry = neo4j_to_industry(props)
        assert industry.code == "C1511"
        assert industry.parent_code == "C15"


class TestFinancialReportModel:
    """财务报告模型测试"""

    def test_create_financial_report(self):
        """测试创建财务报告"""
        report = FinancialReportCreate(
            stock_code="600519",
            report_date=date(2024, 3, 31),
            report_type=ReportType.Q1,
            revenue=46700000000,
            net_profit=24000000000,
        )
        assert report.stock_code == "600519"
        assert report.report_type == ReportType.Q1

    def test_financial_report_to_neo4j(self):
        """测试财务报告转 Neo4j 属性"""
        report = FinancialReport(
            stock_code="600519",
            report_date=date(2024, 3, 31),
            report_type=ReportType.Q1,
            revenue=46700000000,
            net_profit=24000000000,
            roe=0.085,
        )
        neo4j_props = financial_report_to_neo4j(report)
        assert neo4j_props["stockCode"] == "600519"
        assert neo4j_props["reportType"] == "Q1"
        assert neo4j_props["roe"] == 0.085

    def test_neo4j_to_financial_report(self):
        """测试 Neo4j 属性转财务报告"""
        props = {
            "stockCode": "600519",
            "reportDate": "2024-03-31",
            "reportType": "Q1",
            "revenue": 46700000000,
            "netProfit": 24000000000,
            "roe": 0.085,
        }
        report = neo4j_to_financial_report(props)
        assert report.stock_code == "600519"
        assert report.report_date == date(2024, 3, 31)
        assert report.report_type == ReportType.Q1


class TestMarketEventModel:
    """市场事件模型测试"""

    def test_create_market_event(self):
        """测试创建市场事件"""
        event = MarketEventCreate(
            event_id="EVT001",
            title="央行降准0.5个百分点",
            event_type=EventType.POLICY,
            event_date=date(2024, 2, 5),
            impact_level=ImpactLevel.HIGH,
        )
        assert event.event_id == "EVT001"
        assert event.event_type == EventType.POLICY

    def test_market_event_to_neo4j(self):
        """测试市场事件转 Neo4j 属性"""
        event = MarketEvent(
            event_id="EVT001",
            title="央行降准0.5个百分点",
            event_type=EventType.POLICY,
            event_date=date(2024, 2, 5),
            impact_level=ImpactLevel.HIGH,
        )
        neo4j_props = event_to_neo4j(event)
        assert neo4j_props["eventId"] == "EVT001"
        assert neo4j_props["eventType"] == "PolicyEvent"

    def test_neo4j_to_market_event(self):
        """测试 Neo4j 属性转市场事件"""
        props = {
            "eventId": "EVT001",
            "title": "央行降准0.5个百分点",
            "eventType": "PolicyEvent",
            "eventDate": "2024-02-05",
            "impactLevel": "High",
        }
        event = neo4j_to_event(props)
        assert event.event_id == "EVT001"
        assert event.event_type == EventType.POLICY


class TestInvestorModel:
    """投资者模型测试"""

    def test_create_investor(self):
        """测试创建投资者"""
        investor = InvestorCreate(
            investor_id="INV001",
            name="易方达蓝筹精选",
            investor_type=InvestorType.FUND,
        )
        assert investor.investor_id == "INV001"
        assert investor.investor_type == InvestorType.FUND

    def test_investor_to_neo4j(self):
        """测试投资者转 Neo4j 属性"""
        investor = Investor(
            investor_id="INV001",
            name="易方达蓝筹精选",
            investor_type=InvestorType.FUND,
        )
        neo4j_props = investor_to_neo4j(investor)
        assert neo4j_props["investorId"] == "INV001"
        assert neo4j_props["investorType"] == "Fund"

    def test_neo4j_to_investor(self):
        """测试 Neo4j 属性转投资者"""
        props = {
            "investorId": "INV001",
            "name": "易方达蓝筹精选",
            "investorType": "Fund",
        }
        investor = neo4j_to_investor(props)
        assert investor.investor_id == "INV001"
        assert investor.investor_type == InvestorType.FUND
