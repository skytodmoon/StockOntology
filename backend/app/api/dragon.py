"""
龙头战法 API

提供龙头股分析、供应链查询、护城河分析等核心功能接口。
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.core.services import (
    get_company_service,
    get_market_service,
    get_concept_service,
    get_event_service,
    get_graph_service,
)

router = APIRouter(prefix="/dragon")


class DragonResponse(BaseModel):
    """龙头战法响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


class CompanyDetailResponse(BaseModel):
    """企业详情响应"""
    stock_code: str
    stock_name: Optional[str]
    market: Optional[str]
    description: Optional[str]
    employees: Optional[int]
    is_leader: Optional[bool]
    moat_level: Optional[int]
    moat_type: Optional[str]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    roe: Optional[float]
    industries: List[Dict[str, str]] = []
    concepts: List[Dict[str, str]] = []
    suppliers: List[Dict[str, str]] = []
    customers: List[Dict[str, str]] = []
    latest_price: Optional[Dict[str, Any]] = None


class DragonStockResponse(BaseModel):
    """龙头股响应"""
    stock_code: str
    stock_name: str
    industry: Optional[str]
    moat_level: Optional[int]
    moat_type: Optional[str]
    market_cap: Optional[int]
    roe: Optional[float]


class SupplyChainResponse(BaseModel):
    """供应链响应"""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []


class MarketDataResponse(BaseModel):
    """行情数据响应"""
    stock_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    change_pct: Optional[float]


class ConceptStockResponse(BaseModel):
    """概念成分股响应"""
    stock_code: str
    stock_name: str
    concept: str
    is_leader: bool
    market_cap: Optional[int]


@router.get("/stocks", response_model=DragonResponse)
async def get_dragon_stocks(
    industry_code: Optional[str] = Query(None, description="行业代码"),
):
    """
    获取龙头股列表

    Args:
        industry_code: 行业代码（可选），如 IND001(半导体)

    Returns:
        龙头股列表
    """
    try:
        service = get_company_service()
        stocks = service.get_dragon_stocks(industry_code)
        return DragonResponse(data=stocks)
    except Exception as e:
        logger.error(f"Failed to get dragon stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/high-moat", response_model=DragonResponse)
async def get_high_moat_companies(
    min_moat: int = Query(4, ge=1, le=5, description="最低护城河等级"),
):
    """
    获取高护城河企业

    Args:
        min_moat: 最低护城河等级（1-5）

    Returns:
        高护城河企业列表
    """
    try:
        service = get_company_service()
        companies = service.get_hightech_moat_companies(min_moat)
        return DragonResponse(data=companies)
    except Exception as e:
        logger.error(f"Failed to get high moat companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}", response_model=DragonResponse)
