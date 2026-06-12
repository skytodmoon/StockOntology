"""
知识图谱 API

提供知识图谱的查询和管理接口。
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from loguru import logger

from app.core.graph import GraphBuilder, GraphQuery, GraphStatistics

router = APIRouter()


class GraphResponse(BaseModel):
    """图谱响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


def _get_builder():
    """获取图谱构建器"""
    return GraphBuilder()

def _get_query():
    """获取图谱查询服务"""
    return GraphQuery()

def _get_statistics():
    """获取图谱统计服务"""
    return GraphStatistics()


@router.get("/stats", response_model=GraphResponse)
async def get_graph_stats():
    """获取图谱统计信息"""
    try:
        stats = _get_statistics()
        overview = stats.get_overview()
        return GraphResponse(data=overview)
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-overview", response_model=GraphResponse)
async def get_market_overview():
    """获取市场概览"""
    try:
        stats = _get_statistics()
        overview = stats.get_market_overview()
        return GraphResponse(data=overview)
    except Exception as e:
        logger.error(f"Failed to get market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/statistics", response_model=GraphResponse)
async def get_company_statistics():
    """获取公司统计信息"""
    try:
        stats = _get_statistics()
        company_stats = stats.get_company_statistics()
        return GraphResponse(data=company_stats)
    except Exception as e:
        logger.error(f"Failed to get company statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industries/statistics", response_model=GraphResponse)
async def get_industry_statistics():
    """获取行业统计信息"""
    try:
        stats = _get_statistics()
        industry_stats = stats.get_industry_statistics()
        return GraphResponse(data=industry_stats)
    except Exception as e:
        logger.error(f"Failed to get industry statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investors/statistics", response_model=GraphResponse)
async def get_investor_statistics():
    """获取投资者统计信息"""
    try:
        stats = _get_statistics()
        investor_stats = stats.get_investor_statistics()
        return GraphResponse(data=investor_stats)
    except Exception as e:
        logger.error(f"Failed to get investor statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/statistics", response_model=GraphResponse)
async def get_event_statistics():
    """获取事件统计信息"""
    try:
        stats = _get_statistics()
        event_stats = stats.get_event_statistics()
        return GraphResponse(data=event_stats)
    except Exception as e:
        logger.error(f"Failed to get event statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships/statistics", response_model=GraphResponse)
async def get_relationship_statistics():
    """获取关系统计信息"""
    try:
        stats = _get_statistics()
        rel_stats = stats.get_relationship_statistics()
        return GraphResponse(data=rel_stats)
    except Exception as e:
        logger.error(f"Failed to get relationship statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top/companies", response_model=GraphResponse)
async def get_top_companies(
    metric: str = Query("marketCap", description="排序指标"),
    limit: int = Query(10, ge=1, le=100),
):
    """获取顶级公司"""
    try:
        stats = _get_statistics()
        companies = stats.get_top_companies(metric, limit)
        return GraphResponse(data=companies)
    except Exception as e:
        logger.error(f"Failed to get top companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top/investors", response_model=GraphResponse)
async def get_top_investors(
    limit: int = Query(10, ge=1, le=100),
):
    """获取顶级投资者"""
    try:
        stats = _get_statistics()
        investors = stats.get_top_investors(limit)
        return GraphResponse(data=investors)
    except Exception as e:
        logger.error(f"Failed to get top investors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-events", response_model=GraphResponse)
async def get_recent_events(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=100),
):
    """获取最近事件"""
    try:
        stats = _get_statistics()
        events = stats.get_recent_events(days, limit)
        return GraphResponse(data=events)
    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}", response_model=GraphResponse)
async def get_company_info(stock_code: str):
    """获取公司信息"""
    try:
        query = _get_query()
        company = query.get_company_info(stock_code)
        if company is None:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")
        return GraphResponse(data=company)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/details", response_model=GraphResponse)
async def get_company_details(stock_code: str):
    """获取公司详细信息"""
    try:
        query = _get_query()
        company = query.get_company_with_industry(stock_code)
        if company is None:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")
        return GraphResponse(data=company)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/graph", response_model=GraphResponse)
async def get_company_graph(
    stock_code: str,
    depth: int = Query(2, ge=1, le=4),
):
    """获取公司关系图谱"""
    try:
        query = _get_query()
        graph = query.get_company_graph(stock_code, depth)
        return GraphResponse(data=graph)
    except Exception as e:
        logger.error(f"Failed to get company graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/competitors", response_model=GraphResponse)
async def get_company_competitors(
    stock_code: str,
    limit: int = Query(10, ge=1, le=50),
):
    """获取公司竞争对手"""
    try:
        query = _get_query()
        competitors = query.get_company_competitors(stock_code, limit)
        return GraphResponse(data=competitors)
    except Exception as e:
        logger.error(f"Failed to get competitors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/investors", response_model=GraphResponse)
async def get_company_investors(
    stock_code: str,
    limit: int = Query(20, ge=1, le=100),
):
    """获取公司投资者"""
    try:
        query = _get_query()
        investors = query.get_company_investors(stock_code, limit)
        return GraphResponse(data=investors)
    except Exception as e:
        logger.error(f"Failed to get company investors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/events", response_model=GraphResponse)
async def get_company_events(
    stock_code: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
):
    """获取公司事件"""
    try:
        query = _get_query()
        events = query.get_company_events(stock_code, days, limit)
        return GraphResponse(data=events)
    except Exception as e:
        logger.error(f"Failed to get company events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}/financial", response_model=GraphResponse)
async def get_company_financial(
    stock_code: str,
    limit: int = Query(10, ge=1, le=50),
):
    """获取公司财务报告"""
    try:
        query = _get_query()
        reports = query.get_company_financial_reports(stock_code, limit)
        return GraphResponse(data=reports)
    except Exception as e:
        logger.error(f"Failed to get company financial: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/path", response_model=GraphResponse)
async def find_path(
    start_code: str,
    end_code: str,
    max_depth: int = Query(5, ge=1, le=10),
):
    """查找两个公司之间的路径"""
    try:
        query = _get_query()
        paths = query.find_path(start_code, end_code, max_depth)
        return GraphResponse(data=paths)
    except Exception as e:
        logger.error(f"Failed to find path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/companies", response_model=GraphResponse)
async def search_companies(
    keyword: str,
    limit: int = Query(20, ge=1, le=100),
):
    """搜索公司"""
    try:
        query = _get_query()
        companies = query.search_companies(keyword, limit)
        return GraphResponse(data=companies)
    except Exception as e:
        logger.error(f"Failed to search companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/events", response_model=GraphResponse)
async def search_events(
    keyword: str,
    limit: int = Query(50, ge=1, le=200),
):
    """搜索事件"""
    try:
        query = _get_query()
        events = query.search_events(keyword, limit)
        return GraphResponse(data=events)
    except Exception as e:
        logger.error(f"Failed to search events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/init", response_model=GraphResponse)
async def init_database():
    """初始化数据库"""
    try:
        builder = _get_builder()
        builder.init_schema()
        return GraphResponse(message="Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to init database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=GraphResponse)
async def execute_query(
    query: str = Body(..., description="Cypher 查询语句"),
    parameters: Optional[Dict[str, Any]] = Body(None, description="查询参数"),
):
    """执行 Cypher 查询"""
    try:
        graph_query = _get_query()
        result = graph_query.execute_query(query, parameters)
        return GraphResponse(data=result)
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
