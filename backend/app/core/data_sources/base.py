"""
数据源基类

提供统一的数据源接口和防封策略。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import date, datetime
import time
import random
import requests
from loguru import logger


class DataSource(ABC):
    """数据源基类"""

    # 数据源优先级（数字越小优先级越高）
    priority: int = 100
    # 数据源名称
    name: str = "base"
    # 请求间隔（秒）
    request_interval: float = 1.0
    # 随机抖动范围（秒）
    jitter_range: tuple = (0.1, 0.5)
    # 最大重试次数
    max_retries: int = 3
    # 超时时间（秒）
    timeout: int = 10

    def __init__(self):
        """初始化数据源"""
        self.session = requests.Session()
        self._last_request_time: float = 0
        self._setup_session()

    def _setup_session(self):
        """配置会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        })

    def _wait_for_rate_limit(self):
        """等待以满足请求间隔限制"""
        now = time.time()
        elapsed = now - self._last_request_time
        jitter = random.uniform(*self.jitter_range)
        wait_time = max(0, self.request_interval + jitter - elapsed)
        if wait_time > 0:
            time.sleep(wait_time)
        self._last_request_time = time.time()

    def _request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        发送请求（带重试和防封）

        Args:
            url: 请求URL
            method: 请求方法
            params: URL参数
            data: 请求体数据
            headers: 额外请求头
            **kwargs: 其他参数

        Returns:
            响应对象或None
        """
        self._wait_for_rate_limit()

        req_headers = {}
        if headers:
            req_headers.update(headers)

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=req_headers,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"[{self.name}] 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"[{self.name}] 请求最终失败: {url}")
                    return None

        return None

    def _request_json(
        self,
        url: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Optional[Dict]:
        """
        发送请求并返回JSON

        Args:
            url: 请求URL
            params: URL参数
            **kwargs: 其他参数

        Returns:
            JSON数据或None
        """
        response = self._request(url, params=params, **kwargs)
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"[{self.name}] JSON解析失败: {e}")
        return None

    # ========== 抽象方法 ==========

    @abstractmethod
    def get_stock_list(self, market: str = "all") -> List[Dict[str, Any]]:
        """
        获取股票列表

        Args:
            market: 市场类型 (sh/sz/bj/all)

        Returns:
            股票列表
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_realtime_quote(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取实时行情

        Args:
            stock_codes: 股票代码列表

        Returns:
            实时行情列表
        """
        pass

    @abstractmethod
    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码

        Returns:
            股票信息
        """
        pass

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
        return []

    def get_financial_report(
        self,
        stock_code: str,
        report_type: str = "balance"
    ) -> Optional[Dict[str, Any]]:
        """
        获取财务报表

        Args:
            stock_code: 股票代码
            report_type: 报表类型 (balance/income/cashflow)

        Returns:
            财务数据
        """
        return None


class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        """初始化数据源管理器"""
        self._sources: Dict[str, DataSource] = {}
        self._sorted_sources: List[DataSource] = []

    def register(self, source: DataSource):
        """
        注册数据源

        Args:
            source: 数据源实例
        """
        self._sources[source.name] = source
        self._update_sorted_sources()
        logger.info(f"注册数据源: {source.name} (优先级: {source.priority})")

    def _update_sorted_sources(self):
        """更新排序后的数据源列表"""
        self._sorted_sources = sorted(
            self._sources.values(),
            key=lambda s: s.priority
        )

    def get_source(self, name: str) -> Optional[DataSource]:
        """
        获取指定数据源

        Args:
            name: 数据源名称

        Returns:
            数据源实例
        """
        return self._sources.get(name)

    def get_best_source(self) -> Optional[DataSource]:
        """
        获取最优数据源

        Returns:
            优先级最高的数据源
        """
        return self._sorted_sources[0] if self._sorted_sources else None

    def execute_with_fallback(
        self,
        method_name: str,
        *args,
        preferred_source: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        执行方法并在失败时自动切换数据源

        Args:
            method_name: 方法名
            *args: 位置参数
            preferred_source: 首选数据源
            **kwargs: 关键字参数

        Returns:
            方法执行结果
        """
        # 确定数据源顺序
        if preferred_source and preferred_source in self._sources:
            sources = [self._sources[preferred_source]] + [
                s for s in self._sorted_sources if s.name != preferred_source
            ]
        else:
            sources = self._sorted_sources

        # 依次尝试
        for source in sources:
            try:
                method = getattr(source, method_name, None)
                if method is None:
                    continue
                result = method(*args, **kwargs)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"[{source.name}] 执行 {method_name} 失败: {e}")
                continue

        logger.error(f"所有数据源都无法执行 {method_name}")
        return None


# 全局数据源管理器
_manager: Optional[DataSourceManager] = None


def get_data_source_manager() -> DataSourceManager:
    """获取全局数据源管理器"""
    global _manager
    if _manager is None:
        _manager = DataSourceManager()
        # 注册默认数据源
        from .eastmoney import EastMoneyDataSource
        from .tencent import TencentDataSource
        from .tdx import TDXDataSource

        _manager.register(TDXDataSource())  # 优先级最高
        _manager.register(TencentDataSource())
        _manager.register(EastMoneyDataSource())  # 优先级最低（容易封IP）

    return _manager