async def get_company_detail(stock_code: str):
    """
    获取企业完整信息（多数据库聚合）

    Args:
        stock_code: 股票代码

    Returns:
        企业完整信息
    """
    try:
        service = get_company_service()
        detail = service.get_company_detail(stock_code)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")
        return DragonResponse(data=detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/supply-chain", response_model=DragonResponse)
async def get_supply_chain(
    stock_code: str,
    direction: str = Query("all", enum=["up", "down", "all"], description="供应链方向"),
):
    """
    获取供应链关系

    Args:
        stock_code: 股票代码
        direction: 供应链方向（up:上游, down:下游, all:全部）

    Returns:
        供应链图谱数据
    """
    try:
        service = get_company_service()
        supply_chain = service.get_supply_chain(stock_code, direction)
        return DragonResponse(data=supply_chain)
    except Exception as e:
        logger.error(f"Failed to get supply chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/graph", response_model=DragonResponse)
async def get_company_graph(
    stock_code: str,
    depth: int = Query(2, ge=1, le=4, description="图谱深度"),
):
    """
    获取企业关联图谱

    Args:
        stock_code: 股票代码
        depth: 图谱深度（1-4）

    Returns:
        企业关联图谱
    """
    try:
        service = get_graph_service()
        graph = service.get_company_graph(stock_code, depth)
        return DragonResponse(data=graph)
    except Exception as e:
        logger.error(f"Failed to get company graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/{stock_code}/daily", response_model=DragonResponse)
async def get_daily_data(
    stock_code: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    获取股票日K线数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期（格式：YYYY-MM-DD）
        limit: 返回数量限制

    Returns:
        日K线数据列表
    """
    try:
        service = get_market_service()
        data = service.get_daily_data(stock_code, start_date, end_date, limit)
        return DragonResponse(data=data)
    except Exception as e:
        logger.error(f"Failed to get daily data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/{stock_code}/recent", response_model=DragonResponse)
async def get_recent_data(
    stock_code: str,
    days: int = Query(30, ge=1, le=365, description="天数"),
):
    """
    获取最近N天股票数据

    Args:
        stock_code: 股票代码
        days: 天数

    Returns:
        股票数据列表
    """
    try:
        service = get_market_service()
        data = service.get_recent_data(stock_code, days)
        return DragonResponse(data=data)
    except Exception as e:
        logger.error(f"Failed to get recent data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/{stock_code}/statistics", response_model=DragonResponse)
async def get_price_statistics(
    stock_code: str,
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
):
    """
    获取股票价格统计

    Args:
        stock_code: 股票代码
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期（格式：YYYY-MM-DD）

    Returns:
        价格统计数据
    """
    try:
        service = get_market_service()
        stats = service.get_price_statistics(stock_code, start_date, end_date)
        return DragonResponse(data=stats)
    except Exception as e:
        logger.error(f"Failed to get price statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/{stock_code}/ma", response_model=DragonResponse)
async def get_moving_average(
    stock_code: str,
    window: int = Query(20, ge=5, le=200, description="移动平均窗口"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
):
    """
    获取移动平均线数据

    Args:
        stock_code: 股票代码
        window: 移动平均窗口（天数）
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期（格式：YYYY-MM-DD）

    Returns:
        移动平均线数据
    """
    try:
        service = get_market_service()
        data = service.get_moving_average(stock_code, window, start_date, end_date)
        return DragonResponse(data=data)
    except Exception as e:
        logger.error(f"Failed to get moving average: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concepts", response_model=DragonResponse)
async def get_all_concepts():
    """
    获取所有概念板块

    Returns:
        概念板块列表
    """
    try:
        service = get_concept_service()
        concepts = service.get_all_concepts()
        return DragonResponse(data=concepts)
    except Exception as e:
        logger.error(f"Failed to get concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concept/{concept_code}/stocks", response_model=DragonResponse)
async def get_concept_stocks(concept_code: str):
    """
    获取概念成分股

    Args:
        concept_code: 概念代码（如 CON001）

    Returns:
        概念成分股列表
    """
    try:
        service = get_concept_service()
        stocks = service.get_concept_stocks(concept_code)
        return DragonResponse(data=stocks)
    except Exception as e:
        logger.error(f"Failed to get concept stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/concepts", response_model=DragonResponse)
async def get_stock_concepts(stock_code: str):
    """
    获取股票所属概念

    Args:
        stock_code: 股票代码

    Returns:
        概念列表
    """
    try:
        service = get_concept_service()
        concepts = service.get_related_concepts(stock_code)
        return DragonResponse(data=concepts)
    except Exception as e:
        logger.error(f"Failed to get stock concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=DragonResponse)
async def get_all_events(
    limit: int = Query(20, ge=1, le=100, description="数量限制"),
):
    """
    获取市场事件

    Args:
        limit: 数量限制

    Returns:
        市场事件列表
    """
    try:
        service = get_event_service()
        events = service.get_all_events(limit)
        return DragonResponse(data=events)
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_id}/impacts", response_model=DragonResponse)
async def get_event_impacts(event_id: str):
    """
    获取事件影响的股票

    Args:
        event_id: 事件ID

    Returns:
        受影响的股票列表
    """
    try:
        service = get_event_service()
        impacts = service.get_event_impacts(event_id)
        return DragonResponse(data=impacts)
    except Exception as e:
        logger.error(f"Failed to get event impacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/events", response_model=DragonResponse)
async def get_stock_events(stock_code: str):
    """
    获取影响股票的事件

    Args:
        stock_code: 股票代码

    Returns:
        事件列表
    """
    try:
        service = get_event_service()
        events = service.get_stock_events(stock_code)
        return DragonResponse(data=events)
    except Exception as e:
        logger.error(f"Failed to get stock events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis", response_model=DragonResponse)
async def get_dragon_analysis():
    """
    获取龙头战法综合分析报告

    Returns:
        综合分析报告
    """
    try:
        # 获取各服务数据
        company_service = get_company_service()
        concept_service = get_concept_service()

        # 龙头股统计
        dragons = company_service.get_dragon_stocks()
        high_moat = company_service.get_hightech_moat_companies(min_moat=4)
        concepts = concept_service.get_all_concepts()

        # 按行业统计
        industry_stats = {}
        for dragon in dragons:
            industry = dragon.get("industry", "其他")
            if industry not in industry_stats:
                industry_stats[industry] = {"count": 0, "total_market_cap": 0}
            industry_stats[industry]["count"] += 1
            industry_stats[industry]["total_market_cap"] += dragon.get("market_cap", 0)

        analysis = {
            "summary": {
                "total_dragons": len(dragons),
                "high_moat_count": len(high_moat),
                "active_concepts": len(concepts),
            },
            "industry_distribution": industry_stats,
            "top_dragons": dragons[:10],
            "hot_concepts": concepts[:5],
            "high_moat_companies": high_moat[:10],
        }

        return DragonResponse(data=analysis)
    except Exception as e:
        logger.error(f"Failed to get dragon analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
