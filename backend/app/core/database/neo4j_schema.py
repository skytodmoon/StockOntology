"""
Neo4j Schema 定义

定义图数据库的节点类型、关系类型、索引和约束。
"""

from typing import List, Dict, Any
from loguru import logger


# 节点标签
class NodeLabels:
    """节点标签常量"""
    COMPANY = "Company"
    INDUSTRY = "Industry"
    FINANCIAL_REPORT = "FinancialReport"
    MARKET_EVENT = "MarketEvent"
    INVESTOR = "Investor"
    STOCK = "Stock"
    INDEX = "Index"
    SECTOR = "Sector"


# 关系类型
class RelationshipTypes:
    """关系类型常量"""
    BELONGS_TO = "BELONGS_TO"
    COMPETES_WITH = "COMPETES_WITH"
    SUPPLY_TO = "SUPPLY_TO"
    IMPACTS = "IMPACTS"
    HOLDS = "HOLDS"
    HAS_REPORT = "HAS_REPORT"
    CORRELATED_WITH = "CORRELATED_WITH"
    CAUSED_BY = "CAUSED_BY"
    SUB_INDUSTRY_OF = "SUB_INDUSTRY_OF"
    SUPPLY_CHAIN = "SUPPLY_CHAIN"
    PARTNERS_WITH = "PARTNERS_WITH"


# 索引定义
INDEXES: List[Dict[str, Any]] = [
    # Company 索引
    {
        "label": NodeLabels.COMPANY,
        "property": "stockCode",
        "name": "idx_company_stock_code",
    },
    {
        "label": NodeLabels.COMPANY,
        "property": "stockName",
        "name": "idx_company_stock_name",
    },
    {
        "label": NodeLabels.COMPANY,
        "property": "market",
        "name": "idx_company_market",
    },
    {
        "label": NodeLabels.COMPANY,
        "property": "industry",
        "name": "idx_company_industry",
    },
    # Industry 索引
    {
        "label": NodeLabels.INDUSTRY,
        "property": "code",
        "name": "idx_industry_code",
    },
    {
        "label": NodeLabels.INDUSTRY,
        "property": "name",
        "name": "idx_industry_name",
    },
    {
        "label": NodeLabels.INDUSTRY,
        "property": "level",
        "name": "idx_industry_level",
    },
    # FinancialReport 索引
    {
        "label": NodeLabels.FINANCIAL_REPORT,
        "property": "stockCode",
        "name": "idx_financial_stock_code",
    },
    {
        "label": NodeLabels.FINANCIAL_REPORT,
        "property": "reportDate",
        "name": "idx_financial_report_date",
    },
    {
        "label": NodeLabels.FINANCIAL_REPORT,
        "property": "reportType",
        "name": "idx_financial_report_type",
    },
    # MarketEvent 索引
    {
        "label": NodeLabels.MARKET_EVENT,
        "property": "eventId",
        "name": "idx_event_id",
    },
    {
        "label": NodeLabels.MARKET_EVENT,
        "property": "eventType",
        "name": "idx_event_type",
    },
    {
        "label": NodeLabels.MARKET_EVENT,
        "property": "eventDate",
        "name": "idx_event_date",
    },
    {
        "label": NodeLabels.MARKET_EVENT,
        "property": "impactLevel",
        "name": "idx_event_impact_level",
    },
    # Investor 索引
    {
        "label": NodeLabels.INVESTOR,
        "property": "investorId",
        "name": "idx_investor_id",
    },
    {
        "label": NodeLabels.INVESTOR,
        "property": "name",
        "name": "idx_investor_name",
    },
    {
        "label": NodeLabels.INVESTOR,
        "property": "investorType",
        "name": "idx_investor_type",
    },
]


# 唯一约束
UNIQUE_CONSTRAINTS: List[Dict[str, Any]] = [
    {
        "label": NodeLabels.COMPANY,
        "property": "stockCode",
        "name": "constraint_company_stock_code_unique",
    },
    {
        "label": NodeLabels.INDUSTRY,
        "property": "code",
        "name": "constraint_industry_code_unique",
    },
    {
        "label": NodeLabels.MARKET_EVENT,
        "property": "eventId",
        "name": "constraint_event_id_unique",
    },
    {
        "label": NodeLabels.INVESTOR,
        "property": "investorId",
        "name": "constraint_investor_id_unique",
    },
]


