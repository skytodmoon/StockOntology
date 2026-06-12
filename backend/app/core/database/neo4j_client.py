"""
Neo4j 图数据库客户端

提供 Neo4j 连接管理、会话管理和常用查询操作。
"""

from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from neo4j import GraphDatabase, Driver, Session, ManagedTransaction
from neo4j.time import DateTime, Date, Time
from loguru import logger

from app.config import settings


def _serialize_value(value: Any) -> Any:
    """
    序列化 Neo4j 返回的值，处理特殊类型
    
    Args:
        value: 要序列化的值
        
    Returns:
        可序列化的值
    """
    if isinstance(value, (DateTime, Date, Time)):
        return str(value)
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    else:
        return value


class Neo4jClient:
    """Neo4j 客户端"""

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        database: str = None,
        max_connection_pool: int = None,
        connection_timeout: int = None,
    ):
        """
        初始化 Neo4j 客户端

        Args:
            uri: Neo4j 连接 URI
            user: 用户名
            password: 密码
            database: 数据库名称
            max_connection_pool: 最大连接池大小
            connection_timeout: 连接超时时间（秒）
        """
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.database = database or settings.NEO4J_DATABASE
        self.max_connection_pool = max_connection_pool or settings.NEO4J_MAX_CONNECTION_POOL
        self.connection_timeout = connection_timeout or settings.NEO4J_CONNECTION_TIMEOUT

        self._driver: Optional[Driver] = None

    @property
    def driver(self) -> Driver:
        """获取或创建驱动实例"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self.max_connection_pool,
                connection_timeout=self.connection_timeout,
            )
            logger.info(f"Connected to Neo4j at {self.uri}")
        return self._driver

    def close(self):
        """关闭连接"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @contextmanager
    def get_session(self, database: str = None):
        """
        获取数据库会话上下文管理器

        Args:
            database: 数据库名称，默认使用配置的数据库

        Yields:
            Session: Neo4j 会话
        """
        db = database or self.database
        session = self.driver.session(database=db)
        try:
            yield session
        finally:
            session.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: str = None,
    ) -> List[Dict[str, Any]]:
        """
        执行 Cypher 查询

        Args:
            query: Cypher 查询语句
            parameters: 查询参数
            database: 数据库名称

        Returns:
            查询结果列表
        """
        with self.get_session(database) as session:
            result = session.run(query, parameters or {})
            return [_serialize_value(record.data()) for record in result]

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: str = None,
    ) -> Any:
        """
        执行写入操作

        Args:
            query: Cypher 查询语句
            parameters: 查询参数
            database: 数据库名称

        Returns:
            写入结果
        """
        with self.get_session(database) as session:
            result = session.execute_write(
                lambda tx: tx.run(query, parameters or {}).data()
            )
            return _serialize_value(result)

    def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: str = None,
    ) -> List[Dict[str, Any]]:
        """
        执行读取操作

        Args:
            query: Cypher 查询语句
            parameters: 查询参数
            database: 数据库名称

        Returns:
            查询结果列表
        """
        with self.get_session(database) as session:
            result = session.execute_read(
                lambda tx: tx.run(query, parameters or {}).data()
            )
            return _serialize_value(result)

    def create_indexes(self):
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX company_code IF NOT EXISTS FOR (c:Company) ON (c.stockCode)",
            "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.stockName)",
            "CREATE INDEX industry_code IF NOT EXISTS FOR (i:Industry) ON (i.code)",
            "CREATE INDEX industry_name IF NOT EXISTS FOR (i:Industry) ON (i.name)",
            "CREATE INDEX event_id IF NOT EXISTS FOR (e:MarketEvent) ON (e.eventId)",
            "CREATE INDEX event_date IF NOT EXISTS FOR (e:MarketEvent) ON (e.eventDate)",
            "CREATE INDEX investor_id IF NOT EXISTS FOR (inv:Investor) ON (inv.investorId)",
            "CREATE INDEX report_date IF NOT EXISTS FOR (f:FinancialReport) ON (f.reportDate)",
        ]

        for index_query in indexes:
            try:
                self.execute_write(index_query)
                logger.info(f"Created index: {index_query.split(' IF NOT EXISTS')[0].split('INDEX ')[1]}")
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")

    def create_constraints(self):
        """创建数据库约束"""
        constraints = [
            "CREATE CONSTRAINT company_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.stockCode IS UNIQUE",
            "CREATE CONSTRAINT industry_unique IF NOT EXISTS FOR (i:Industry) REQUIRE i.code IS UNIQUE",
            "CREATE CONSTRAINT event_unique IF NOT EXISTS FOR (e:MarketEvent) REQUIRE e.eventId IS UNIQUE",
            "CREATE CONSTRAINT investor_unique IF NOT EXISTS FOR (inv:Investor) REQUIRE inv.investorId IS UNIQUE",
        ]

        for constraint_query in constraints:
            try:
                self.execute_write(constraint_query)
                logger.info(f"Created constraint: {constraint_query.split(' IF NOT EXISTS')[0].split('CONSTRAINT ')[1]}")
            except Exception as e:
                logger.warning(f"Constraint creation failed: {e}")

    def init_database(self):
        """初始化数据库（创建索引和约束）"""
        logger.info("Initializing Neo4j database...")
        self.create_constraints()
        self.create_indexes()
        logger.info("Neo4j database initialized")

    def get_node_count(self, label: str) -> int:
        """获取节点数量"""
        query = f"MATCH (n:{label}) RETURN count(n) as count"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0

    def get_relationship_count(self, rel_type: str) -> int:
        """获取关系数量"""
        query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {}

        # 获取所有节点标签
        labels_query = "CALL db.labels()"
        labels = self.execute_query(labels_query)
        stats["labels"] = [record["label"] for record in labels]

        # 获取每种标签的节点数量
        stats["node_counts"] = {}
        for label in stats["labels"]:
            stats["node_counts"][label] = self.get_node_count(label)

        # 获取所有关系类型
        rel_types_query = "CALL db.relationshipTypes()"
        rel_types = self.execute_query(rel_types_query)
        stats["relationship_types"] = [record["relationshipType"] for record in rel_types]

        # 获取每种关系类型的数量
        stats["relationship_counts"] = {}
        for rel_type in stats["relationship_types"]:
            stats["relationship_counts"][rel_type] = self.get_relationship_count(rel_type)

        return stats


# 全局客户端实例
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """
    获取 Neo4j 客户端单例

    Returns:
        Neo4jClient: Neo4j 客户端实例
    """
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client
