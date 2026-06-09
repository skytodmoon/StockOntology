"""
财务数据 API

提供财务报告的增删改查接口。
"""

from typing import Any, Dict, List, Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.models.financial import (
    FinancialReport,
    FinancialReportCreate,
    ReportType,
    FinancialReportResponse,
    FinancialReportListResponse,
)
from app.repositories import FinancialRepository

router = APIRouter()


def get_financial_repo() -> FinancialRepository:
    """获取财务仓库实例"""
    return FinancialRepository()


@router.get("/{stock_code}", response_model=FinancialReportListResponse)
async def get_financial_reports(
    stock_code: str,
    report_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """获取公司的财务报告列表"""
    try:
        repo = get_financial_repo()
        reports = repo.find_by_stock_code(
            stock_code,
            ReportType(report_type) if report_type else None,
            start_date,
            end_date,
            limit,
        )
        return FinancialReportListResponse(
            data=reports,
            total=len(reports),
        )
    except Exception as e:
        logger.error(f"Failed to get financial reports for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/latest")
async def get_latest_financial_report(stock_code: str):
    """获取最新的财务报告"""
    try:
        repo = get_financial_repo()
        report = repo.find_latest_by_stock_code(stock_code)
        if report is None:
            raise HTTPException(
                status_code=404,
                detail=f"No financial report found for '{stock_code}'"
            )
        return {"success": True, "data": report}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest report for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/{report_date}")
async def get_financial_report_by_date(
    stock_code: str,
    report_date: date,
    report_type: Optional[str] = None,
):
    """根据日期获取财务报告"""
    try:
        repo = get_financial_repo()
        report = repo.find_by_stock_code_and_date(
            stock_code,
            report_date,
            ReportType(report_type) if report_type else None,
        )
        if report is None:
            raise HTTPException(
                status_code=404,
                detail=f"No financial report found for '{stock_code}' on {report_date}"
            )
        return {"success": True, "data": report}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report for {stock_code} on {report_date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/trends")
async def get_financial_trends(
    stock_code: str,
    indicators: List[str] = Query(["revenue", "netProfit", "eps", "roe"]),
    periods: int = Query(8, ge=1, le=20),
):
    """获取财务指标趋势"""
    try:
        repo = get_financial_repo()
        trends = repo.get_financial_trends(stock_code, indicators, periods)
        return {"success": True, "data": trends}
    except Exception as e:
        logger.error(f"Failed to get trends for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/comparison")
async def get_industry_comparison(
    stock_code: str,
    indicators: List[str] = Query(["peRatio", "pbRatio", "roe", "netMargin"]),
):
    """获取行业对比数据"""
    try:
        repo = get_financial_repo()
        comparison = repo.get_industry_comparison(stock_code, indicators)
        return {"success": True, "data": comparison}
    except Exception as e:
        logger.error(f"Failed to get comparison for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{stock_code}")
async def create_financial_report(
    stock_code: str,
    report: FinancialReportCreate,
):
    """创建财务报告"""
    try:
        # 确保股票代码一致
        report.stock_code = stock_code

        repo = get_financial_repo()
        created = repo.create_financial_report(report)
        if created is None:
            raise HTTPException(status_code=400, detail="Failed to create financial report")
        return {
            "success": True,
            "data": created,
            "message": "Financial report created successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create financial report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{stock_code}/batch")
async def batch_import_financial_reports(
    stock_code: str,
    reports: List[FinancialReportCreate],
):
    """批量导入财务报告"""
    try:
        # 确保股票代码一致
        for report in reports:
            report.stock_code = stock_code

        repo = get_financial_repo()
        count = repo.batch_import(reports)
        return {
            "success": True,
            "message": f"Imported {count} financial reports",
            "imported": count,
        }
    except Exception as e:
        logger.error(f"Failed to batch import financial reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))
