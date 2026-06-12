"""
数据源模块

提供多数据源支持，包括东方财富、通达信、腾讯等。
参考 a-stock-data 项目的设计理念：
- 多数据源优先级
- 防封策略
- 统一错误处理
"""

from .base import DataSource, DataSourceManager, get_data_source_manager
from .eastmoney import EastMoneyDataSource
from .tencent import TencentDataSource
from .tdx import TDXDataSource

__all__ = [
    "DataSource",
    "DataSourceManager",
    "get_data_source_manager",
    "EastMoneyDataSource",
    "TencentDataSource",
    "TDXDataSource",
]
