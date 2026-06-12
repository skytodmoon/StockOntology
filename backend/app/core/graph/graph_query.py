"""
图谱查询服务

提供知识图谱的查询功能。
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.core.database import get_neo4j_client


class GraphQuery:
    """图谱查询服务"""

    def __init__(self):
        """初始化图谱查询服务"""
        self._neo4j = None

    @property
    def neo4j(self):
        """获取 Neo4j 客户端"""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        执行 Cypher 查询

        Args:
            query: Cypher 查询语句
            parameters: 查询参数

        Returns:
            查询结果
        """
        return self.neo4j.execute_query(query, parameters)

    def get_company_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取公司信息

        Args:
            stock_code: 股票代码

        Returns:
            公司信息
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            RETURN c
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code})
        if result:
            return dict(result[0]["c"])
        return None

    def get_company_with_industry(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取公司及其行业信息

        Args:
            stock_code: 股票代码

        Returns:
            公司和行业信息
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            RETURN c, i
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code})
        if result:
            company = dict(result[0]["c"])
            industry = result[0].get("i")
            if industry:
                company["industry_info"] = dict(industry)
            return company
        return None

    def get_company_financial_reports(
        self,
        stock_code: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取公司财务报告

        Args:
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            财务报告列表
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:HAS_REPORT]->(f:FinancialReport)
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code, "limit": limit})
        return [dict(r["f"]) for r in result]

    def get_company_investors(
        self,
        stock_code: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取公司投资者

        Args:
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            投资者列表
        """
        query = """
            MATCH (inv:Investor)-[h:HOLDS]->(c:Company {stockCode: $stockCode})
            RETURN inv, h
            ORDER BY h.shares DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code, "limit": limit})
        investors = []
        for r in result:
            investor = dict(r["inv"])
            holding = dict(r["h"])
            investor["holding"] = holding
            investors.append(investor)
        return investors

    def get_company_competitors(
        self,
        stock_code: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取公司竞争对手

        Args:
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            竞争对手列表
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:BELONGS_TO]->(i:Industry)
                  <-[:BELONGS_TO]-(competitor:Company)
            WHERE competitor <> c
            RETURN competitor
            ORDER BY competitor.marketCap DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code, "limit": limit})
        return [dict(r["competitor"]) for r in result]

    def get_company_events(
        self,
        stock_code: str,
        days: int = 30,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取影响公司的事件

        Args:
            stock_code: 股票代码
            days: 天数
            limit: 返回数量

        Returns:
            事件列表
        """
        query = """
            MATCH (e:MarketEvent)-[:IMPACTS]->(c:Company {stockCode: $stockCode})
            WHERE e.eventDate >= date() - duration({days: $days})
            RETURN e
            ORDER BY e.eventDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(
            query,
            {"stockCode": stock_code, "days": days, "limit": limit}
        )
        return [dict(r["e"]) for r in result]

    def get_industry_companies(
        self,
        industry_code: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        获取行业公司

        Args:
            industry_code: 行业代码
            limit: 返回数量

        Returns:
            公司列表
        """
        query = """
            MATCH (c:Company)-[:BELONGS_TO]->(i:Industry {code: $code})
            RETURN c
            ORDER BY c.marketCap DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"code": industry_code, "limit": limit})
        return [dict(r["c"]) for r in result]

    def get_industry_statistics(self, industry_code: str) -> Dict[str, Any]:
        """
        获取行业统计信息

        Args:
            industry_code: 行业代码

        Returns:
            统计信息
        """
        query = """
            MATCH (c:Company)-[:BELONGS_TO]->(i:Industry {code: $code})
            OPTIONAL MATCH (c)-[:HAS_REPORT]->(f:FinancialReport)
            WITH c, max(f.reportDate) as latest_date
            OPTIONAL MATCH (c)-[:HAS_REPORT]->(f:FinancialReport {reportDate: latest_date})
            RETURN
                count(DISTINCT c) as company_count,
                sum(c.marketCap) as total_market_cap,
                avg(c.marketCap) as avg_market_cap,
                avg(f.peRatio) as avg_pe,
                avg(f.pbRatio) as avg_pb,
                avg(f.roe) as avg_roe
        """
        result = self.neo4j.execute_query(query, {"code": industry_code})
        if result:
            return dict(result[0])
        return {}

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
            MATCH path = (c:Company {{stockCode: $stockCode}})-[*1..{depth}]-(related)
            WITH nodes(path) as ns, relationships(path) as rs
            UNWIND ns as n
            WITH collect(DISTINCT {{data: n, labels: labels(n), id: elementId(n)}}) as nodes, rs
            UNWIND rs as r
            WITH nodes, collect(DISTINCT {{type: type(r), id: elementId(r), 
                source: elementId(startNode(r)), target: elementId(endNode(r))}}) as relationships
            RETURN nodes, relationships
        """
        result = self.neo4j.execute_query(query, {"stockCode": stock_code})

        if not result:
            return {"nodes": [], "edges": []}

        nodes = []
        for node in result[0]["nodes"]:
            node_data = dict(node["data"])
            node_data["labels"] = node["labels"]
            node_data["id"] = node["id"]
            nodes.append(node_data)

        edges = []
        for rel in result[0]["relationships"]:
            edge_data = {
                "type": rel["type"],
                "id": rel["id"],
                "source": rel["source"],
                "target": rel["target"],
            }
            edges.append(edge_data)

        return {"nodes": nodes, "edges": edges}

    def find_path(
        self,
        start_code: str,
        end_code: str,
        max_depth: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        查找两个公司之间的路径

        Args:
            start_code: 起始公司代码
            end_code: 目标公司代码
            max_depth: 最大深度

        Returns:
            路径列表
        """
        query = f"""
            MATCH path = shortestPath(
                (a:Company {{stockCode: $startCode}})-[*..{max_depth}]-
                (b:Company {{stockCode: $endCode}})
            )
            RETURN path
        """
        result = self.neo4j.execute_query(
            query,
            {"startCode": start_code, "endCode": end_code}
        )

        paths = []
        for r in result:
            path = r["path"]
            nodes = [dict(node) for node in path.nodes]
            relationships = [dict(rel) for rel in path.relationships]
            paths.append({"nodes": nodes, "relationships": relationships})

        return paths

    def search_companies(
        self,
        keyword: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        搜索公司

        Args:
            keyword: 关键词
            limit: 返回数量

        Returns:
            公司列表
        """
        query = """
            MATCH (c:Company)
            WHERE c.stockName CONTAINS $keyword OR c.stockCode CONTAINS $keyword
            RETURN c
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"keyword": keyword, "limit": limit})
        return [dict(r["c"]) for r in result]

    def search_events(
        self,
        keyword: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        搜索事件

        Args:
            keyword: 关键词
            limit: 返回数量

        Returns:
            事件列表
        """
        query = """
            MATCH (e:MarketEvent)
            WHERE e.title CONTAINS $keyword OR e.content CONTAINS $keyword
            RETURN e
            ORDER BY e.eventDate DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"keyword": keyword, "limit": limit})
        return [dict(r["e"]) for r in result]
