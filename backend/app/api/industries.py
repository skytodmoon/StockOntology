"""
行业管理 API

提供行业的增删改查接口。
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.models.industry import (
    Industry,
    IndustryCreate,
    IndustryUpdate,
    IndustryResponse,
    IndustryListResponse,
)
from app.repositories import IndustryRepository

router = APIRouter()


def get_industry_repo() -> IndustryRepository:
    """获取行业仓库实例"""
    return IndustryRepository()


@router.get("", response_model=IndustryListResponse)
async def get_industries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    level: Optional[int] = None,
):
    """获取行业列表"""
    try:
        repo = get_industry_repo()

        if level:
            industries = repo.find_by_level(level)
        else:
            industries = repo.find_all(skip=skip, limit=limit)

        total = repo.count()

        return IndustryListResponse(
            data=industries,
            total=total,
        )
    except Exception as e:
        logger.error(f"Failed to get industries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hierarchy")
async def get_industry_hierarchy():
    """获取行业层级结构"""
    try:
        repo = get_industry_repo()
        hierarchy = repo.get_industry_hierarchy()
        return {"success": True, "data": hierarchy}
    except Exception as e:
        logger.error(f"Failed to get hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}", response_model=IndustryResponse)
async def get_industry(code: str):
    """获取行业详情"""
    try:
        repo = get_industry_repo()
        industry = repo.find_by_code(code)
        if industry is None:
            raise HTTPException(status_code=404, detail=f"Industry '{code}' not found")
        return IndustryResponse(data=industry)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get industry {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/chain")
async def get_industry_chain(code: str):
    """获取产业链信息"""
    try:
        repo = get_industry_repo()
        chain = repo.get_industry_chain(code)
        return {"success": True, "data": chain}
    except Exception as e:
        logger.error(f"Failed to get industry chain {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/statistics")
async def get_industry_statistics(code: str):
    """获取行业统计信息"""
    try:
        repo = get_industry_repo()
        stats = repo.get_industry_statistics(code)
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Failed to get industry stats {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/companies")
async def get_industry_companies(
    code: str,
    limit: int = Query(20, ge=1, le=100),
):
    """获取行业龙头公司"""
    try:
        repo = get_industry_repo()
        companies = repo.get_top_companies(code, limit)
        return {"success": True, "data": companies}
    except Exception as e:
        logger.error(f"Failed to get industry companies {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/sub-industries")
async def get_sub_industries(code: str):
    """获取子行业"""
    try:
        repo = get_industry_repo()
        sub_industries = repo.find_sub_industries(code)
        return {"success": True, "data": sub_industries}
    except Exception as e:
        logger.error(f"Failed to get sub-industries {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=IndustryResponse)
async def create_industry(industry: IndustryCreate):
    """创建行业"""
    try:
        repo = get_industry_repo()
        created = repo.create_industry(industry)
        if created is None:
            raise HTTPException(status_code=400, detail="Failed to create industry")
        return IndustryResponse(data=created, message="Industry created successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create industry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{code}", response_model=IndustryResponse)
async def update_industry(code: str, update: IndustryUpdate):
    """更新行业"""
    try:
        repo = get_industry_repo()
        updated = repo.update_industry(code, update)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Industry '{code}' not found")
        return IndustryResponse(data=updated, message="Industry updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update industry {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{code}")
async def delete_industry(code: str):
    """删除行业"""
    try:
        repo = get_industry_repo()
        success = repo.delete_industry(code)
        if not success:
            raise HTTPException(status_code=404, detail=f"Industry '{code}' not found")
        return {"success": True, "message": f"Industry '{code}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete industry {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{parent_code}/sub-industries/{child_code}")
async def create_sub_industry(parent_code: str, child_code: str):
    """创建子行业关系"""
    try:
        repo = get_industry_repo()
        success = repo.create_sub_industry_relationship(parent_code, child_code)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create sub-industry relationship")
        return {"success": True, "message": "Sub-industry relationship created"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create sub-industry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_import_industries(industries: List[IndustryCreate]):
    """批量导入行业"""
    try:
        repo = get_industry_repo()
        count = repo.batch_import(industries)
        return {
            "success": True,
            "message": f"Imported {count} industries",
            "imported": count,
        }
    except Exception as e:
        logger.error(f"Failed to batch import industries: {e}")
        raise HTTPException(status_code=500, detail=str(e))
