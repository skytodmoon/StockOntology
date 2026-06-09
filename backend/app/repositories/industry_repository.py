"""
行业数据仓库

提供行业数据的访问方法。
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from .base_repository import BaseRepository
from app.models.industry import (
    Industry,
    IndustryCreate,
    IndustryUpdate,
    industry_to_neo4j,
    neo4j_to_industry,
)


class IndustryRepository(BaseRepository[Industry]):
    """行业数据仓库"""

    def __init__(self):
        super().__init__("Industry")

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        order_desc: bool = False,
    ) -> List[Industry]:
        """
        查找所有行业并转换为 Industry 模型
        """
        results = super().find_all(skip=skip, limit=limit, order_by=order_by, order_desc=order_desc)
        return [neo4j_to_industry(r) for r in results]

    def find_by_code(self, code: str) -> Optional[Industry]:
        """
        根据行业代码查找行业

        Args:
            code: 行业代码

        Returns:
            行业模型
        """
        result = self.find_one_by_property("code", code)
        if result:
            return neo4j_to_industry(result)
        return None

    def find_by_name(self, name: str) -> Optional[Industry]:
        """
        根据行业名称查找行业

        Args:
            name: 行业名称

        Returns:
            行业模型
        """
        result = self.find_one_by_property("name", name)
        if result:
            return neo4j_to_industry(result)
        return None

    def find_by_level(self, level: int) -> List[Industry]:
        """
        根据级别查找行业

        Args:
            level: 行业级别

        Returns:
            行业列表
        """
        results = self.find_by_property("level", level)
        return [neo4j_to_industry(r) for r in results]

    def find_sub_industries(self, parent_code: str) -> List[Industry]:
        """
        查找子行业

        Args:
            parent_code: 上级行业代码

        Returns:
            子行业列表
        """
        results = self.find_by_property("parentCode", parent_code)
        return [neo4j_to_industry(r) for r in results]

    def get_industry_hierarchy(self) -> List[Dict[str, Any]]:
        """
        获取行业层级结构

        Returns:
            行业层级结构
        """
        query = """
            MATCH (i:Industry)
            WHERE i.parentCode IS NULL OR i.parentCode = ''
            OPTIONAL MATCH (i)<-[:SUB_INDUSTRY_OF]-(child:Industry)
            RETURN i, collect(child) as children
            ORDER BY i.code
        """
        result = self.neo4j.execute_query(query)

        hierarchy = []
        for record in result:
            industry = neo4j_to_industry(record["i"])
            children = [neo4j_to_industry(c) for c in record["children"]]
            hierarchy.append({
                "industry": industry,
                "children": children,
            })

        return hierarchy

    def get_industry_chain(self, industry_code: str) -> Dict[str, Any]:
        """
        获取产业链信息

        Args:
            industry_code: 行业代码

        Returns:
            产业链信息
        """
        # 获取上游行业
        upstream_query = """
            MATCH (i:Industry {code: $code})<-[:SUPPLY_TO]-(upstream:Industry)
            RETURN upstream
        """
        upstream_result = self.neo4j.execute_query(upstream_query, {"code": industry_code})
        upstream = [neo4j_to_industry(r["upstream"]) for r in upstream_result]

        # 获取下游行业
        downstream_query = """
            MATCH (i:Industry {code: $code})-[:SUPPLY_TO]->(downstream:Industry)
            RETURN downstream
        """
        downstream_result = self.neo4j.execute_query(downstream_query, {"code": industry_code})
        downstream = [neo4j_to_industry(r["downstream"]) for r in downstream_result]

        # 获取竞争行业
        competitor_query = """
            MATCH (i:Industry {code: $code})-[:COMPETES_WITH]-(competitor:Industry)
            RETURN competitor
        """
        competitor_result = self.neo4j.execute_query(competitor_query, {"code": industry_code})
        competitors = [neo4j_to_industry(r["competitor"]) for r in competitor_result]

        industry = self.find_by_code(industry_code)

        return {
            "industry": industry,
            "upstream": upstream,
            "downstream": downstream,
            "competitors": competitors,
        }

    def get_industry_statistics(self, industry_code: str) -> Dict[str, Any]:
        """
        获取行业统计信息

        Args:
            industry_code: 行业代码

        Returns:
            统计信息
        """
        query = """
            MATCH (i:Industry {code: $code})<-[:BELONGS_TO]-(c:Company)
            OPTIONAL MATCH (c)-[:HAS_REPORT]->(f:FinancialReport)
            WITH i, c, max(f.reportDate) as latest_report_date
            OPTIONAL MATCH (c)-[:HAS_REPORT]->(latest_f:FinancialReport {reportDate: latest_report_date})
            RETURN
                count(DISTINCT c) as company_count,
                sum(c.marketCap) as total_market_cap,
                avg(c.marketCap) as avg_market_cap,
                avg(latest_f.peRatio) as avg_pe,
                avg(latest_f.pbRatio) as avg_pb,
                avg(latest_f.roe) as avg_roe
        """
        result = self.neo4j.execute_query(query, {"code": industry_code})

        if not result:
            return {}

        record = result[0]
        return {
            "company_count": record["company_count"],
            "total_market_cap": record["total_market_cap"],
            "avg_market_cap": record["avg_market_cap"],
            "avg_pe": record["avg_pe"],
            "avg_pb": record["avg_pb"],
            "avg_roe": record["avg_roe"],
        }

    def get_top_companies(
        self,
        industry_code: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取行业龙头公司

        Args:
            industry_code: 行业代码
            limit: 返回数量

        Returns:
            公司列表
        """
        query = """
            MATCH (i:Industry {code: $code})<-[:BELONGS_TO]-(c:Company)
            RETURN c
            ORDER BY c.marketCap DESC
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"code": industry_code, "limit": limit})

        companies = []
        for record in result:
            company_data = dict(record["c"])
            companies.append(company_data)

        return companies

    def create_industry(self, industry: IndustryCreate) -> Optional[Industry]:
        """
        创建行业

        Args:
            industry: 行业创建模型

        Returns:
            创建的行业模型
        """
        # 检查是否已存在
        if self.exists(code=industry.code):
            logger.warning(f"Industry {industry.code} already exists")
            return self.find_by_code(industry.code)

        properties = industry_to_neo4j(Industry(**industry.dict()))
        result = self.create(properties)
        if result:
            return neo4j_to_industry(result)
        return None

    def update_industry(
        self,
        code: str,
        update: IndustryUpdate,
    ) -> Optional[Industry]:
        """
        更新行业

        Args:
            code: 行业代码
            update: 更新数据

        Returns:
            更新后的行业模型
        """
        industry = self.find_by_code(code)
        if not industry:
            logger.warning(f"Industry {code} not found")
            return None

        update_data = update.dict(exclude_unset=True)
        if not update_data:
            return industry

        # 转换字段名
        neo4j_update = {}
        for key, value in update_data.items():
            camel_key = "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(key.split("_"))
            )
            neo4j_update[camel_key] = value

        # 查找节点 ID
        query = """
            MATCH (n:Industry {code: $code})
            RETURN id(n) as node_id
        """
        result = self.neo4j.execute_query(query, {"code": code})
        if not result:
            return None

        node_id = str(result[0]["node_id"])
        updated = self.update(node_id, neo4j_update)
        if updated:
            return neo4j_to_industry(updated)
        return None

    def delete_industry(self, code: str) -> bool:
        """
        删除行业

        Args:
            code: 行业代码

        Returns:
            是否删除成功
        """
        query = """
            MATCH (n:Industry {code: $code})
            RETURN id(n) as node_id
        """
        result = self.neo4j.execute_query(query, {"code": code})
        if not result:
            return False

        node_id = str(result[0]["node_id"])
        return self.delete(node_id)

    def create_sub_industry_relationship(
        self,
        parent_code: str,
        child_code: str,
    ) -> bool:
        """
        创建子行业关系

        Args:
            parent_code: 上级行业代码
            child_code: 子行业代码

        Returns:
            是否创建成功
        """
        query = """
            MATCH (parent:Industry {code: $parent_code})
            MATCH (child:Industry {code: $child_code})
            CREATE (child)-[:SUB_INDUSTRY_OF]->(parent)
            RETURN parent, child
        """
        try:
            self.neo4j.execute_write(
                query,
                {"parent_code": parent_code, "child_code": child_code}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create sub-industry relationship: {e}")
            return False

    def batch_import(self, industries: List[IndustryCreate]) -> int:
        """
        批量导入行业

        Args:
            industries: 行业列表

        Returns:
            导入的行业数量
        """
        items = []
        for industry in industries:
            items.append(industry_to_neo4j(Industry(**industry.dict())))

        return self.batch_create(items)
