"""
投资者数据仓库

提供投资者数据的访问方法。
"""

from typing import Any, Dict, List, Optional
from datetime import date
from loguru import logger

from .base_repository import BaseRepository
from app.models.investor import (
    Investor,
    InvestorCreate,
    InvestorType,
    Holding,
    investor_to_neo4j,
    neo4j_to_investor,
    holding_to_neo4j,
)


class InvestorRepository(BaseRepository[Investor]):
    """投资者数据仓库"""

    def __init__(self):
        super().__init__("Investor")

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        order_desc: bool = False,
    ) -> List[Investor]:
        """
        查找所有投资者并转换为 Investor 模型
        """
        results = super().find_all(skip=skip, limit=limit, order_by=order_by, order_desc=order_desc)
        return [neo4j_to_investor(r) for r in results]

    def find_by_investor_id(self, investor_id: str) -> Optional[Investor]:
        """
        根据投资者ID查找投资者

        Args:
            investor_id: 投资者ID

        Returns:
            投资者模型
        """
        result = self.find_one_by_property("investorId", investor_id)
        if result:
            return neo4j_to_investor(result)
        return None

    def find_by_type(
        self,
        investor_type: InvestorType,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Investor]:
        """
        根据类型查找投资者

        Args:
            investor_type: 投资者类型
            skip: 跳过数量
            limit: 返回数量

        Returns:
            投资者列表
        """
        results = self.find_by_property("investorType", investor_type.value)
        return [neo4j_to_investor(r) for r in results[skip:skip + limit]]

    def search_investors(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Investor]:
        """
        搜索投资者

        Args:
            keyword: 搜索关键词
            skip: 跳过数量
            limit: 返回数量

        Returns:
            投资者列表
        """
        results = self.search(keyword, ["name", "description"], skip, limit)
        return [neo4j_to_investor(r) for r in results]

    def get_investor_holdings(
        self,
        investor_id: str,
        report_date: date = None,
    ) -> List[Dict[str, Any]]:
        """
        获取投资者持仓

        Args:
            investor_id: 投资者ID
            report_date: 报告日期

        Returns:
            持仓列表
        """
        where_clauses = ["inv.investorId = $investor_id"]
        params = {"investor_id": investor_id}

        if report_date:
            where_clauses.append("h.reportDate = $report_date")
            params["report_date"] = report_date.isoformat()

        where_clause = " AND ".join(where_clauses)

        query = f"""
            MATCH (inv:Investor)-[h:HOLDS]->(c:Company)
            WHERE {where_clause}
            RETURN inv, h, c
            ORDER BY h.shares DESC
        """
        result = self.neo4j.execute_query(query, params)

        holdings = []
        for record in result:
            investor = neo4j_to_investor(record["inv"])
            company_data = dict(record["c"])
            holding_data = dict(record["h"])

            holdings.append({
                "investor": investor,
                "company": company_data,
                "holding": holding_data,
            })

        return holdings

    def get_company_investors(
        self,
        stock_code: str,
        report_date: date = None,
        investor_type: InvestorType = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取公司的投资者

        Args:
            stock_code: 股票代码
            report_date: 报告日期
            investor_type: 投资者类型
            limit: 返回数量

        Returns:
            投资者列表
        """
        where_clauses = ["c.stockCode = $stock_code"]
        params = {"stock_code": stock_code, "limit": limit}

        if report_date:
            where_clauses.append("h.reportDate = $report_date")
            params["report_date"] = report_date.isoformat()

        if investor_type:
            where_clauses.append("inv.investorType = $investor_type")
            params["investor_type"] = investor_type.value

        where_clause = " AND ".join(where_clauses)

        query = f"""
            MATCH (inv:Investor)-[h:HOLDS]->(c:Company)
            WHERE {where_clause}
            RETURN inv, h, c
            ORDER BY h.shares DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, params)

        investors = []
        for record in result:
            investor = neo4j_to_investor(record["inv"])
            company_data = dict(record["c"])
            holding_data = dict(record["h"])

            investors.append({
                "investor": investor,
                "company": company_data,
                "holding": holding_data,
            })

        return investors

    def get_investor_behavior(self, investor_id: str) -> Dict[str, Any]:
        """
        获取投资者行为分析

        Args:
            investor_id: 投资者ID

        Returns:
            行为分析数据
        """
        # 获取持仓统计
        stats_query = """
            MATCH (inv:Investor {investorId: $investor_id})-[h:HOLDS]->(c:Company)
            WITH inv,
                 count(c) as holding_count,
                 sum(h.marketValue) as total_value,
                 avg(h.ratio) as avg_ratio
            RETURN inv, holding_count, total_value, avg_ratio
        """
        stats_result = self.neo4j.execute_query(stats_query, {"investor_id": investor_id})

        if not stats_result:
            return {}

        stats = stats_result[0]

        # 获取行业偏好
        industry_query = """
            MATCH (inv:Investor {investorId: $investor_id})-[h:HOLDS]->(c:Company)-[:BELONGS_TO]->(i:Industry)
            RETURN i.name as industry, sum(h.marketValue) as value
            ORDER BY value DESC
        """
        industry_result = self.neo4j.execute_query(industry_query, {"investor_id": investor_id})

        industry_preferences = {}
        total_value = stats.get("total_value", 0) or 1
        for record in industry_result:
            industry_preferences[record["industry"]] = record["value"] / total_value

        return {
            "investor_id": investor_id,
            "holding_count": stats.get("holding_count", 0),
            "total_market_value": stats.get("total_value", 0),
            "concentration": stats.get("avg_ratio", 0),
            "industry_preferences": industry_preferences,
        }

    def get_top_investors(
        self,
        investor_type: InvestorType = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取顶级投资者

        Args:
            investor_type: 投资者类型
            limit: 返回数量

        Returns:
            投资者列表
        """
        where_clause = ""
        params = {"limit": limit}

        if investor_type:
            where_clause = "WHERE inv.investorType = $investor_type"
            params["investor_type"] = investor_type.value

        query = f"""
            MATCH (inv:Investor)-[h:HOLDS]->(c:Company)
            {where_clause}
            WITH inv, sum(h.marketValue) as total_value
            RETURN inv, total_value
            ORDER BY total_value DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, params)

        investors = []
        for record in result:
            investor = neo4j_to_investor(record["inv"])
            investors.append({
                "investor": investor,
                "total_market_value": record["total_value"],
            })

        return investors

    def create_investor(self, investor: InvestorCreate) -> Optional[Investor]:
        """
        创建投资者

        Args:
            investor: 投资者创建模型

        Returns:
            创建的投资者模型
        """
        # 检查是否已存在
        if self.exists(investorId=investor.investor_id):
            logger.warning(f"Investor {investor.investor_id} already exists")
            return self.find_by_investor_id(investor.investor_id)

        properties = investor_to_neo4j(Investor(**investor.dict()))
        result = self.create(properties)
        if result:
            return neo4j_to_investor(result)
        return None

    def create_holding(
        self,
        investor_id: str,
        stock_code: str,
        holding: Holding,
    ) -> bool:
        """
        创建持仓关系

        Args:
            investor_id: 投资者ID
            stock_code: 股票代码
            holding: 持仓数据

        Returns:
            是否创建成功
        """
        properties = holding_to_neo4j(holding)

        query = """
            MATCH (inv:Investor {investorId: $investor_id})
            MATCH (c:Company {stockCode: $stock_code})
            CREATE (inv)-[:HOLDS $properties]->(c)
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "investor_id": investor_id,
                    "stock_code": stock_code,
                    "properties": properties,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create holding relationship: {e}")
            return False

    def update_holding(
        self,
        investor_id: str,
        stock_code: str,
        holding: Holding,
    ) -> bool:
        """
        更新持仓关系

        Args:
            investor_id: 投资者ID
            stock_code: 股票代码
            holding: 持仓数据

        Returns:
            是否更新成功
        """
        properties = holding_to_neo4j(holding)

        query = """
            MATCH (inv:Investor {investorId: $investor_id})-[h:HOLDS]->(c:Company {stockCode: $stock_code})
            SET h += $properties
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "investor_id": investor_id,
                    "stock_code": stock_code,
                    "properties": properties,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update holding relationship: {e}")
            return False

    def delete_holding(
        self,
        investor_id: str,
        stock_code: str,
    ) -> bool:
        """
        删除持仓关系

        Args:
            investor_id: 投资者ID
            stock_code: 股票代码

        Returns:
            是否删除成功
        """
        query = """
            MATCH (inv:Investor {investorId: $investor_id})-[h:HOLDS]->(c:Company {stockCode: $stock_code})
            DELETE h
        """
        try:
            self.neo4j.execute_write(
                query,
                {"investor_id": investor_id, "stock_code": stock_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete holding relationship: {e}")
            return False

    def batch_import(self, investors: List[InvestorCreate]) -> int:
        """
        批量导入投资者

        Args:
            investors: 投资者列表

        Returns:
            导入的投资者数量
        """
        count = 0
        for investor in investors:
            if self.create_investor(investor):
                count += 1
        return count
