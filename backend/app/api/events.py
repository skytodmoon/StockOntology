"""
市场事件 API

提供市场事件的增删改查接口。
"""

from typing import Any, Dict, List, Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.models.event import (
    MarketEvent,
    MarketEventCreate,
    EventType,
    ImpactLevel,
    MarketEventResponse,
    MarketEventListResponse,
)
from app.repositories import EventRepository

router = APIRouter()


def get_event_repo() -> EventRepository:
    """获取事件仓库实例"""
    return EventRepository()


@router.get("", response_model=MarketEventListResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    impact_level: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """获取事件列表"""
    try:
        repo = get_event_repo()

        if start_date and end_date:
            events = repo.find_by_date_range(
                start_date,
                end_date,
                EventType(event_type) if event_type else None,
                skip,
                limit,
            )
        elif event_type:
            events = repo.find_by_type(EventType(event_type), skip, limit)
        elif impact_level:
            events = repo.find_by_impact_level(ImpactLevel(impact_level), skip, limit)
        else:
            events = repo.find_all(skip=skip, limit=limit)

        total = repo.count()

        return MarketEventListResponse(
            data=events,
            total=total,
        )
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_events(
    days: int = Query(7, ge=1, le=30),
    event_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """获取最近事件"""
    try:
        repo = get_event_repo()
        events = repo.find_recent_events(
            days,
            EventType(event_type) if event_type else None,
            limit,
        )
        return {"success": True, "data": events, "total": len(events)}
    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}")
async def search_events(
    keyword: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """搜索事件"""
    try:
        repo = get_event_repo()
        events = repo.search_events(keyword, skip, limit)
        return {"success": True, "data": events, "total": len(events)}
    except Exception as e:
        logger.error(f"Failed to search events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=MarketEventResponse)
async def get_event(event_id: str):
    """获取事件详情"""
    try:
        repo = get_event_repo()
        event = repo.find_by_event_id(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
        return MarketEventResponse(data=event)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}/impact")
async def get_event_impact(event_id: str):
    """获取事件影响"""
    try:
        repo = get_event_repo()
        impact = repo.get_event_impact(event_id)
        return {"success": True, "data": impact}
    except Exception as e:
        logger.error(f"Failed to get event impact {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}/chain")
async def get_event_chain(event_id: str):
    """获取事件链"""
    try:
        repo = get_event_repo()
        chain = repo.get_event_chain(event_id)
        return {"success": True, "data": chain}
    except Exception as e:
        logger.error(f"Failed to get event chain {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}")
async def get_company_events(
    stock_code: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
):
    """获取影响公司的事件"""
    try:
        repo = get_event_repo()
        events = repo.get_events_by_company(stock_code, days, limit)
        return {"success": True, "data": events, "total": len(events)}
    except Exception as e:
        logger.error(f"Failed to get company events {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry/{industry}")
async def get_industry_events(
    industry: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
):
    """获取影响行业的事件"""
    try:
        repo = get_event_repo()
        events = repo.get_events_by_industry(industry, days, limit)
        return {"success": True, "data": events, "total": len(events)}
    except Exception as e:
        logger.error(f"Failed to get industry events {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=MarketEventResponse)
async def create_event(event: MarketEventCreate):
    """创建事件"""
    try:
        repo = get_event_repo()
        created = repo.create_event(event)
        if created is None:
            raise HTTPException(status_code=400, detail="Failed to create event")
        return MarketEventResponse(data=created, message="Event created successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{event_id}/impact")
async def create_impact(
    event_id: str,
    target_code: str,
    target_type: str,
    impact_type: str,
    impact_direction: str,
    confidence: float = Query(0.5, ge=0, le=1),
):
    """创建事件影响关系"""
    try:
        repo = get_event_repo()
        success = repo.create_impact_relationship(
            event_id,
            target_code,
            target_type,
            impact_type,
            impact_direction,
            confidence,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create impact")
        return {"success": True, "message": "Impact relationship created"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{cause_id}/causes/{effect_id}")
async def create_causal_relationship(cause_id: str, effect_id: str):
    """创建因果关系"""
    try:
        repo = get_event_repo()
        success = repo.create_causal_relationship(cause_id, effect_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create causal relationship")
        return {"success": True, "message": "Causal relationship created"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create causal relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_import_events(events: List[MarketEventCreate]):
    """批量导入事件"""
    try:
        repo = get_event_repo()
        count = repo.batch_import(events)
        return {
            "success": True,
            "message": f"Imported {count} events",
            "imported": count,
        }
    except Exception as e:
        logger.error(f"Failed to batch import events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
