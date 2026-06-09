"""
财务数据采集器

提供公司财务数据的采集功能。
"""

from typing import Any, Dict, List, Optional
from datetime import date
from loguru import logger

from .base_collector import BaseCollector


class FinancialDataCollector(BaseCollector):
    """财务数据采集器"""

    def __init__(self, name: str = "FinancialDataCollector", config: Dict[str, Any] = None):
        """
        初始化财务数据采集器

        Args:
            name: 采集器名称
            config: 配置参数
        """
        super().__init__(name, config)
        self._data_source = config.get("data_source", "tushare") if config else "tushare"
        self._token = config.get("token", "") if config else ""

    def collect(
        self,
        stock_codes: List[str] = None,
        report_type: str = "annual",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        采集财务数据

        Args:
            stock_codes: 股票代码列表
            report_type: 报告类型（annual/quarterly）
            **kwargs: 其他参数

        Returns:
            财务数据列表
        """
        logger.info(f"Collecting financial data from {self._data_source}")

        if self._data_source == "tushare":
            return self._collect_from_tushare(stock_codes, report_type)
        elif self._data_source == "akshare":
            return self._collect_from_akshare(stock_codes, report_type)
        else:
            logger.error(f"Unknown data source: {self._data_source}")
            return []

    def _collect_from_tushare(
        self,
        stock_codes: List[str],
        report_type: str,
    ) -> List[Dict[str, Any]]:
        """
        从 Tushare 采集财务数据

        Args:
            stock_codes: 股票代码列表
            report_type: 报告类型

        Returns:
            财务数据列表
        """
        try:
            import tushare as ts

            if not self._token:
                logger.warning("Tushare token not configured")
                return []

            pro = ts.pro_api(self._token)
            data = []

            # 如果没有指定股票代码，获取部分股票
            if not stock_codes:
                stock_list = pro.stock_basic(exchange='', list_status='L')
                stock_codes = stock_list['ts_code'].tolist()[:50]

            for code in stock_codes:
                try:
                    # 获取利润表
                    income_df = pro.income(ts_code=code)
                    # 获取资产负债表
                    balance_df = pro.balancesheet(ts_code=code)
                    # 获取现金流量表
                    cashflow_df = pro.cashflow(ts_code=code)

                    if income_df is not None and not income_df.empty:
                        for _, row in income_df.head(4).iterrows():  # 最近4期
                            report_data = {
                                "stockCode": code[:6],
                                "reportDate": str(row.get('end_date', '')),
                                "reportType": self._determine_report_type(str(row.get('end_date', ''))),
                                "revenue": float(row.get('revenue', 0) or 0),
                                "netProfit": float(row.get('n_income', 0) or 0),
                                "grossProfit": float(row.get('revenue', 0) or 0) - float(row.get('oper_cost', 0) or 0),
                            }
                            data.append(report_data)

                except Exception as e:
                    logger.warning(f"Failed to collect financial data for {code}: {e}")

            return data

        except ImportError:
            logger.error("Tushare not installed")
            return []
        except Exception as e:
            logger.error(f"Tushare collection failed: {e}")
            return []

    def _collect_from_akshare(
        self,
        stock_codes: List[str],
        report_type: str,
    ) -> List[Dict[str, Any]]:
        """
        从 AKShare 采集财务数据

        Args:
            stock_codes: 股票代码列表
            report_type: 报告类型

        Returns:
            财务数据列表
        """
        try:
            import akshare as ak

            data = []

            # 如果没有指定股票代码
            if not stock_codes:
                stock_list = ak.stock_info_a_code_name()
                stock_codes = stock_list['code'].tolist()[:30]

            for code in stock_codes:
                try:
                    # 获取财务摘要
                    df = ak.stock_financial_abstract_ths(symbol=code)
                    if df is not None and not df.empty:
                        for _, row in df.head(4).iterrows():
                            report_data = {
                                "stockCode": code,
                                "reportDate": str(row.get('报告期', '')),
                                "reportType": self._determine_report_type(str(row.get('报告期', ''))),
                                "revenue": self._safe_float(row.get('营业总收入')),
                                "netProfit": self._safe_float(row.get('净利润')),
                                "eps": self._safe_float(row.get('基本每股收益')),
                                "roe": self._safe_float(row.get('净资产收益率')),
                            }
                            data.append(report_data)

                except Exception as e:
                    logger.warning(f"Failed to collect financial data for {code}: {e}")

            return data

        except ImportError:
            logger.error("AKShare not installed")
            return []
        except Exception as e:
            logger.error(f"AKShare collection failed: {e}")
            return []

    def _determine_report_type(self, date_str: str) -> str:
        """
        确定报告类型

        Args:
            date_str: 日期字符串

        Returns:
            报告类型
        """
        if not date_str:
            return "Annual"

        try:
            if len(date_str) >= 6:
                month = int(date_str[4:6]) if len(date_str) >= 6 else 0
                if month == 3:
                    return "Q1"
                elif month == 6:
                    return "Q2"
                elif month == 9:
                    return "Q3"
                elif month == 12:
                    return "Annual"
        except (ValueError, IndexError):
            pass

        return "Annual"

    def _safe_float(self, value) -> Optional[float]:
        """
        安全转换为浮点数

        Args:
            value: 原始值

        Returns:
            浮点数或 None
        """
        if value is None or value == '' or value == '--':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证财务数据

        Args:
            data: 待验证的数据

        Returns:
            数据是否有效
        """
        required_fields = ["stockCode", "reportDate"]

        for field in required_fields:
            if field not in data or data[field] is None:
                return False

        # 验证日期格式
        report_date = data.get("reportDate", "")
        if len(str(report_date)) < 6:
            return False

        return True

    def collect_company_info(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """
        采集公司基本信息

        Args:
            stock_codes: 股票代码列表

        Returns:
            公司信息列表
        """
        try:
            import akshare as ak

            companies = []
            for code in stock_codes:
                try:
                    df = ak.stock_individual_info_em(symbol=code)
                    if df is not None and not df.empty:
                        info = {}
                        for _, row in df.iterrows():
                            key = str(row['item'])
                            value = row['value']
                            if key == '股票简称':
                                info['stockName'] = str(value)
                            elif key == '上市时间':
                                info['listDate'] = str(value)
                            elif key == '总股本':
                                info['totalShare'] = self._safe_float(value)
                            elif key == '流通股':
                                info['floatShare'] = self._safe_float(value)

                        info['stockCode'] = code
                        if 'stockName' in info:
                            companies.append(info)

                except Exception as e:
                    logger.warning(f"Failed to collect company info for {code}: {e}")

            return companies

        except ImportError:
            logger.error("AKShare not installed")
            return []
        except Exception as e:
            logger.error(f"Company info collection failed: {e}")
            return []
