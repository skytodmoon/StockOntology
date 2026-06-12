"""
新闻舆情采集器

提供新闻和舆情数据的采集功能。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from .base_collector import BaseCollector


class NewsCollector(BaseCollector):
    """新闻舆情采集器"""

    def __init__(self, name: str = "NewsCollector", config: Dict[str, Any] = None):
        """
        初始化新闻采集器

        Args:
            name: 采集器名称
            config: 配置参数
        """
        super().__init__(name, config)
        self._sources = config.get("sources", ["eastmoney", "sina"]) if config else ["eastmoney", "sina"]

    def collect(
        self,
        keyword: str = None,
        stock_code: str = None,
        limit: int = 100,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        采集新闻数据

        Args:
            keyword: 搜索关键词
            stock_code: 股票代码
            limit: 返回数量
            **kwargs: 其他参数

        Returns:
            新闻数据列表
        """
        logger.info(f"Collecting news data")

        all_news = []

        for source in self._sources:
            try:
                if source == "eastmoney":
                    news = self._collect_from_eastmoney(keyword, stock_code, limit)
                elif source == "sina":
                    news = self._collect_from_sina(keyword, stock_code, limit)
                else:
                    logger.warning(f"Unknown news source: {source}")
                    continue

                all_news.extend(news)
                logger.info(f"Collected {len(news)} news from {source}")

            except Exception as e:
                logger.error(f"Failed to collect from {source}: {e}")

        return all_news[:limit]

    def _collect_from_eastmoney(
        self,
        keyword: str = None,
        stock_code: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        从东方财富采集新闻

        Args:
            keyword: 搜索关键词
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            新闻列表
        """
        try:
            import akshare as ak

            news_list = []

            if stock_code:
                # 获取个股新闻
                try:
                    df = ak.stock_news_em(symbol=stock_code)
                    if df is not None and not df.empty:
                        for _, row in df.head(limit).iterrows():
                            item = {
                                "title": str(row.get('新闻标题', '')),
                                "content": str(row.get('新闻内容', '')),
                                "source": "eastmoney",
                                "url": str(row.get('新闻链接', '')),
                                "publishTime": str(row.get('发布时间', '')),
                                "stockCode": stock_code,
                                "keywords": keyword or "",
                            }
                            if self.validate_data(item):
                                news_list.append(item)
                except Exception as e:
                    logger.warning(f"Failed to get stock news: {e}")

            else:
                # 获取财经新闻
                try:
                    df = ak.stock_news_em(symbol="财经")
                    if df is not None and not df.empty:
                        for _, row in df.head(limit).iterrows():
                            item = {
                                "title": str(row.get('新闻标题', '')),
                                "content": str(row.get('新闻内容', '')),
                                "source": "eastmoney",
                                "url": str(row.get('新闻链接', '')),
                                "publishTime": str(row.get('发布时间', '')),
                                "keywords": keyword or "",
                            }
                            if self.validate_data(item):
                                news_list.append(item)
                except Exception as e:
                    logger.warning(f"Failed to get financial news: {e}")

            return news_list

        except ImportError:
            logger.error("AKShare not installed")
            return []
        except Exception as e:
            logger.error(f"Eastmoney collection failed: {e}")
            return []

    def _collect_from_sina(
        self,
        keyword: str = None,
        stock_code: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        从新浪财经采集新闻

        Args:
            keyword: 搜索关键词
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            新闻列表
        """
        try:
            import akshare as ak

            news_list = []

            # 获取新浪财经新闻
            try:
                df = ak.stock_info_global_sina()
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        news_list.append({
                            "title": str(row.get('title', '')),
                            "content": str(row.get('content', '')),
                            "source": "sina",
                            "url": str(row.get('url', '')),
                            "publishTime": str(row.get('create_time', '')),
                            "keywords": keyword or "",
                        })
            except Exception as e:
                logger.warning(f"Failed to get sina news: {e}")

            return news_list

        except ImportError:
            logger.error("AKShare not installed")
            return []
        except Exception as e:
            logger.error(f"Sina collection failed: {e}")
            return []

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证新闻数据

        Args:
            data: 待验证的数据

        Returns:
            数据是否有效
        """
        required_fields = ["title", "source"]

        for field in required_fields:
            if field not in data or data[field] is None:
                return False

        # 标题不能为空
        if not data.get("title", "").strip():
            return False

        return True

    def collect_hot_topics(self) -> List[Dict[str, Any]]:
        """
        采集热门话题

        Returns:
            热门话题列表
        """
        try:
            import akshare as ak

            topics = []

            # 获取热门概念
            try:
                df = ak.stock_board_concept_name_em()
                if df is not None and not df.empty:
                    for _, row in df.head(20).iterrows():
                        topics.append({
                            "type": "concept",
                            "name": str(row.get('板块名称', '')),
                            "changePct": float(row.get('涨跌幅', 0) or 0),
                            "leaderStock": str(row.get('领涨股票', '')),
                        })
            except Exception as e:
                logger.warning(f"Failed to get hot concepts: {e}")

            # 获取热门行业
            try:
                df = ak.stock_board_industry_name_em()
                if df is not None and not df.empty:
                    for _, row in df.head(20).iterrows():
                        topics.append({
                            "type": "industry",
                            "name": str(row.get('板块名称', '')),
                            "changePct": float(row.get('涨跌幅', 0) or 0),
                            "leaderStock": str(row.get('领涨股票', '')),
                        })
            except Exception as e:
                logger.warning(f"Failed to get hot industries: {e}")

            return topics

        except ImportError:
            logger.error("AKShare not installed")
            return []
        except Exception as e:
            logger.error(f"Hot topics collection failed: {e}")
            return []
