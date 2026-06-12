"""
腾讯数据源

通过腾讯财经API获取数据。
特点：
- 不容易封IP
- 数据稳定
- 无需第三方库
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
from loguru import logger

from .base import DataSource


class TencentDataSource(DataSource):
    """腾讯数据源"""

    priority = 20  # 优先级第二
    name = "tencent"
    request_interval = 0.8

    # 腾讯财经API
    API_QUOTE = "https://web.sqt.gtimg.cn/q="
    API_KLINE = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    def _get_market_code(self, stock_code: str) -> str:
        """
        获取腾讯格式的市场代码

        Args:
            stock_code: 股票代码

        Returns:
            市场代码 (sh/sz)
        """
        if stock_code.startswith(("6", "9", "5")):
            return "sh"
        return "sz"

    def get_stock_list(self, market: str = "all") -> List[Dict[str, Any]]:
        """
        获取股票列表

        注意：腾讯API不直接提供股票列表，需要从其他数据源获取

        Args:
            market: 市场类型

        Returns:
            股票列表
        """
        # 腾讯API不提供股票列表接口
        return []

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
        try:
            market = self._get_market_code(stock_code)
            symbol = f"{market}{stock_code}"

            # 日期处理
            if not end_date:
                end_date = date.today().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (date.today() - timedelta(days=limit * 2)).strftime("%Y-%m-%d")

            params = {
                "_var": "kline_dayqfq",
                "param": f"{symbol},day,,,{limit},qfq",
                "r": "0.123456789",
            }

            data = self._request_json(self.API_KLINE, params=params)
            if data and "data" in data:
                stock_data = data["data"].get(symbol, {})
                day_data = stock_data.get("day", [])

                results = []
                for item in day_data:
                    if len(item) >= 6:
                        results.append({
                            "stock_code": stock_code,
                            "trade_date": item[0],
                            "open": float(item[1]),
                            "close": float(item[2]),
                            "high": float(item[3]),
                            "low": float(item[4]),
                            "volume": float(item[5]),
                            "amount": float(item[6]) if len(item) > 6 else 0,
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
        results = []

        try:
            # 构建查询字符串
            symbols = []
            for code in stock_codes:
                market = self._get_market_code(code)
                symbols.append(f"{market}{code}")

            url = f"{self.API_QUOTE}{'~'.join(symbols)}"
            response = self._request(url)

            if response:
                text = response.text
                # 解析腾讯格式的数据
                # 格式: v_sh600000="1~浦发银行~600000~..."
                lines = text.strip().split('\n')
                for line in lines:
                    if '~' in line:
                        parts = line.split('~')
                        if len(parts) >= 35:
                            results.append({
                                "code": parts[2],
                                "name": parts[1],
                                "price": float(parts[3]),
                                "prev_close": float(parts[4]),
                                "open": float(parts[5]),
                                "volume": float(parts[6]),
                                "high": float(parts[33]) if len(parts) > 33 else 0,
                                "low": float(parts[34]) if len(parts) > 34 else 0,
                                "amount": float(parts[37]) if len(parts) > 37 else 0,
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
        quotes = self.get_realtime_quote([stock_code])
        return quotes[0] if quotes else None
