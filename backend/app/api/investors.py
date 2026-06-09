"""
投资者管理 API

提供投资者的增删改查接口。
"""

from typing import Any, Dict, List, Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.models.investor import (
    Investor,
    InvestorCreate,
    InvestorType,
    Holding,
    InvestorResponse,
    InvestorListResponse,
    HoldingResponse,
)
from app.repositories import InvestorRepository

router = APIRouter()


def get_investor_repo() -> InvestorRepository:
    """获取投资者仓库实例"""
    return InvestorRepository()


@router.get("", response_model=InvestorListResponse)
async def get_investors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    investor_type: Optional[str] = None,
):
    """获取投资者列表"""
    try:
        repo = get_investor_repo()

        if investor_type:
            investors = repo.find_by_type(InvestorType(investor_type), skip, limit)
        else:
            investors = repo.find_all(skip=skip, limit=limit)

        total = repo.count()

        return InvestorListResponse(
            data=investors,
            total=total,
        )
    except Exception as e:
        logger.error(f"Failed to get investors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top")
async def get_top_investors(
    investor_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """获取顶级投资者"""
    try:
        repo = get_investor_repo()
        investors = repo.get_top_investors(
            InvestorType(investor_type) if investor_type else None,
            limit,
        )
        return {"success": True, "data": investors}
    except Exception as e:
        logger.error(f"Failed to get top investors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}")
async def search_investors(
    keyword: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """搜索投资者"""
    try:
        repo = get_investor_repo()
        investors = repo.search_investors(keyword, skip, limit)
        return {"success": True, "data": investors, "total": len(investors)}
    except Exception as e:
        logger.error(f"Failed to search investors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investor_id}", response_model=InvestorResponse)
async def get_investor(investor_id: str):
    """获取投资者详情"""
    try:
        repo = get_investor_repo()
        investor = repo.find_by_investor_id(investor_id)
        if investor is None:
            raise HTTPException(status_code=404, detail=f"Investor '{investor_id}' not found")
        return InvestorResponse(data=investor)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get investor {investor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investor_id}/holdings")
async def get_investor_holdings(
    investor_id: str,
    report_date: Optional[date] = None,
):
    """获取投资者持仓"""
    try:
        repo = get_investor_repo()
        holdings = repo.get_investor_holdings(investor_id, report_date)
        return {"success": True, "data": holdings, "total": len(holdings)}
    except Exception as e:
        logger.error(f"Failed to get holdings for {investor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investor_id}/behavior")
async def get_investor_behavior(investor_id: str):
    """获取投资者行为分析"""
    try:
        repo = get_investor_repo()
        behavior = repo.get_investor_behavior(investor_id)
        return {"success": True, "data": behavior}
    except Exception as e:
        logger.error(f"Failed to get behavior for {investor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{stock_code}")
async def get_company_investors(
    stock_code: str,
    report_date: Optional[date] = None,
    investor_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """获取公司的投资者"""
    try:
        repo = get_investor_repo()
        investors = repo.get_company_investors(
            stock_code,
            report_date,
            InvestorType(investor_type) if investor_type else None,
            limit,
        )
        return {"success": True, "data": investors, "total": len(investors)}
    except Exception as e:
        logger.error(f"Failed to get company investors {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=InvestorResponse)
async def create_investor(investor: InvestorCreate):
    """创建投资者"""
    try:
        repo = get_investor_repo()
        created = repo.create_investor(investor)
        if created is None:
            raise HTTPException(status_code=400, detail="Failed to create investor")
        return InvestorResponse(data=created, message="Investor created successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create investor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{investor_id}/holdings/{stock_code}")
async def create_holding(
    investor_id: str,
    stock_code: str,
    holding: Holding,
):
    """创建持仓关系"""
    try:
        repo = get_investor_repo()
        success = repo.create_holding(investor_id, stock_code, holding)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create holding")
        return {"success": True, "message": "Holding created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create holding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{investor_id}/holdings/{stock_code}")
async def update_holding(
    investor_id: str,
    stock_code: str,
    holding: Holding,
):
    """更新持仓关系"""
    try:
        repo = get_investor_repo()
        success = repo.update_holding(investor_id, stock_code, holding)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update holding")
        return {"success": True, "message": "Holding updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update holding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{investor_id}/holdings/{stock_code}")
async def delete_holding(investor_id: str, stock_code: str):
    """删除持仓关系"""
    try:
        repo = get_investor_repo()
        success = repo.delete_holding(investor_id, stock_code)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete holding")
        return {"success": True, "message": "Holding deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete holding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_import_investors(investors: List[InvestorCreate]):
    """批量导入投资者"""
    try:
        repo = get_investor_repo()
        count = repo.batch_import(investors)
        return {
            "success": True,
            "message": f"Imported {count} investors",
            "imported": count,
        }
    except Exception as e:
        logger.error(f"Failed to batch import investors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
