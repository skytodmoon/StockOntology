"""
公司数据仓库

提供公司数据的访问方法。
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from .base_repository import BaseRepository
from app.models.company import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    company_to_neo4j,
    neo4j_to_company,
)


class CompanyRepository(BaseRepository[Company]):
    """公司数据仓库"""

    def __init__(self):
        super().__init__("Company")

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        order_desc: bool = False,
    ) -> List[Company]:
        """
        查找所有公司并转换为 Company 模型
        """
        results = super().find_all(skip=skip, limit=limit, order_by=order_by, order_desc=order_desc)
        return [neo4j_to_company(r) for r in results]

    def find_by_stock_code(self, stock_code: str) -> Optional[Company]:
        """
        根据股票代码查找公司

        Args:
            stock_code: 股票代码

        Returns:
            公司模型
        """
        result = self.find_one_by_property("stockCode", stock_code)
        if result:
            return neo4j_to_company(result)
        return None

    def find_by_market(self, market: str) -> List[Company]:
        """
        根据市场查找公司

        Args:
            market: 市场代码（SH/SZ/BJ）

        Returns:
            公司列表
        """
        results = self.find_by_property("market", market)
        return [neo4j_to_company(r) for r in results]

    def find_by_industry(self, industry: str) -> List[Company]:
        """
        根据行业查找公司

        Args:
            industry: 行业名称

        Returns:
            公司列表
        """
        results = self.find_by_property("industry", industry)
        return [neo4j_to_company(r) for r in results]

    def search_companies(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Company]:
        """
        搜索公司

        Args:
            keyword: 搜索关键词
            skip: 跳过数量
            limit: 返回数量

        Returns:
            公司列表
        """
        results = self.search(
            keyword,
            ["stockCode", "stockName", "description"],
            skip,
            limit,
        )
        return [neo4j_to_company(r) for r in results]

    def get_companies_by_market_cap(
        self,
        min_cap: float = None,
        max_cap: float = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Company]:
        """
        根据市值范围查找公司

        Args:
            min_cap: 最小市值
            max_cap: 最大市值
            skip: 跳过数量
            limit: 返回数量

        Returns:
            公司列表
        """
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if min_cap is not None:
            where_clauses.append("n.marketCap >= $min_cap")
            params["min_cap"] = min_cap
        if max_cap is not None:
            where_clauses.append("n.marketCap <= $max_cap")
            params["max_cap"] = max_cap

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"

        query = f"""
            MATCH (n:{self.node_label})
            WHERE {where_clause}
            RETURN n
            ORDER BY n.marketCap DESC
            SKIP $skip
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, params)
        return [neo4j_to_company(r["n"]) for r in result]

    def get_companies_with_financial_report(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Company]:
        """
        获取有财务报告的公司

        Args:
            skip: 跳过数量
            limit: 返回数量

        Returns:
            公司列表
        """
        query = f"""
            MATCH (c:{self.node_label})-[:HAS_REPORT]->(f:FinancialReport)
            WITH c, max(f.reportDate) as latest_report
            RETURN c
            ORDER BY c.marketCap DESC
            SKIP $skip
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"skip": skip, "limit": limit})
        return [neo4j_to_company(r["c"]) for r in result]

    def get_company_with_details(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取公司详细信息（包含关联数据）

        Args:
            stock_code: 股票代码

        Returns:
            公司详细信息
        """
        query = """
            MATCH (c:Company {stockCode: $stock_code})
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            OPTIONAL MATCH (c)-[:HAS_REPORT]->(f:FinancialReport)
            WITH c, i, max(f.reportDate) as latest_report_date
            OPTIONAL MATCH (c)-[:HAS_REPORT]->(latest_f:FinancialReport {reportDate: latest_report_date})
            RETURN c, i, latest_f
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code})

        if not result:
            return None

        record = result[0]
        company = neo4j_to_company(record["c"])

        details = company.dict()
        if record.get("i"):
            details["industry_info"] = dict(record["i"])
        if record.get("latest_f"):
            details["latest_financial"] = dict(record["latest_f"])

        return details

    def get_company_graph(
        self,
        stock_code: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """
        获取公司关系图谱

        Args:
            stock_code: 股票代码
            depth: 关系深度

        Returns:
            图谱数据
        """
        query = f"""
            MATCH path = (c:Company {{stockCode: $stock_code}})-[*1..{depth}]-(related)
            WITH nodes(path) as ns, relationships(path) as rs
            UNWIND ns as n
            WITH collect(DISTINCT n) as nodes, rs
            UNWIND rs as r
            RETURN nodes, collect(DISTINCT r) as relationships
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code})

        if not result:
            return {"nodes": [], "edges": []}

        nodes = []
        for node in result[0]["nodes"]:
            node_data = dict(node)
            node_data["labels"] = list(node.labels)
            node_data["id"] = node.element_id
            nodes.append(node_data)

        edges = []
        for rel in result[0]["relationships"]:
            edge_data = dict(rel)
            edge_data["type"] = rel.type
            edge_data["id"] = rel.element_id
            edge_data["source"] = rel.start_node.element_id
            edge_data["target"] = rel.end_node.element_id
            edges.append(edge_data)

        return {"nodes": nodes, "edges": edges}

    def get_competitors(
        self,
        stock_code: str,
        limit: int = 10,
    ) -> List[Company]:
        """
        获取竞争对手

        Args:
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            竞争对手列表
        """
        query = """
            MATCH (c:Company {stockCode: $stock_code})-[:BELONGS_TO]->(i:Industry)
                  <-[:BELONGS_TO]-(competitor:Company)
            WHERE competitor <> c
            RETURN competitor
            ORDER BY competitor.marketCap DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code, "limit": limit})
        return [neo4j_to_company(r["competitor"]) for r in result]

    def get_investors(
        self,
        stock_code: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取机构投资者

        Args:
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            投资者列表
        """
        query = """
            MATCH (inv:Investor)-[h:HOLDS]->(c:Company {stockCode: $stock_code})
            RETURN inv, h
            ORDER BY h.shares DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code, "limit": limit})

        investors = []
        for record in result:
            investor_data = dict(record["inv"])
            holding_data = dict(record["h"])
            investor_data["holding"] = holding_data
            investors.append(investor_data)

        return investors

    def create_company(self, company: CompanyCreate) -> Optional[Company]:
        """
        创建公司

        Args:
            company: 公司创建模型

        Returns:
            创建的公司模型
        """
        # 检查是否已存在
        if self.exists(stockCode=company.stock_code):
            logger.warning(f"Company {company.stock_code} already exists")
            return self.find_by_stock_code(company.stock_code)

        properties = company_to_neo4j(Company(**company.dict()))
        result = self.create(properties)
        if result:
            return neo4j_to_company(result)
        return None

    def update_company(
        self,
        stock_code: str,
        update: CompanyUpdate,
    ) -> Optional[Company]:
        """
        更新公司

        Args:
            stock_code: 股票代码
            update: 更新数据

        Returns:
            更新后的公司模型
        """
        # 查找公司
        company = self.find_by_stock_code(stock_code)
        if not company:
            logger.warning(f"Company {stock_code} not found")
            return None

        # 更新属性
        update_data = update.dict(exclude_unset=True)
        if not update_data:
            return company

        # 转换为 Neo4j 属性格式
        neo4j_update = {}
        for key, value in update_data.items():
            # 转换字段名（snake_case -> camelCase）
            camel_key = "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(key.split("_"))
            )
            neo4j_update[camel_key] = value

        # 查找节点 ID
        query = """
            MATCH (n:Company {stockCode: $stock_code})
            RETURN id(n) as node_id
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code})
        if not result:
            return None

        node_id = str(result[0]["node_id"])
        updated = self.update(node_id, neo4j_update)
        if updated:
            return neo4j_to_company(updated)
        return None

    def delete_company(self, stock_code: str) -> bool:
        """
        删除公司

        Args:
            stock_code: 股票代码

        Returns:
            是否删除成功
        """
        query = """
            MATCH (n:Company {stockCode: $stock_code})
            RETURN id(n) as node_id
        """
        result = self.neo4j.execute_query(query, {"stock_code": stock_code})
        if not result:
            return False

        node_id = str(result[0]["node_id"])
        return self.delete(node_id)

    def batch_import(self, companies: List[CompanyCreate]) -> int:
        """
        批量导入公司

        Args:
            companies: 公司列表

        Returns:
            导入的公司数量
        """
        items = []
        for company in companies:
            items.append(company_to_neo4j(Company(**company.dict())))

        return self.batch_create(items)
