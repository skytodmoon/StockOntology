"""
财务数据仓库

提供财务报告数据的访问方法。
"""

from typing import Any, Dict, List, Optional
from datetime import date
from loguru import logger

from .base_repository import BaseRepository
from app.models.financial import (
    FinancialReport,
    FinancialReportCreate,
    ReportType,
    financial_report_to_neo4j,
    neo4j_to_financial_report,
)


class FinancialRepository(BaseRepository[FinancialReport]):
    """财务数据仓库"""

    def __init__(self):
        super().__init__("FinancialReport")

    def find_by_stock_code_and_date(
        self,
        stock_code: str,
        report_date: date,
        report_type: ReportType = None,
    ) -> Optional[FinancialReport]:
        """
        根据股票代码和报告日期查找财务报告

        Args:
            stock_code: 股票代码
            report_date: 报告日期
            report_type: 报告类型

        Returns:
            财务报告模型
        """
        query = """
            MATCH (f:FinancialReport {stockCode: $stock_code, reportDate: $report_date})
            WHERE $report_type IS NULL OR f.reportType = $report_type
            RETURN f
            LIMIT 1
        """
        result = self.neo4j.execute_query(
            query,
            {
                "stock_code": stock_code,
                "report_date": report_date.isoformat(),
                "report_type": report_type.value if report_type else None,
            }
        )
        if result:
            return neo4j_to_financial_report(result[0]["f"])
        return None

    def find_latest_by_stock_code(
        self,
        stock_code: str,
    ) -> Optional[FinancialReport]:
        """
        查找最新的财务报告

        Args:
            stock_code: 股票代码

        Returns:
            财务报告模型
        """
        query = """
            MATCH (f:FinancialReport {stockCode: $stock_code})
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT 1
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code})
        if result:
            return neo4j_to_financial_report(result[0]["f"])
        return None

    def find_by_stock_code(
        self,
        stock_code: str,
        report_type: ReportType = None,
        start_date: date = None,
        end_date: date = None,
        limit: int = 20,
    ) -> List[FinancialReport]:
        """
        查找公司的财务报告列表

        Args:
            stock_code: 股票代码
            report_type: 报告类型
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量

        Returns:
            财务报告列表
        """
        where_clauses = ["f.stockCode = $stock_code"]
        params = {"stock_code": stock_code, "limit": limit}

        if report_type:
            where_clauses.append("f.reportType = $report_type")
            params["report_type"] = report_type.value

        if start_date:
            where_clauses.append("f.reportDate >= $start_date")
            params["start_date"] = start_date.isoformat()

        if end_date:
            where_clauses.append("f.reportDate <= $end_date")
            params["end_date"] = end_date.isoformat()

        where_clause = " AND ".join(where_clauses)

        query = f"""
            MATCH (f:FinancialReport)
            WHERE {where_clause}
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, params)
        return [neo4j_to_financial_report(r["f"]) for r in result]

    def get_financial_trends(
        self,
        stock_code: str,
        indicators: List[str],
        periods: int = 8,
    ) -> Dict[str, List[float]]:
        """
        获取财务指标趋势

        Args:
            stock_code: 股票代码
            indicators: 指标列表
            periods: 期数

        Returns:
            指标趋势数据
        """
        query = """
            MATCH (f:FinancialReport {stockCode: $stock_code})
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT $periods
        """
        result = self.neo4j.execute_query(
            query,
            {"stock_code": stock_code, "periods": periods}
        )

        trends = {indicator: [] for indicator in indicators}
        report_dates = []

        for record in reversed(result):  # 按时间正序
            report = record["f"]
            report_dates.append(report.get("reportDate"))
            for indicator in indicators:
                value = report.get(indicator)
                trends[indicator].append(value if value is not None else 0)

        trends["report_dates"] = report_dates
        return trends

    def get_industry_comparison(
        self,
        stock_code: str,
        indicators: List[str],
    ) -> Dict[str, Any]:
        """
        获取行业对比数据

        Args:
            stock_code: 股票代码
            indicators: 指标列表

        Returns:
            行业对比数据
        """
        # 获取公司所属行业
        company_query = """
            MATCH (c:Company {stockCode: $stock_code})-[:BELONGS_TO]->(i:Industry)
            RETURN i.name as industry
        """
        company_result = self.neo4j.execute_query(company_query, {"stock_code": stock_code})
        if not company_result:
            return {}

        industry = company_result[0]["industry"]

        # 获取行业平均值
        avg_query = """
            MATCH (c:Company)-[:BELONGS_TO]->(i:Industry {name: $industry})
            MATCH (c)-[:HAS_REPORT]->(f:FinancialReport)
            WITH c, max(f.reportDate) as latest_date
            MATCH (c)-[:HAS_REPORT]->(f:FinancialReport {reportDate: latest_date})
            RETURN
                avg(f.peRatio) as avg_pe,
                avg(f.pbRatio) as avg_pb,
                avg(f.roe) as avg_roe,
                avg(f.netMargin) as avg_net_margin,
                count(c) as company_count
        """
        avg_result = self.neo4j.execute_query(avg_query, {"industry": industry})

        # 获取公司数据
        company_data_query = """
            MATCH (c:Company {stockCode: $stock_code})-[:HAS_REPORT]->(f:FinancialReport)
            WITH c, max(f.reportDate) as latest_date
            MATCH (c)-[:HAS_REPORT]->(f:FinancialReport {reportDate: latest_date})
            RETURN f
        """
        company_data_result = self.neo4j.execute_query(
            company_data_query,
            {"stock_code": stock_code}
        )

        company_data = {}
        if company_data_result:
            report = company_data_result[0]["f"]
            for indicator in indicators:
                company_data[indicator] = report.get(indicator)

        industry_avg = {}
        if avg_result:
            avg_data = avg_result[0]
            industry_avg = {
                "pe_ratio": avg_data.get("avg_pe"),
                "pb_ratio": avg_data.get("avg_pb"),
                "roe": avg_data.get("avg_roe"),
                "net_margin": avg_data.get("avg_net_margin"),
                "company_count": avg_data.get("company_count"),
            }

        return {
            "industry": industry,
            "company_data": company_data,
            "industry_avg": industry_avg,
        }

    def create_financial_report(
        self,
        report: FinancialReportCreate,
    ) -> Optional[FinancialReport]:
        """
        创建财务报告

        Args:
            report: 财务报告创建模型

        Returns:
            创建的财务报告模型
        """
        # 检查是否已存在
        existing = self.find_by_stock_code_and_date(
            report.stock_code,
            report.report_date,
            report.report_type,
        )
        if existing:
            logger.warning(
                f"Financial report for {report.stock_code} on {report.report_date} already exists"
            )
            return existing

        properties = financial_report_to_neo4j(
            FinancialReport(**report.dict())
        )
        result = self.create(properties)
        if result:
            # 创建公司与报告的关系
            self._create_company_report_relationship(
                report.stock_code,
                properties
            )
            return neo4j_to_financial_report(result)
        return None

    def _create_company_report_relationship(
        self,
        stock_code: str,
        report_properties: Dict[str, Any],
    ):
        """
        创建公司与报告的关系

        Args:
            stock_code: 股票代码
            report_properties: 报告属性
        """
        query = """
            MATCH (c:Company {stockCode: $stock_code})
            MATCH (f:FinancialReport {stockCode: $stock_code, reportDate: $report_date})
            CREATE (c)-[:HAS_REPORT]->(f)
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stock_code": stock_code,
                    "report_date": report_properties.get("reportDate"),
                }
            )
        except Exception as e:
            logger.error(f"Failed to create company-report relationship: {e}")

    def batch_import(self, reports: List[FinancialReportCreate]) -> int:
        """
        批量导入财务报告

        Args:
            reports: 财务报告列表

        Returns:
            导入的报告数量
        """
        count = 0
        for report in reports:
            if self.create_financial_report(report):
                count += 1
        return count
