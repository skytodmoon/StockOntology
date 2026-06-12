"""
东方财富数据源

提供股票列表、行情、新闻等数据。
特点：
- 数据全面
- 容易封IP，需要严格控制请求频率
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
from loguru import logger

from .base import DataSource


class EastMoneyDataSource(DataSource):
    """东方财富数据源"""

    priority = 100  # 优先级最低
    name = "eastmoney"
    request_interval = 1.5  # 更长的请求间隔
    jitter_range = (0.5, 1.0)  # 更大的随机抖动

    # 东方财富API端点
    API_BASE = "https://push2.eastmoney.com/api/qt"
    API_QUOTE = "https://push2.eastmoney.com/api/qt/stock/get"
    API_KLINE = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    API_NEWS = "https://np-listapi.eastmoney.com/comm/web/getFastNewsList"

    def _setup_session(self):
        """配置会话"""
        super()._setup_session()
        self.session.headers.update({
            'Referer': 'https://quote.eastmoney.com/',
            'Origin': 'https://quote.eastmoney.com',
        })

    def get_stock_list(self, market: str = "all") -> List[Dict[str, Any]]:
        """
        获取股票列表

        Args:
            market: 市场类型 (sh/sz/bj/all)

        Returns:
            股票列表
        """
        # 市场代码映射
        market_map = {
            "sh": 1,   # 上交所
            "sz": 0,   # 深交所
            "bj": 0,   # 北交所（使用深交所代码）
        }

        results = []

        if market == "all":
            markets = ["sh", "sz"]
        else:
            markets = [market]

        for mkt in markets:
            try:
                # 东方财富股票列表API
                url = f"{self.API_BASE}/stock/list"
                params = {
                    "fltt": 2,
                    "invt": 2,
                    "fid": "f3",
                    "fs": f"b:{market_map.get(mkt, 1)}",
                    "fields": "f12,f14,f2,f3,f4,f5,f6",
                    "pn": 1,
                    "pz": 5000,  # 每页数量
                }

                data = self._request_json(url, params=params)
                if data and "data" in data and "diff" in data["data"]:
                    for item in data["data"]["diff"]:
                        results.append({
                            "code": item.get("f12", ""),
                            "name": item.get("f14", ""),
                            "price": item.get("f2", 0),
                            "change_pct": item.get("f3", 0),
                            "change": item.get("f4", 0),
                            "volume": item.get("f5", 0),
                            "amount": item.get("f6", 0),
                            "market": mkt,
                        })

            except Exception as e:
                logger.error(f"[{self.name}] 获取股票列表失败 ({mkt}): {e}")

        logger.info(f"[{self.name}] 获取股票列表: {len(results)} 只")
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
        try:
            # 确定市场代码
            market = "1" if stock_code.startswith(("6", "9")) else "0"
            secid = f"{market}.{stock_code}"

            # 日期处理
            if not end_date:
                end_date = date.today().strftime("%Y%m%d")
            if not start_date:
                start_date = (date.today() - timedelta(days=limit)).strftime("%Y%m%d")

            params = {
                "cb": "",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "secid": secid,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": 101,  # 日K
                "fqt": 1,    # 前复权
                "beg": start_date,
                "end": end_date,
            }

            data = self._request_json(self.API_KLINE, params=params)
            if data and "data" in data and "klines" in data["data"]:
                results = []
                for line in data["data"]["klines"]:
                    parts = line.split(",")
                    if len(parts) >= 7:
                        results.append({
                            "stock_code": stock_code,
                            "trade_date": parts[0],
                            "open": float(parts[1]),
                            "close": float(parts[2]),
                            "high": float(parts[3]),
                            "low": float(parts[4]),
                            "volume": float(parts[5]),
                            "amount": float(parts[6]),
                            "change_pct": float(parts[7]) if len(parts) > 7 else 0,
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

        # 批量获取（每次最多50个）
        batch_size = 50
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i + batch_size]

            try:
                # 构建secid列表
                secids = []
                for code in batch:
                    market = "1" if code.startswith(("6", "9")) else "0"
                    secids.append(f"{market}.{code}")

                params = {
                    "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                    "secids": ",".join(secids),
                    "fields": "f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f18",
                }

                data = self._request_json(self.API_QUOTE, params=params)
                if data and "data" in data:
                    items = data["data"]
                    if isinstance(items, list):
                        for item in items:
                            results.append({
                                "code": item.get("f12", ""),
                                "name": item.get("f14", ""),
                                "price": item.get("f2", 0),
                                "change_pct": item.get("f3", 0),
                                "change": item.get("f4", 0),
                                "volume": item.get("f5", 0),
                                "amount": item.get("f6", 0),
                                "high": item.get("f15", 0),
                                "low": item.get("f16", 0),
                                "open": item.get("f17", 0),
                                "prev_close": item.get("f18", 0),
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
        try:
            market = "1" if stock_code.startswith(("6", "9")) else "0"
            secid = f"{market}.{stock_code}"

            params = {
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "secid": secid,
                "fields": "f12,f14,f2,f3,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f11,f62,f128,f136,f115,f152",
            }

            data = self._request_json(self.API_QUOTE, params=params)
            if data and "data" in data:
                item = data["data"]
                return {
                    "code": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "price": item.get("f2", 0),
                    "change_pct": item.get("f3", 0),
                    "high": item.get("f15", 0),
                    "low": item.get("f16", 0),
                    "open": item.get("f17", 0),
                    "prev_close": item.get("f18", 0),
                    "volume": item.get("f5", 0),
                    "amount": item.get("f6", 0),
                    "total_market_value": item.get("f20", 0),
                    "circulating_market_value": item.get("f21", 0),
                    "pe_ratio": item.get("f23", 0),
                    "pb_ratio": item.get("f24", 0),
                    "total_share": item.get("f25", 0),
                    "circulating_share": item.get("f26", 0),
                }

        except Exception as e:
            logger.error(f"[{self.name}] 获取股票信息失败 ({stock_code}): {e}")

        return None

    def get_news(
        self,
        stock_code: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取新闻资讯

        Args:
            stock_code: 股票代码（可选）
            limit: 返回数量

        Returns:
            新闻列表
        """
        try:
            params = {
                "client": "web",
                "biz": "web_724",
                "fastColumn": "102",
                "sortEnd": "",
                "pageSize": limit,
            }

            data = self._request_json(self.API_NEWS, params=params)
            if data and "data" in data:
                results = []
                for item in data["data"]:
                    results.append({
                        "title": item.get("title", ""),
                        "content": item.get("digest", ""),
                        "source": "eastmoney",
                        "url": item.get("url", ""),
                        "publish_time": item.get("showtime", ""),
                        "keywords": "",
                    })
                return results

        except Exception as e:
            logger.error(f"[{self.name}] 获取新闻失败: {e}")

        return []
