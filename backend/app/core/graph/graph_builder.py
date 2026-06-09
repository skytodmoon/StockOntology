"""
图谱构建器

提供知识图谱的构建功能。
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.core.database import get_neo4j_client
from app.core.database.neo4j_schema import get_init_schema_queries


class GraphBuilder:
    """图谱构建器"""

    def __init__(self):
        """初始化图谱构建器"""
        self._neo4j = None

    @property
    def neo4j(self):
        """获取 Neo4j 客户端"""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    def init_schema(self):
        """初始化数据库 Schema"""
        queries = get_init_schema_queries()
        for query in queries:
            try:
                self.neo4j.execute_write(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Schema init warning: {e}")
        logger.info("Schema initialized")

    def create_company(self, company_data: Dict[str, Any]) -> bool:
        """
        创建公司节点

        Args:
            company_data: 公司数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (c:Company {stockCode: $stockCode})
            SET c += $properties
            RETURN c
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": company_data.get("stockCode"),
                    "properties": company_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create company: {e}")
            return False

    def create_industry(self, industry_data: Dict[str, Any]) -> bool:
        """
        创建行业节点

        Args:
            industry_data: 行业数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (i:Industry {code: $code})
            SET i += $properties
            RETURN i
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "code": industry_data.get("code"),
                    "properties": industry_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create industry: {e}")
            return False

    def create_financial_report(self, report_data: Dict[str, Any]) -> bool:
        """
        创建财务报告节点

        Args:
            report_data: 财务报告数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (f:FinancialReport {
                stockCode: $stockCode,
                reportDate: $reportDate,
                reportType: $reportType
            })
            SET f += $properties
            RETURN f
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": report_data.get("stockCode"),
                    "reportDate": report_data.get("reportDate"),
                    "reportType": report_data.get("reportType"),
                    "properties": report_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create financial report: {e}")
            return False

    def create_event(self, event_data: Dict[str, Any]) -> bool:
        """
        创建事件节点

        Args:
            event_data: 事件数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (e:MarketEvent {eventId: $eventId})
            SET e += $properties
            RETURN e
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "eventId": event_data.get("eventId"),
                    "properties": event_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return False

    def create_investor(self, investor_data: Dict[str, Any]) -> bool:
        """
        创建投资者节点

        Args:
            investor_data: 投资者数据

        Returns:
            是否创建成功
        """
        query = """
            MERGE (inv:Investor {investorId: $investorId})
            SET inv += $properties
            RETURN inv
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "investorId": investor_data.get("investorId"),
                    "properties": investor_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create investor: {e}")
            return False

    def create_company_industry_relationship(
        self,
        stock_code: str,
        industry_code: str,
    ) -> bool:
        """
        创建公司-行业关系

        Args:
            stock_code: 股票代码
            industry_code: 行业代码

        Returns:
            是否创建成功
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            MATCH (i:Industry {code: $industryCode})
            MERGE (c)-[:BELONGS_TO]->(i)
            RETURN c, i
        """
        try:
            self.neo4j.execute_write(
                query,
                {"stockCode": stock_code, "industryCode": industry_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create company-industry relationship: {e}")
            return False

    def create_company_report_relationship(
        self,
        stock_code: str,
        report_date: str,
        report_type: str,
    ) -> bool:
        """
        创建公司-报告关系

        Args:
            stock_code: 股票代码
            report_date: 报告日期
            report_type: 报告类型

        Returns:
            是否创建成功
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            MATCH (f:FinancialReport {
                stockCode: $stockCode,
                reportDate: $reportDate,
                reportType: $reportType
            })
            MERGE (c)-[:HAS_REPORT]->(f)
            RETURN c, f
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": stock_code,
                    "reportDate": report_date,
                    "reportType": report_type,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create company-report relationship: {e}")
            return False

    def create_company_competitor_relationship(
        self,
        stock_code1: str,
        stock_code2: str,
        competition_level: str = "Medium",
    ) -> bool:
        """
        创建公司竞争关系

        Args:
            stock_code1: 股票代码1
            stock_code2: 股票代码2
            competition_level: 竞争级别

        Returns:
            是否创建成功
        """
        query = """
            MATCH (c1:Company {stockCode: $stockCode1})
            MATCH (c2:Company {stockCode: $stockCode2})
            MERGE (c1)-[:COMPETES_WITH {level: $level}]->(c2)
            MERGE (c2)-[:COMPETES_WITH {level: $level}]->(c1)
            RETURN c1, c2
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode1": stock_code1,
                    "stockCode2": stock_code2,
                    "level": competition_level,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create competitor relationship: {e}")
            return False

    def create_company_supply_relationship(
        self,
        supplier_code: str,
        customer_code: str,
        supply_type: str = "Product",
    ) -> bool:
        """
        创建供应链关系

        Args:
            supplier_code: 供应商股票代码
            customer_code: 客户股票代码
            supply_type: 供应类型

        Returns:
            是否创建成功
        """
        query = """
            MATCH (supplier:Company {stockCode: $supplierCode})
            MATCH (customer:Company {stockCode: $customerCode})
            MERGE (supplier)-[:SUPPLY_TO {type: $type}]->(customer)
            RETURN supplier, customer
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "supplierCode": supplier_code,
                    "customerCode": customer_code,
                    "type": supply_type,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create supply relationship: {e}")
            return False

    def create_investor_holding_relationship(
        self,
        investor_id: str,
        stock_code: str,
        holding_data: Dict[str, Any],
    ) -> bool:
        """
        创建投资者持仓关系

        Args:
            investor_id: 投资者ID
            stock_code: 股票代码
            holding_data: 持仓数据

        Returns:
            是否创建成功
        """
        query = """
            MATCH (inv:Investor {investorId: $investorId})
            MATCH (c:Company {stockCode: $stockCode})
            MERGE (inv)-[:HOLDS]->(c)
            SET inv += $properties
            RETURN inv, c
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "investorId": investor_id,
                    "stockCode": stock_code,
                    "properties": holding_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create investor-holding relationship: {e}")
            return False

    def create_event_impact_relationship(
        self,
        event_id: str,
        target_code: str,
        target_type: str,
        impact_data: Dict[str, Any],
    ) -> bool:
        """
        创建事件影响关系

        Args:
            event_id: 事件ID
            target_code: 目标代码
            target_type: 目标类型（Company/Industry）
            impact_data: 影响数据

        Returns:
            是否创建成功
        """
        query = f"""
            MATCH (e:MarketEvent {{eventId: $eventId}})
            MATCH (t:{target_type} {{stockCode: $targetCode}})
            MERGE (e)-[:IMPACTS]->(t)
            SET e += $properties
            RETURN e, t
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "eventId": event_id,
                    "targetCode": target_code,
                    "properties": impact_data,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create event impact: {e}")
            return False

    def create_industry_hierarchy(
        self,
        parent_code: str,
        child_code: str,
    ) -> bool:
        """
        创建行业层级关系

        Args:
            parent_code: 上级行业代码
            child_code: 子行业代码

        Returns:
            是否创建成功
        """
        query = """
            MATCH (parent:Industry {code: $parentCode})
            MATCH (child:Industry {code: $childCode})
            MERGE (child)-[:SUB_INDUSTRY_OF]->(parent)
            RETURN parent, child
        """
        try:
            self.neo4j.execute_write(
                query,
                {"parentCode": parent_code, "childCode": child_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create industry hierarchy: {e}")
            return False

    def batch_create_companies(self, companies: List[Dict[str, Any]]) -> int:
        """
        批量创建公司

        Args:
            companies: 公司数据列表

        Returns:
            创建成功的数量
        """
        count = 0
        for company in companies:
            if self.create_company(company):
                count += 1
        return count

    def batch_create_industries(self, industries: List[Dict[str, Any]]) -> int:
        """
        批量创建行业

        Args:
            industries: 行业数据列表

        Returns:
            创建成功的数量
        """
        count = 0
        for industry in industries:
            if self.create_industry(industry):
                count += 1
        return count

    def batch_create_financial_reports(self, reports: List[Dict[str, Any]]) -> int:
        """
        批量创建财务报告

        Args:
            reports: 财务报告数据列表

        Returns:
            创建成功的数量
        """
        count = 0
        for report in reports:
            if self.create_financial_report(report):
                count += 1
        return count
