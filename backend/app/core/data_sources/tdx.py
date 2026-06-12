"""
通达信数据源

通过 mootdx 库获取数据。
特点：
- 不容易封IP
- 数据稳定
- 需要安装 mootdx 库
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
from loguru import logger

from .base import DataSource


class TDXDataSource(DataSource):
    """通达信数据源"""

    priority = 10  # 优先级最高
    name = "tdx"
    request_interval = 0.5  # 较短的请求间隔

    def __init__(self):
        """初始化通达信数据源"""
        super().__init__()
        self._api = None
        self._try_init_api()

    def _try_init_api(self):
        """尝试初始化API"""
        try:
            from mootdx.quotes import Quotes
            # 使用标准行情接口
            self._api = Quotes.factory(market='std')
            logger.info(f"[{self.name}] 初始化成功")
        except ImportError:
            logger.warning(f"[{self.name}] mootdx 未安装，请运行: pip install mootdx")
            self._api = None
        except Exception as e:
            logger.warning(f"[{self.name}] 初始化失败: {e}")
            self._api = None

    def _get_market(self, stock_code: str) -> int:
        """
        获取市场代码

        Args:
            stock_code: 股票代码

        Returns:
            市场代码 (0=深市, 1=沪市)
        """
        if stock_code.startswith(("6", "9", "5")):
            return 1  # 沪市
        return 0  # 深市

    def get_stock_list(self, market: str = "all") -> List[Dict[str, Any]]:
        """
        获取股票列表

        Args:
            market: 市场类型 (sh/sz/bj/all)

        Returns:
            股票列表
        """
        if not self._api:
            return []

        results = []

        try:
            # 获取沪市股票
            if market in ["all", "sh"]:
                data = self._api.stocks(market=1)
                if data is not None and not data.empty:
                    for _, row in data.iterrows():
                        code = str(row.get('code', ''))
                        # 过滤指数和基金
                        if code.startswith(('5', '6')):
                            results.append({
                                "code": code,
                                "name": row.get('name', ''),
                                "market": "sh",
                            })

            # 获取深市股票
            if market in ["all", "sz"]:
                data = self._api.stocks(market=0)
                if data is not None and not data.empty:
                    for _, row in data.iterrows():
                        code = str(row.get('code', ''))
                        # 过滤指数和基金
                        if code.startswith(('0', '3')):
                            results.append({
                                "code": code,
                                "name": row.get('name', ''),
                                "market": "sz",
                            })

            logger.info(f"[{self.name}] 获取股票列表: {len(results)} 只")

        except Exception as e:
            logger.error(f"[{self.name}] 获取股票列表失败: {e}")

        return results

    def get_daily_kline(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取日K线数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量

        Returns:
            K线数据列表
        """
        if not self._api:
            return []

        try:
            market = self._get_market(stock_code)

            # 日期处理
            if not end_date:
                end_date = date.today().strftime("%Y%m%d")
            if not start_date:
                start_date = (date.today() - timedelta(days=limit * 2)).strftime("%Y%m%d")

            # 获取K线数据
            data = self._api.bars(
                code=stock_code,
                frequency=9,  # 日K
                start=0,
                offset=limit
            )

            if data is not None and not data.empty:
                results = []
                for _, row in data.iterrows():
                    results.append({
                        "stock_code": stock_code,
                        "trade_date": str(row.get('datetime', ''))[:10],
                        "open": float(row.get('open', 0)),
                        "close": float(row.get('close', 0)),
                        "high": float(row.get('high', 0)),
                        "low": float(row.get('low', 0)),
                        "volume": float(row.get('volume', 0)),
                        "amount": float(row.get('amount', 0)),
                    })
                return results

        except Exception as e:
            logger.error(f"[{self.name}] 获取K线数据失败 ({stock_code}): {e}")

        return []

    def get_realtime_quote(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取实时行情

        Args:
            stock_codes: 股票代码列表

        Returns:
            实时行情列表
        """
        if not self._api:
            return []

        results = []

        try:
            for code in stock_codes:
                market = self._get_market(code)
                data = self._api.quotes(code=code)

                if data is not None and not data.empty:
                    for _, row in data.iterrows():
                        results.append({
                            "code": code,
                            "name": row.get('name', ''),
                            "price": float(row.get('price', 0)),
                            "open": float(row.get('open', 0)),
                            "high": float(row.get('high', 0)),
                            "low": float(row.get('low', 0)),
                            "volume": float(row.get('volume', 0)),
                            "amount": float(row.get('amount', 0)),
                            "prev_close": float(row.get('last_close', 0)),
                        })

        except Exception as e:
            logger.error(f"[{self.name}] 获取实时行情失败: {e}")

        return results

    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码

        Returns:
            股票信息
        """
        if not self._api:
            return None

        try:
            market = self._get_market(stock_code)
            data = self._api.quotes(code=stock_code)

            if data is not None and not data.empty:
                row = data.iloc[0]
                return {
                    "code": stock_code,
                    "name": row.get('name', ''),
                    "price": float(row.get('price', 0)),
                    "open": float(row.get('open', 0)),
                    "high": float(row.get('high', 0)),
                    "low": float(row.get('low', 0)),
                    "volume": float(row.get('volume', 0)),
                    "amount": float(row.get('amount', 0)),
                    "prev_close": float(row.get('last_close', 0)),
                }

        except Exception as e:
            logger.error(f"[{self.name}] 获取股票信息失败 ({stock_code}): {e}")

        return None
