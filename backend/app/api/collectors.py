"""
数据采集 API

提供数据采集的管理接口。
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.core.collectors import CollectorManager
from app.core.collectors.market_collector import MarketDataCollector
from app.core.collectors.financial_collector import FinancialDataCollector
from app.core.collectors.news_collector import NewsCollector

router = APIRouter()


class CollectorResponse(BaseModel):
    """采集器响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


# 创建采集器管理器实例
_collector_manager = None


def get_collector_manager() -> CollectorManager:
    """获取采集器管理器单例"""
    global _collector_manager
    if _collector_manager is None:
        _collector_manager = CollectorManager()
        # 注册采集器
        _collector_manager.register(MarketDataCollector)
        _collector_manager.register(FinancialDataCollector)
        _collector_manager.register(NewsCollector)
    return _collector_manager


@router.get("/status", response_model=CollectorResponse)
async def get_collector_status():
    """获取采集器状态"""
    try:
        manager = get_collector_manager()
        status = manager.get_status()
        return CollectorResponse(data=status)
    except Exception as e:
        logger.error(f"Failed to get collector status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classes", response_model=CollectorResponse)
async def get_collector_classes():
    """获取可用的采集器类"""
    try:
        manager = get_collector_manager()
        classes = manager.list_classes()
        return CollectorResponse(data=classes)
    except Exception as e:
        logger.error(f"Failed to get collector classes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market/collect", response_model=CollectorResponse)
async def collect_market_data(
    stock_codes: List[str] = None,
    start_date: str = None,
    end_date: str = None,
):
    """采集行情数据"""
    try:
        manager = get_collector_manager()

        # 创建采集器
        collector = manager.get("MarketDataCollector")
        if collector is None:
            collector = manager.create("MarketDataCollector", "MarketDataCollector")

        # 执行采集
        data = collector.start(
            stock_codes=stock_codes,
            start_date=start_date,
            end_date=end_date,
        )

        return CollectorResponse(
            data={
                "count": len(data) if isinstance(data, list) else 0,
                "samples": data[:5] if isinstance(data, list) else [],
            },
            message=f"Collected {len(data) if isinstance(data, list) else 0} market data items"
        )
    except Exception as e:
        logger.error(f"Failed to collect market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market/realtime", response_model=CollectorResponse)
async def collect_realtime_data(stock_codes: List[str]):
    """采集实时行情"""
    try:
        manager = get_collector_manager()

        # 创建采集器
        collector = manager.get("MarketDataCollector")
        if collector is None:
            collector = manager.create("MarketDataCollector", "MarketDataCollector")

        # 执行采集
        data = collector.collect_realtime(stock_codes)

        return CollectorResponse(
            data=data,
            message=f"Collected {len(data)} realtime data items"
        )
    except Exception as e:
        logger.error(f"Failed to collect realtime data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market/stock-list", response_model=CollectorResponse)
async def collect_stock_list():
    """采集股票列表"""
    try:
        manager = get_collector_manager()

        # 创建采集器
        collector = manager.get("MarketDataCollector")
        if collector is None:
            collector = manager.create("MarketDataCollector", "MarketDataCollector")

        # 执行采集
        data = collector.collect_stock_list()

        return CollectorResponse(
            data={
                "count": len(data),
                "samples": data[:10],
            },
            message=f"Collected {len(data)} stocks"
        )
    except Exception as e:
        logger.error(f"Failed to collect stock list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/financial/collect", response_model=CollectorResponse)
async def collect_financial_data(
    stock_codes: List[str] = None,
    report_type: str = "annual",
):
    """采集财务数据"""
    try:
        manager = get_collector_manager()

        # 创建采集器
        collector = manager.get("FinancialDataCollector")
        if collector is None:
            collector = manager.create("FinancialDataCollector", "FinancialDataCollector")

        # 执行采集
        data = collector.start(
            stock_codes=stock_codes,
            report_type=report_type,
        )

        return CollectorResponse(
            data={
                "count": len(data) if isinstance(data, list) else 0,
                "samples": data[:5] if isinstance(data, list) else [],
            },
            message=f"Collected {len(data) if isinstance(data, list) else 0} financial data items"
        )
    except Exception as e:
        logger.error(f"Failed to collect financial data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/financial/company-info", response_model=CollectorResponse)
async def collect_company_info(stock_codes: List[str]):
    """采集公司信息"""
    try:
        manager = get_collector_manager()

        # 创建采集器
        collector = manager.get("FinancialDataCollector")
        if collector is None:
            collector = manager.create("FinancialDataCollector", "FinancialDataCollector")

        # 执行采集
        data = collector.collect_company_info(stock_codes)

        return CollectorResponse(
            data=data,
            message=f"Collected {len(data)} company info items"
        )
    except Exception as e:
        logger.error(f"Failed to collect company info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news/collect", response_model=CollectorResponse)
async def collect_news(
    keyword: str = None,
    stock_code: str = None,
    limit: int = 100,
):
    """采集新闻数据"""
    try:
        manager = get_collector_manager()

        # 创建采集器
        collector = manager.get("NewsCollector")
        if collector is None:
            collector = manager.create("NewsCollector", "NewsCollector")

        # 执行采集
        data = collector.start(
            keyword=keyword,
            stock_code=stock_code,
            limit=limit,
        )

        return CollectorResponse(
            data={
                "count": len(data) if isinstance(data, list) else 0,
                "samples": data[:5] if isinstance(data, list) else [],
            },
            message=f"Collected {len(data) if isinstance(data, list) else 0} news items"
        )
    except Exception as e:
        logger.error(f"Failed to collect news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news/hot-topics", response_model=CollectorResponse)
async def collect_hot_topics():
    """采集热门话题"""
    try:
        manager = get_collector_manager()

        # 创建采集器
        collector = manager.get("NewsCollector")
        if collector is None:
            collector = manager.create("NewsCollector", "NewsCollector")

        # 执行采集
        data = collector.collect_hot_topics()

        return CollectorResponse(
            data=data,
            message=f"Collected {len(data)} hot topics"
        )
    except Exception as e:
        logger.error(f"Failed to collect hot topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-all", response_model=CollectorResponse)
async def stop_all_collectors():
    """停止所有采集器"""
    try:
        manager = get_collector_manager()
        manager.stop_all()
        return CollectorResponse(message="All collectors stopped")
    except Exception as e:
        logger.error(f"Failed to stop collectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=CollectorResponse)
async def clear_collectors():
    """清空所有采集器"""
    try:
        manager = get_collector_manager()
        manager.clear()
        return CollectorResponse(message="All collectors cleared")
    except Exception as e:
        logger.error(f"Failed to clear collectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
