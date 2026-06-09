"""
PostgreSQL/TimescaleDB 客户端

提供 PostgreSQL 连接管理，支持时序数据存储。
"""

from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from loguru import logger

from app.config import settings


class PostgresClient:
    """PostgreSQL 客户端"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
    ):
        """
        初始化 PostgreSQL 客户端

        Args:
            host: 主机地址
            port: 端口号
            user: 用户名
            password: 密码
            database: 数据库名称
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_timeout: 连接池超时时间
        """
        self.host = host or settings.POSTGRES_HOST
        self.port = port or settings.POSTGRES_PORT
        self.user = user or settings.POSTGRES_USER
        self.password = password or settings.POSTGRES_PASSWORD
        self.database = database or settings.POSTGRES_DB

        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout

    @property
    def connection_url(self) -> str:
        """获取数据库连接 URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def engine(self) -> Engine:
        """获取或创建数据库引擎"""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_pre_ping=True,
                echo=settings.APP_DEBUG,
            )
            logger.info(f"Connected to PostgreSQL at {self.host}:{self.port}/{self.database}")
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """获取或创建会话工厂"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    def close(self):
        """关闭连接"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("PostgreSQL connection closed")

    @contextmanager
    def get_session(self):
        """
        获取数据库会话上下文管理器

        Yields:
            Session: SQLAlchemy 会话
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询

        Args:
            query: SQL 查询语句
            parameters: 查询参数

        Returns:
            查询结果列表
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query), parameters or {})
            return [dict(row._mapping) for row in result]

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        执行写入操作

        Args:
            query: SQL 查询语句
            parameters: 查询参数

        Returns:
            受影响的行数
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query), parameters or {})
            connection.commit()
            return result.rowcount

    def execute_many(
        self,
        query: str,
        parameters_list: List[Dict[str, Any]],
    ) -> int:
        """
        批量执行写入操作

        Args:
            query: SQL 查询语句
            parameters_list: 参数列表

        Returns:
            受影响的行数
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query), parameters_list)
            connection.commit()
            return result.rowcount

    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """
        检查表是否存在

        Args:
            table_name: 表名
            schema: Schema 名称

        Returns:
            表是否存在
        """
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = :table_name
            )
        """
        result = self.execute_query(query, {"schema": schema, "table_name": table_name})
        return result[0]["exists"] if result else False

    def create_table(self, create_sql: str):
        """
        创建表

        Args:
            create_sql: 创建表的 SQL 语句
        """
        with self.engine.connect() as connection:
            connection.execute(text(create_sql))
            connection.commit()
            logger.info("Table created successfully")

    def get_table_info(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """
        获取表结构信息

        Args:
            table_name: 表名
            schema: Schema 名称

        Returns:
            列信息列表
        """
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table_name
            ORDER BY ordinal_position
        """
        return self.execute_query(query, {"schema": schema, "table_name": table_name})

    def init_timescaledb(self):
        """初始化 TimescaleDB 扩展"""
        try:
            self.execute_write("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            logger.info("TimescaleDB extension created")
        except Exception as e:
            logger.warning(f"TimescaleDB extension creation failed: {e}")

    def create_hypertable(
        self,
        table_name: str,
        time_column: str,
        chunk_time_interval: str = "1 day",
    ):
        """
        创建 TimescaleDB 超表

        Args:
            table_name: 表名
            time_column: 时间列名
            chunk_time_interval: 分块时间间隔
        """
        query = f"""
            SELECT create_hypertable(
                '{table_name}',
                '{time_column}',
                chunk_time_interval => INTERVAL '{chunk_time_interval}',
                if_not_exists => TRUE
            )
        """
        try:
            self.execute_write(query)
            logger.info(f"Hypertable created for {table_name}")
        except Exception as e:
            logger.warning(f"Hypertable creation failed: {e}")


# 全局客户端实例
_postgres_client: Optional[PostgresClient] = None


def get_postgres_client() -> PostgresClient:
    """
    获取 PostgreSQL 客户端单例

    Returns:
        PostgresClient: PostgreSQL 客户端实例
    """
    global _postgres_client
    if _postgres_client is None:
        _postgres_client = PostgresClient()
    return _postgres_client
