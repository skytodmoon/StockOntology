"""
公司管理 API

提供公司的增删改查接口。
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.models.company import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
)
from app.repositories import CompanyRepository

router = APIRouter()


def get_company_repo() -> CompanyRepository:
    """获取公司仓库实例"""
    return CompanyRepository()


@router.get("", response_model=CompanyListResponse)
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    market: Optional[str] = None,
    industry: Optional[str] = None,
):
    """获取公司列表"""
    try:
        repo = get_company_repo()

        if market:
            companies = repo.find_by_market(market)
        elif industry:
            companies = repo.find_by_industry(industry)
        else:
            companies = repo.find_all(skip=skip, limit=limit)

        total = repo.count()

        return CompanyListResponse(
            data=companies,
            total=total,
            page=skip // limit + 1,
            page_size=limit,
        )
    except Exception as e:
        logger.error(f"Failed to get companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}", response_model=CompanyResponse)
async def get_company(stock_code: str):
    """获取公司详情"""
    try:
        repo = get_company_repo()
        company = repo.find_by_stock_code(stock_code)
        if company is None:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")
        return CompanyResponse(data=company)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/details")
async def get_company_details(stock_code: str):
    """获取公司详细信息（包含关联数据）"""
    try:
        repo = get_company_repo()
        details = repo.get_company_with_details(stock_code)
        if details is None:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")
        return {"success": True, "data": details}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company details {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/graph")
async def get_company_graph(
    stock_code: str,
    depth: int = Query(2, ge=1, le=4),
):
    """获取公司关系图谱"""
    try:
        repo = get_company_repo()
        graph = repo.get_company_graph(stock_code, depth)
        return {"success": True, "data": graph}
    except Exception as e:
        logger.error(f"Failed to get company graph {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/competitors")
async def get_competitors(
    stock_code: str,
    limit: int = Query(10, ge=1, le=50),
):
    """获取竞争对手"""
    try:
        repo = get_company_repo()
        competitors = repo.get_competitors(stock_code, limit)
        return {"success": True, "data": competitors}
    except Exception as e:
        logger.error(f"Failed to get competitors for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/investors")
async def get_company_investors(
    stock_code: str,
    limit: int = Query(20, ge=1, le=100),
):
    """获取机构投资者"""
    try:
        repo = get_company_repo()
        investors = repo.get_investors(stock_code, limit)
        return {"success": True, "data": investors}
    except Exception as e:
        logger.error(f"Failed to get investors for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}")
async def search_companies(
    keyword: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """搜索公司"""
    try:
        repo = get_company_repo()
        companies = repo.search_companies(keyword, skip, limit)
        return {"success": True, "data": companies, "total": len(companies)}
    except Exception as e:
        logger.error(f"Failed to search companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-cap/range")
async def get_companies_by_market_cap(
    min_cap: Optional[float] = Query(None, ge=0),
    max_cap: Optional[float] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """根据市值范围获取公司"""
    try:
        repo = get_company_repo()
        companies = repo.get_companies_by_market_cap(min_cap, max_cap, skip, limit)
        return {"success": True, "data": companies, "total": len(companies)}
    except Exception as e:
        logger.error(f"Failed to get companies by market cap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=CompanyResponse)
async def create_company(company: CompanyCreate):
    """创建公司"""
    try:
        repo = get_company_repo()
        created = repo.create_company(company)
        if created is None:
            raise HTTPException(status_code=400, detail="Failed to create company")
        return CompanyResponse(data=created, message="Company created successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create company: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{stock_code}", response_model=CompanyResponse)
async def update_company(stock_code: str, update: CompanyUpdate):
    """更新公司"""
    try:
        repo = get_company_repo()
        updated = repo.update_company(stock_code, update)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")
        return CompanyResponse(data=updated, message="Company updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update company {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{stock_code}")
async def delete_company(stock_code: str):
    """删除公司"""
    try:
        repo = get_company_repo()
        success = repo.delete_company(stock_code)
        if not success:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")
        return {"success": True, "message": f"Company '{stock_code}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete company {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_import_companies(companies: List[CompanyCreate]):
    """批量导入公司"""
    try:
        repo = get_company_repo()
        count = repo.batch_import(companies)
        return {
            "success": True,
            "message": f"Imported {count} companies",
            "imported": count,
        }
    except Exception as e:
        logger.error(f"Failed to batch import companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
