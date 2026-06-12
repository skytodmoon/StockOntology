"""
TimescaleDB 客户端

专门用于时序数据存储和查询，继承自 PostgreSQL 客户端。
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from loguru import logger

from app.config import settings
from .postgres_client import PostgresClient


class TimescaleClient(PostgresClient):
    """TimescaleDB 客户端 - 专门处理时序数据"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
    ):
        """
        初始化 TimescaleDB 客户端

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
        super().__init__(
            host=host or settings.TIMESCALE_HOST,
            port=port or settings.TIMESCALE_PORT,
            user=user or settings.TIMESCALE_USER,
            password=password or settings.TIMESCALE_PASSWORD,
            database=database or settings.TIMESCALE_DB,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
        )

    @property
    def connection_url(self) -> str:
        """获取 TimescaleDB 连接 URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def init_database(self):
        """初始化 TimescaleDB 数据库"""
        self.init_timescaledb()
        self.create_stock_tables()

    def create_stock_tables(self):
        """创建股票相关的时序表"""
        # 创建股票日K线表
        daily_table_sql = """
            CREATE TABLE IF NOT EXISTS stock_daily (
                stock_code TEXT NOT NULL,
                trade_date DATE NOT NULL,
                open NUMERIC(10, 2) NOT NULL,
                high NUMERIC(10, 2) NOT NULL,
                low NUMERIC(10, 2) NOT NULL,
                close NUMERIC(10, 2) NOT NULL,
                volume BIGINT NOT NULL,
                amount NUMERIC(20, 2) NOT NULL,
                change_pct NUMERIC(6, 2),
                turnover_rate NUMERIC(6, 2),
                pe_ratio NUMERIC(10, 2),
                pb_ratio NUMERIC(10, 2),
                dividend_yield NUMERIC(6, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.create_table(daily_table_sql)
        self.create_hypertable("stock_daily", "trade_date", chunk_time_interval="1 month")

        # 创建股票分钟K线表
        minute_table_sql = """
            CREATE TABLE IF NOT EXISTS stock_minute (
                stock_code TEXT NOT NULL,
                trade_time TIMESTAMPTZ NOT NULL,
                open NUMERIC(10, 2) NOT NULL,
                high NUMERIC(10, 2) NOT NULL,
                low NUMERIC(10, 2) NOT NULL,
                close NUMERIC(10, 2) NOT NULL,
                volume BIGINT NOT NULL,
                amount NUMERIC(20, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.create_table(minute_table_sql)
        self.create_hypertable("stock_minute", "trade_time", chunk_time_interval="1 day")

        # 创建大盘指数表
        index_table_sql = """
            CREATE TABLE IF NOT EXISTS market_index (
                index_code TEXT NOT NULL,
                trade_date DATE NOT NULL,
                open NUMERIC(12, 2) NOT NULL,
                high NUMERIC(12, 2) NOT NULL,
                low NUMERIC(12, 2) NOT NULL,
                close NUMERIC(12, 2) NOT NULL,
                volume BIGINT NOT NULL,
                amount NUMERIC(20, 2) NOT NULL,
                change_pct NUMERIC(6, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.create_table(index_table_sql)
        self.create_hypertable("market_index", "trade_date", chunk_time_interval="1 month")

        logger.info("TimescaleDB stock tables created")

    def insert_daily_data(self, data: List[Dict[str, Any]]):
        """
        插入股票日K线数据

        Args:
            data: 股票数据列表
                - stock_code: 股票代码
                - trade_date: 交易日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                - amount: 成交额
                - change_pct: 涨跌幅
                - turnover_rate: 换手率
                - pe_ratio: 市盈率
                - pb_ratio: 市净率
                - dividend_yield: 股息率
        """
        if not data:
            return 0

        query = """
            INSERT INTO stock_daily (
                stock_code, trade_date, open, high, low, close,
                volume, amount, change_pct, turnover_rate,
                pe_ratio, pb_ratio, dividend_yield
            ) VALUES (
                :stock_code, :trade_date, :open, :high, :low, :close,
                :volume, :amount, :change_pct, :turnover_rate,
                :pe_ratio, :pb_ratio, :dividend_yield
            ) ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                amount = EXCLUDED.amount,
                change_pct = EXCLUDED.change_pct,
                turnover_rate = EXCLUDED.turnover_rate,
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                dividend_yield = EXCLUDED.dividend_yield
        """
        return self.execute_many(query, data)

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取股票日K线数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            股票日K线数据列表
        """
        query = """
            SELECT
                stock_code,
                trade_date,
                open,
                high,
                low,
                close,
                volume,
                amount,
                change_pct
            FROM stock_daily
            WHERE stock_code = :stock_code
        """
        params = {"stock_code": stock_code}

        if start_date:
            query += " AND trade_date >= :start_date"
            params["start_date"] = start_date

        if end_date:
            query += " AND trade_date <= :end_date"
            params["end_date"] = end_date

        query += " ORDER BY trade_date DESC LIMIT :limit"
        params["limit"] = limit

        return self.execute_query(query, params)

    def get_minute_data(
        self,
        stock_code: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取股票分钟K线数据

        Args:
            stock_code: 股票代码
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            股票分钟K线数据列表
        """
        query = """
            SELECT
                stock_code,
                trade_time,
                open,
                high,
                low,
                close,
                volume,
                amount
            FROM stock_minute
            WHERE stock_code = :stock_code
        """
        params = {"stock_code": stock_code}

        if start_time:
            query += " AND trade_time >= :start_time"
            params["start_time"] = start_time

        if end_time:
            query += " AND trade_time <= :end_time"
            params["end_time"] = end_time

        query += " ORDER BY trade_time DESC LIMIT :limit"
        params["limit"] = limit

        return self.execute_query(query, params)

    def get_index_data(
        self,
        index_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取大盘指数数据

        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            大盘指数数据列表
        """
        query = """
            SELECT
                index_code,
                trade_date,
                open,
                high,
                low,
                close,
                volume,
                amount,
                change_pct
            FROM market_index
            WHERE index_code = :index_code
        """
        params = {"index_code": index_code}

        if start_date:
            query += " AND trade_date >= :start_date"
            params["start_date"] = start_date

        if end_date:
            query += " AND trade_date <= :end_date"
            params["end_date"] = end_date

        query += " ORDER BY trade_date DESC LIMIT :limit"
        params["limit"] = limit

        return self.execute_query(query, params)

    def get_price_statistics(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        获取股票价格统计数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            统计数据字典
        """
        query = """
            SELECT
                MIN(low) as min_price,
                MAX(high) as max_price,
                AVG(close) as avg_price,
                FIRST_VALUE(close) OVER (ORDER BY trade_date) as first_close,
                LAST_VALUE(close) OVER (ORDER BY trade_date) as last_close,
                SUM(volume) as total_volume,
                SUM(amount) as total_amount,
                COUNT(*) as trade_days
            FROM stock_daily
            WHERE stock_code = :stock_code
            AND trade_date BETWEEN :start_date AND :end_date
        """
        result = self.execute_query(query, {
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
        })

        if result:
            data = result[0]
            # 计算收益率
            first_close = data.get("first_close")
            last_close = data.get("last_close")
            if first_close and last_close and first_close != 0:
                data["return_rate"] = round((last_close - first_close) / first_close * 100, 2)
            else:
                data["return_rate"] = None
            return data
        return {}

    def get_moving_average(
        self,
        stock_code: str,
        window: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取移动平均线数据

        Args:
            stock_code: 股票代码
            window: 窗口大小（天数）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            移动平均线数据列表
        """
        query = f"""
            SELECT
                stock_code,
                trade_date,
                close,
                AVG(close) OVER (
                    PARTITION BY stock_code
                    ORDER BY trade_date
                    ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW
                ) as ma_{window}
            FROM stock_daily
            WHERE stock_code = :stock_code
        """
        params = {"stock_code": stock_code}

        if start_date:
            query += " AND trade_date >= :start_date"
            params["start_date"] = start_date

        if end_date:
            query += " AND trade_date <= :end_date"
            params["end_date"] = end_date

        query += " ORDER BY trade_date DESC"

        return self.execute_query(query, params)

    def get_recent_data(self, stock_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取最近N天的股票数据

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            股票数据列表
        """
        query = """
            SELECT
                stock_code,
                trade_date,
                open,
                high,
                low,
                close,
                volume,
                amount,
                change_pct
            FROM stock_daily
            WHERE stock_code = :stock_code
            ORDER BY trade_date DESC
            LIMIT :days
        """
        return self.execute_query(query, {"stock_code": stock_code, "days": days})

    def batch_get_recent_data(
        self,
        stock_codes: List[str],
        days: int = 30,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量获取多只股票最近N天的数据

        Args:
            stock_codes: 股票代码列表
            days: 天数

        Returns:
            股票数据字典，key为股票代码
        """
        query = """
            SELECT
                stock_code,
                trade_date,
                open,
                high,
                low,
                close,
                volume,
                amount,
                change_pct
            FROM stock_daily
            WHERE stock_code IN :stock_codes
            ORDER BY stock_code, trade_date DESC
        """
        result = self.execute_query(query, {"stock_codes": tuple(stock_codes)})

        grouped = {}
        for row in result:
            code = row["stock_code"]
            if code not in grouped:
                grouped[code] = []
            if len(grouped[code]) < days:
                grouped[code].append(row)

        return grouped


# 全局客户端实例
_timescale_client = None


def get_timescale_client() -> TimescaleClient:
    """
    获取 TimescaleDB 客户端单例

    Returns:
        TimescaleClient: TimescaleDB 客户端实例
    """
    global _timescale_client
    if _timescale_client is None:
        _timescale_client = TimescaleClient()
    return _timescale_client
