"""
行情数据采集器

提供股票行情数据的采集功能。
支持多数据源自动切换，参考 a-stock-data 项目的设计。
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from loguru import logger

from .base_collector import BaseCollector


class MarketDataCollector(BaseCollector):
    """行情数据采集器"""

    def __init__(self, name: str = "MarketDataCollector", config: Dict[str, Any] = None):
        """
        初始化行情数据采集器

        Args:
            name: 采集器名称
            config: 配置参数
        """
        super().__init__(name, config)
        self._data_source = config.get("data_source", "auto") if config else "auto"
        self._token = config.get("token", "") if config else ""
        self._ds_manager = None

    def _get_data_source_manager(self):
        """获取数据源管理器"""
        if self._ds_manager is None:
            from app.core.data_sources import get_data_source_manager
            self._ds_manager = get_data_source_manager()
        return self._ds_manager

    def collect(
        self,
        stock_codes: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        采集行情数据

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数

        Returns:
            行情数据列表
        """
        # 使用新的数据源管理器
        if self._data_source == "auto":
            return self._collect_from_auto(stock_codes, start_date, end_date)
        elif self._data_source == "tushare":
            return self._collect_from_tushare(stock_codes, start_date, end_date)
        elif self._data_source == "akshare":
            return self._collect_from_akshare(stock_codes, start_date, end_date)
        else:
            logger.error(f"Unknown data source: {self._data_source}")
            return []

    def _collect_from_auto(
        self,
        stock_codes: List[str],
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict[str, Any]]:
        """
        使用数据源管理器自动采集

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            行情数据列表
        """
        logger.info("使用多数据源自动采集行情数据")

        try:
            manager = self._get_data_source_manager()
            all_data = []
            failed_codes = []

            # 默认日期
            if not end_date:
                end_date = date.today().isoformat()
            if not start_date:
                start_date = (date.today() - timedelta(days=30)).isoformat()

            # 如果没有指定股票代码，获取股票列表
            if not stock_codes:
                stock_list = manager.execute_with_fallback("get_stock_list")
                if stock_list:
                    stock_codes = [s["code"] for s in stock_list[:100]]  # 限制数量

            # 批量获取K线数据
            for code in (stock_codes or []):
                try:
                    kline_data = manager.execute_with_fallback(
                        "get_daily_kline",
                        code,
                        start_date.replace('-', ''),
                        end_date.replace('-', ''),
                        100
                    )
                    if kline_data:
                        all_data.extend(kline_data)
                    else:
                        failed_codes.append(code)
                except Exception as e:
                    failed_codes.append(code)
                    logger.debug(f"获取 {code} 行情失败: {e}")

            if failed_codes:
                logger.warning(f"获取行情失败: {len(failed_codes)} 只股票")

            logger.info(f"成功获取 {len(all_data)} 条行情数据")
            return all_data

        except Exception as e:
            logger.error(f"自动采集行情失败: {e}")
            return []

    def _collect_from_tushare(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        从 Tushare 采集数据

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            行情数据列表
        """
        try:
            import tushare as ts

            if not self._token:
                logger.warning("Tushare token not configured")
                return []

            pro = ts.pro_api(self._token)
            data = []

            # 如果没有指定股票代码，获取所有股票
            if not stock_codes:
                stock_list = pro.stock_basic(exchange='', list_status='L')
                stock_codes = stock_list['ts_code'].tolist()[:100]  # 限制数量

            for code in stock_codes:
                try:
                    df = pro.daily(
                        ts_code=code,
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                    )
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            data.append({
                                "stockCode": code[:6],
                                "tradeDate": row['trade_date'],
                                "open": float(row['open']),
                                "high": float(row['high']),
                                "low": float(row['low']),
                                "close": float(row['close']),
                                "volume": float(row['vol']),
                                "amount": float(row['amount']),
                                "change": float(row.get('change', 0)),
                                "changePct": float(row.get('pct_chg', 0)),
                            })
                except Exception as e:
                    logger.warning(f"Failed to collect data for {code}: {e}")

            return data

        except ImportError:
            logger.error("Tushare not installed. Install with: pip install tushare")
            return []
        except Exception as e:
            logger.error(f"Tushare collection failed: {e}")
            return []

    def _collect_from_akshare(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        从 AKShare 采集数据

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            行情数据列表
        """
        try:
            import akshare as ak
            import time

            data = []
            failed_codes = []

            # 如果没有指定股票代码，获取部分股票
            if not stock_codes:
                stock_list = ak.stock_info_a_code_name()
                stock_codes = stock_list['code'].tolist()[:50]  # 限制数量

            for i, code in enumerate(stock_codes):
                try:
                    # 添加延迟避免请求过快
                    if i > 0:
                        time.sleep(0.5)

                    df = ak.stock_zh_a_hist(
                        symbol=code,
                        period="daily",
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust="qfq",
                    )
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            item = {
                                "stockCode": code,
                                "tradeDate": str(row['日期']),
                                "open": float(row['开盘']),
                                "high": float(row['最高']),
                                "low": float(row['最低']),
                                "close": float(row['收盘']),
                                "volume": float(row['成交量']),
                                "amount": float(row['成交额']),
                                "change": float(row.get('涨跌额', 0)),
                                "changePct": float(row.get('涨跌幅', 0)),
                            }
                            if self.validate_data(item):
                                data.append(item)
                except Exception as e:
                    failed_codes.append(code)
                    logger.debug(f"Failed to collect data for {code}: {e}")

            if failed_codes:
                logger.warning(f"Failed to collect data for {len(failed_codes)} stocks: {failed_codes[:5]}...")

            return data

        except ImportError:
            logger.error("AKShare not installed. Install with: pip install akshare")
            return []
        except Exception as e:
            logger.error(f"AKShare collection failed: {e}")
            return []

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证行情数据

        Args:
            data: 待验证的数据

        Returns:
            数据是否有效
        """
        required_fields = ["stockCode", "tradeDate", "open", "high", "low", "close", "volume"]

        for field in required_fields:
            if field not in data or data[field] is None:
                return False

        # 验证价格逻辑
        if data["high"] < data["low"]:
            return False

        if data["open"] < 0 or data["close"] < 0:
            return False

        if data["volume"] < 0:
            return False

        return True

    def collect_realtime(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """
        采集实时行情

        Args:
            stock_codes: 股票代码列表

        Returns:
            实时行情数据
        """
        try:
            import akshare as ak

            data = []
            for code in stock_codes:
                try:
                    df = ak.stock_zh_a_spot_em()
                    if df is not None:
                        row = df[df['代码'] == code]
                        if not row.empty:
                            row = row.iloc[0]
                            data.append({
                                "stockCode": code,
                                "stockName": str(row['名称']),
                                "currentPrice": float(row['最新价']),
                                "change": float(row['涨跌额']),
                                "changePct": float(row['涨跌幅']),
                                "open": float(row['今开']),
                                "high": float(row['最高']),
                                "low": float(row['最低']),
                                "preClose": float(row['昨收']),
                                "volume": float(row['成交量']),
                                "amount": float(row['成交额']),
                                "time": datetime.now().isoformat(),
                            })
                except Exception as e:
                    logger.warning(f"Failed to collect realtime data for {code}: {e}")

            return data

        except ImportError:
            logger.error("AKShare not installed")
            return []
        except Exception as e:
            logger.error(f"Realtime collection failed: {e}")
            return []

    def collect_stock_list(self) -> List[Dict[str, Any]]:
        """
        采集股票列表

        Returns:
            股票列表
        """
        try:
            import akshare as ak

            df = ak.stock_info_a_code_name()
            if df is not None and not df.empty:
                stocks = []
                for _, row in df.iterrows():
                    stocks.append({
                        "stockCode": str(row['code']),
                        "stockName": str(row['name']),
                    })
                return stocks
            return []

        except ImportError:
            logger.error("AKShare not installed")
            return []
        except Exception as e:
            logger.error(f"Stock list collection failed: {e}")
            return []
