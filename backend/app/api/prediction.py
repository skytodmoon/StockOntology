"""
预测 API

提供股价预测接口。
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.core.prediction import PredictionService
from app.core.graph import GraphQuery

router = APIRouter()


class PredictionResponse(BaseModel):
    """预测响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


def _get_prediction_service():
    """获取预测服务"""
    return PredictionService()

def _get_graph_query():
    """获取图谱查询"""
    return GraphQuery()


@router.post("/price", response_model=PredictionResponse)
async def predict_price(
    stock_code: str,
    days: int = Query(5, ge=1, le=30),
):
    """预测股价"""
    try:
        graph = _get_graph_query()

        # 获取历史价格数据
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:HAS_REPORT]->(f:FinancialReport)
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT 30
        """
        result = graph.execute_query(query, {"stockCode": stock_code})

        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for '{stock_code}'")

        # 转换为价格数据格式
        price_data = []
        for r in result:
            report = dict(r["f"])
            price_data.append({
                "close": report.get("eps", 0) * 20,  # 模拟价格
                "volume": 1000000,
                "high": report.get("eps", 0) * 21,
                "low": report.get("eps", 0) * 19,
            })

        service = _get_prediction_service()
        prediction = service.predict_price(stock_code, price_data, days)

        return PredictionResponse(data=prediction)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Price prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trend", response_model=PredictionResponse)
async def predict_trend(
    stock_code: str,
    period: str = Query("week", description="预测周期"),
):
    """预测趋势"""
    try:
        graph = _get_graph_query()

        # 获取历史数据
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:HAS_REPORT]->(f:FinancialReport)
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT 30
        """
        result = graph.execute_query(query, {"stockCode": stock_code})

        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for '{stock_code}'")

        # 转换为价格数据格式
        price_data = []
        for r in result:
            report = dict(r["f"])
            price_data.append({
                "close": report.get("eps", 0) * 20,
                "volume": 1000000,
            })

        service = _get_prediction_service()
        trend = service.predict_trend(stock_code, price_data, period)

        return PredictionResponse(data=trend)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trend prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk", response_model=PredictionResponse)
async def calculate_risk(stock_code: str):
    """计算风险分数"""
    try:
        graph = _get_graph_query()

        # 获取历史数据
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:HAS_REPORT]->(f:FinancialReport)
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT 30
        """
        result = graph.execute_query(query, {"stockCode": stock_code})

        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for '{stock_code}'")

        # 转换为价格数据格式
        price_data = []
        for r in result:
            report = dict(r["f"])
            price_data.append({
                "close": report.get("eps", 0) * 20,
                "volume": 1000000,
            })

        service = _get_prediction_service()
        risk = service.calculate_risk_score(stock_code, price_data)

        return PredictionResponse(data=risk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar-patterns", response_model=PredictionResponse)
async def find_similar_patterns(
    stock_code: str,
    pattern_length: int = Query(10, ge=5, le=30),
    top_k: int = Query(5, ge=1, le=20),
):
    """查找相似模式"""
    try:
        graph = _get_graph_query()

        # 获取历史数据
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:HAS_REPORT]->(f:FinancialReport)
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT 50
        """
        result = graph.execute_query(query, {"stockCode": stock_code})

        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for '{stock_code}'")

        # 转换为价格数据格式
        price_data = []
        for r in result:
            report = dict(r["f"])
            price_data.append({
                "close": report.get("eps", 0) * 20,
                "volume": 1000000,
            })

        service = _get_prediction_service()
        patterns = service.find_similar_patterns(stock_code, price_data, pattern_length, top_k)

        return PredictionResponse(data={
            "stock_code": stock_code,
            "patterns": patterns,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pattern search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/features", response_model=PredictionResponse)
async def extract_features(stock_code: str):
    """提取特征"""
    try:
        from app.core.prediction import FeatureEngineering

        graph = _get_graph_query()

        # 获取历史数据
        query = """
            MATCH (c:Company {stockCode: $stockCode})-[:HAS_REPORT]->(f:FinancialReport)
            RETURN f
            ORDER BY f.reportDate DESC
            LIMIT 30
        """
        result = graph.execute_query(query, {"stockCode": stock_code})

        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for '{stock_code}'")

        # 转换为价格数据格式
        price_data = []
        for r in result:
            report = dict(r["f"])
            price_data.append({
                "close": report.get("eps", 0) * 20,
                "volume": 1000000,
                "high": report.get("eps", 0) * 21,
                "low": report.get("eps", 0) * 19,
            })

        fe = FeatureEngineering()
        features = fe.prepare_features(price_data)

        return PredictionResponse(data={
            "stock_code": stock_code,
            "features": features,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