# 复合索引
COMPOSITE_INDEXES: List[Dict[str, Any]] = [
    {
        "label": NodeLabels.FINANCIAL_REPORT,
        "properties": ["stockCode", "reportDate", "reportType"],
        "name": "idx_financial_stock_date_type",
    },
    {
        "label": NodeLabels.MARKET_EVENT,
        "properties": ["eventType", "eventDate"],
        "name": "idx_event_type_date",
    },
]


# 全文索引
FULLTEXT_INDEXES: List[Dict[str, Any]] = [
    {
        "name": "ft_company_search",
        "labels": [NodeLabels.COMPANY],
        "properties": ["stockName", "description"],
    },
    {
        "name": "ft_event_search",
        "labels": [NodeLabels.MARKET_EVENT],
        "properties": ["title", "content"],
    },
    {
        "name": "ft_investor_search",
        "labels": [NodeLabels.INVESTOR],
        "properties": ["name", "description"],
    },
]


def get_create_index_queries() -> List[str]:
    """
    获取创建索引的 Cypher 查询

    Returns:
        Cypher 查询列表
    """
    queries = []

    # 普通索引
    for index in INDEXES:
        query = f"""
            CREATE INDEX {index['name']} IF NOT EXISTS
            FOR (n:{index['label']})
            ON (n.{index['property']})
        """
        queries.append(query.strip())

    # 复合索引
    for index in COMPOSITE_INDEXES:
        props = ", ".join([f"n.{p}" for p in index["properties"]])
        query = f"""
            CREATE INDEX {index['name']} IF NOT EXISTS
            FOR (n:{index['label']})
            ON ({props})
        """
        queries.append(query.strip())

    return queries


def get_create_constraint_queries() -> List[str]:
    """
    获取创建约束的 Cypher 查询

    Returns:
        Cypher 查询列表
    """
    queries = []

    for constraint in UNIQUE_CONSTRAINTS:
        query = f"""
            CREATE CONSTRAINT {constraint['name']} IF NOT EXISTS
            FOR (n:{constraint['label']})
            REQUIRE n.{constraint['property']} IS UNIQUE
        """
        queries.append(query.strip())

    return queries


def get_create_fulltext_index_queries() -> List[str]:
    """
    获取创建全文索引的 Cypher 查询

    Returns:
        Cypher 查询列表
    """
    queries = []

    for index in FULLTEXT_INDEXES:
        labels = ", ".join(index["labels"])
        properties = ", ".join(index["properties"])
        query = f"""
            CREATE FULLTEXT INDEX {index['name']} IF NOT EXISTS
            FOR (n:{labels})
            ON EACH [{properties}]
        """
        queries.append(query.strip())

    return queries


def get_init_schema_queries() -> List[str]:
    """
    获取初始化 Schema 的所有查询

    Returns:
        Cypher 查询列表
    """
    queries = []
    queries.extend(get_create_constraint_queries())
    queries.extend(get_create_index_queries())
    queries.extend(get_create_fulltext_index_queries())
    return queries


def print_schema():
    """打印 Schema 信息"""
    print("=" * 60)
    print("Neo4j Schema Definition")
    print("=" * 60)

    print("\nNode Labels:")
    for attr in dir(NodeLabels):
        if not attr.startswith("_"):
            print(f"  - {getattr(NodeLabels, attr)}")

    print("\nRelationship Types:")
    for attr in dir(RelationshipTypes):
        if not attr.startswith("_"):
            print(f"  - {getattr(RelationshipTypes, attr)}")

    print(f"\nIndexes: {len(INDEXES)}")
    for index in INDEXES:
        print(f"  - {index['name']}: {index['label']}.{index['property']}")

    print(f"\nUnique Constraints: {len(UNIQUE_CONSTRAINTS)}")
    for constraint in UNIQUE_CONSTRAINTS:
        print(f"  - {constraint['name']}: {constraint['label']}.{constraint['property']}")

    print(f"\nComposite Indexes: {len(COMPOSITE_INDEXES)}")
    for index in COMPOSITE_INDEXES:
        print(f"  - {index['name']}: {index['label']}.{', '.join(index['properties'])}")

    print(f"\nFulltext Indexes: {len(FULLTEXT_INDEXES)}")
    for index in FULLTEXT_INDEXES:
        print(f"  - {index['name']}: {', '.join(index['labels'])}")

    print("=" * 60)


if __name__ == "__main__":
    print_schema()
