"""
预测 API

提供股价预测接口。
增强功能：
- 使用真实行情数据（StockPrice 节点或 AKShare 采集）
- 支持本体特征增强预测
- 预测结果接受本体规则校验
- 预测记录写入图谱（留痕）
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.core.prediction import PredictionService
from app.core.graph import GraphQuery, GraphBuilder

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

def _get_graph_builder():
    """获取图谱构建器"""
    return GraphBuilder()


def _fetch_price_data(stock_code: str, limit: int = 60) -> List[Dict[str, Any]]:
    """
    获取股票历史价格数据

    优先从 Neo4j 的 StockPrice 节点读取，
    如果没有则尝试通过 AKShare 实时采集。

    Args:
        stock_code: 股票代码
        limit: 数据条数

    Returns:
        价格数据列表，每条包含 open/high/low/close/volume
    """
    graph = _get_graph_query()

    # 方式 1：从 Neo4j StockPrice 节点读取
    query = """
        MATCH (sp:StockPrice {stockCode: $stockCode})
        RETURN sp
        ORDER BY sp.tradeDate DESC
        LIMIT $limit
    """
    try:
        result = graph.execute_query(query, {"stockCode": stock_code, "limit": limit})
        if result and len(result) >= 20:
            price_data = []
            for r in reversed(result):  # 按时间正序
                sp = dict(r["sp"])
                price_data.append({
                    "open": float(sp.get("open", 0)),
                    "high": float(sp.get("high", 0)),
                    "low": float(sp.get("low", 0)),
                    "close": float(sp.get("close", 0)),
                    "volume": int(sp.get("volume", 0)),
                    "trade_date": sp.get("tradeDate", ""),
                })
            return price_data
    except Exception as e:
        logger.warning(f"Failed to read StockPrice from Neo4j: {e}")

    # 方式 2：通过 AKShare 实时采集
    try:
        from app.core.collectors.market_collector import MarketDataCollector
        collector = MarketDataCollector()
        raw_data = collector.collect(stock_codes=[stock_code])
        if raw_data and len(raw_data) >= 20:
            price_data = []
            for item in raw_data:
                price_data.append({
                    "open": float(item.get("open", 0)),
                    "high": float(item.get("high", 0)),
                    "low": float(item.get("low", 0)),
                    "close": float(item.get("close", 0)),
                    "volume": int(item.get("volume", 0)),
                    "trade_date": item.get("tradeDate", item.get("trade_date", "")),
                })
            return price_data
    except Exception as e:
        logger.warning(f"Failed to collect data from AKShare: {e}")

    # 方式 3：从 FinancialReport 推算（最后的兜底）
    query = """
        MATCH (c:Company {stockCode: $stockCode})-[:HAS_REPORT]->(f:FinancialReport)
        RETURN f
        ORDER BY f.reportDate DESC
        LIMIT $limit
    """
    try:
        result = graph.execute_query(query, {"stockCode": stock_code, "limit": limit})
        if result:
            price_data = []
            for r in result:
                report = dict(r["f"])
                eps = float(report.get("eps", 0))
                if eps > 0:
                    price_data.append({
                        "close": eps * 20,  # 粗略估算
                        "open": eps * 19.5,
                        "high": eps * 21,
                        "low": eps * 19,
                        "volume": 1000000,
                    })
            return price_data
    except Exception as e:
        logger.warning(f"Failed to read FinancialReport: {e}")

    return []


@router.post("/price", response_model=PredictionResponse)
async def predict_price(
    stock_code: str,
    days: int = Query(5, ge=1, le=30),
):
    """预测股价"""
    try:
        price_data = _fetch_price_data(stock_code)

        if len(price_data) < 20:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient price data for '{stock_code}' (need >= 20, got {len(price_data)})"
            )

        service = _get_prediction_service()
        prediction = service.predict_price(stock_code, price_data, days)

        # 预测记录写入图谱（留痕）
        try:
            builder = _get_graph_builder()
            import uuid
            record_id = str(uuid.uuid4())[:8]
            builder.create_prediction_record({
                "record_id": record_id,
                "recordId": record_id,
                "stock_code": stock_code,
                "model_type": prediction.get("model_type", "simple"),
                "prediction": str(prediction.get("predictions", [])),
                "confidence": prediction.get("confidence", 0),
                "data_points_used": len(price_data),
            })
            builder.create_prediction_company_relationship(record_id, stock_code)
        except Exception as e:
            logger.warning(f"Failed to save prediction record: {e}")

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
        price_data = _fetch_price_data(stock_code)

        if len(price_data) < 10:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for '{stock_code}' (need >= 10, got {len(price_data)})"
            )

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
        price_data = _fetch_price_data(stock_code)

        if len(price_data) < 20:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for '{stock_code}' (need >= 20, got {len(price_data)})"
            )

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
        price_data = _fetch_price_data(stock_code, limit=120)

        if len(price_data) < pattern_length * 2:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for '{stock_code}' (need >= {pattern_length * 2}, got {len(price_data)})"
            )

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

        price_data = _fetch_price_data(stock_code)

        if len(price_data) < 20:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for '{stock_code}' (need >= 20, got {len(price_data)})"
            )

        fe = FeatureEngineering()
        features = fe.prepare_features(price_data)

        return PredictionResponse(data={
            "stock_code": stock_code,
            "features": features,
            "data_points": len(price_data),
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ontology-enhanced", response_model=PredictionResponse)
async def ontology_enhanced_prediction(
    stock_code: str,
    days: int = Query(5, ge=1, le=30),
):
    """
    本体增强预测

    融合技术指标 + 本体特征（事件影响、供应链风险、竞争压力）
    预测结果接受本体规则校验。
    """
    try:
        from app.core.reasoning import OntologyReasoner

        price_data = _fetch_price_data(stock_code)

        if len(price_data) < 20:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for '{stock_code}'"
            )

        # 技术指标预测
        service = _get_prediction_service()
        tech_prediction = service.predict_price(stock_code, price_data, days)

        # 本体特征
        reasoner = OntologyReasoner()
        ontology_features = {
            "accumulated_impact": reasoner.get_accumulated_impact(stock_code, days=30),
        }

        # 本体规则校验
        trend = tech_prediction.get("predictions", [{}])[0].get("trend", "neutral")
        validation = reasoner.predict_with_ontology_rules(stock_code, trend)

        # 融合结果
        result = {
            "stock_code": stock_code,
            "technical_prediction": tech_prediction,
            "ontology_features": ontology_features,
            "ontology_validation": validation,
            "is_consistent": validation.get("is_consistent", True),
            "contradictions": validation.get("contradictions", []),
        }

        # 留痕
        try:
            builder = _get_graph_builder()
            import uuid
            record_id = str(uuid.uuid4())[:8]
            builder.create_prediction_record({
                "record_id": record_id,
                "recordId": record_id,
                "stock_code": stock_code,
                "model_type": "ontology_enhanced",
                "prediction": trend,
                "confidence": tech_prediction.get("confidence", 0),
                "is_consistent": validation.get("is_consistent", True),
            })
            builder.create_prediction_company_relationship(record_id, stock_code)
        except Exception as e:
            logger.warning(f"Failed to save prediction record: {e}")

        return PredictionResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ontology-enhanced prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price-data", response_model=PredictionResponse)
async def get_price_data(
    stock_code: str,
    limit: int = Query(120, ge=10, le=500),
):
    """
    获取股票历史行情数据（用于 K 线图展示）

    从 Neo4j StockPrice 节点读取，返回 OHLCV 格式。
    """
    try:
        graph = _get_graph_query()

        query = """
            MATCH (sp:StockPrice {stockCode: $stockCode})
            RETURN sp
            ORDER BY sp.tradeDate ASC
            LIMIT $limit
        """
        result = graph.execute_query(query, {"stockCode": stock_code, "limit": limit})

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No price data found for '{stock_code}'"
            )

        price_data = []
        for r in result:
            sp = dict(r["sp"])
            price_data.append({
                "trade_date": sp.get("tradeDate", ""),
                "open": float(sp.get("open", 0)),
                "high": float(sp.get("high", 0)),
                "low": float(sp.get("low", 0)),
                "close": float(sp.get("close", 0)),
                "volume": int(sp.get("volume", 0)),
            })

        # 获取公司名称
        company_query = """
            MATCH (c:Company {stockCode: $stockCode})
            RETURN c.stockName AS name
        """
        company_result = graph.execute_query(company_query, {"stockCode": stock_code})
        stock_name = ""
        if company_result:
            stock_name = dict(company_result[0]).get("name", "")

        return PredictionResponse(data={
            "stock_code": stock_code,
            "stock_name": stock_name,
            "count": len(price_data),
            "prices": price_data,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get price data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rising-stars", response_model=PredictionResponse)
async def get_rising_stocks(
    days: int = Query(5, ge=1, le=30, description="预测天数"),
    min_confidence: float = Query(0.5, ge=0, le=1, description="最低置信度"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
):
    """
    扫描所有有行情数据的股票，预测未来有上涨趋势的股票列表

    返回按预测涨幅排序的股票列表，包含：
    - 预测方向（up/down/neutral）
    - 预测涨幅（%）
    - 置信度
    - 技术指标摘要
    - 本体特征摘要
    """
    try:
        graph = _get_graph_query()
        service = _get_prediction_service()

        # 获取所有有行情数据的公司
        companies_query = """
            MATCH (c:Company)-[:HAS_PRICE]->(sp:StockPrice)
            WITH c, count(sp) AS price_count
            WHERE price_count >= 30
            RETURN c.stockCode AS code, c.stockName AS name,
                   c.leaderTag AS tag, c.industry AS industry,
                   price_count
            ORDER BY price_count DESC
        """
        companies = graph.execute_query(companies_query)

        if not companies:
            return PredictionResponse(data={
                "rising_stocks": [],
                "total_scanned": 0,
                "message": "没有找到有行情数据的股票",
            })

        results = []
        scanned = 0

        for comp in companies:
            comp_data = dict(comp)
            code = comp_data["code"]

            try:
                # 获取价格数据
                price_data = _fetch_price_data(code, limit=60)
                if len(price_data) < 20:
                    continue

                scanned += 1

                # 趋势预测
                trend_result = service.predict_trend(code, price_data, "week")

                # 只保留看涨的
                trend = trend_result.get("trend", "neutral")
                if trend != "bullish":
                    continue

                confidence = trend_result.get("confidence", 0)
                if confidence < min_confidence:
                    continue

                # 价格预测
                price_pred = service.predict_price(code, price_data, days)
                predictions = price_pred.get("predictions", [])

                # 计算预测涨幅
                current_price = price_data[-1].get("close", 0)
                predicted_price = predictions[-1].get("predicted_price", current_price) if predictions else current_price
                change_pct = ((predicted_price - current_price) / current_price * 100) if current_price > 0 else 0

                # 技术指标
                indicators = trend_result.get("indicators", {})

                results.append({
                    "stock_code": code,
                    "stock_name": comp_data.get("name", ""),
                    "leader_tag": comp_data.get("tag", ""),
                    "industry": comp_data.get("industry", ""),
                    "current_price": round(current_price, 2),
                    "predicted_price": round(predicted_price, 2),
                    "predicted_change_pct": round(change_pct, 2),
                    "confidence": round(confidence, 2),
                    "trend": trend,
                    "signals": trend_result.get("signals", []),
                    "indicators": {
                        "ma5": indicators.get("ma5"),
                        "ma10": indicators.get("ma10"),
                        "rsi": indicators.get("rsi"),
                    },
                    "predictions": predictions,
                })

            except Exception as e:
                logger.warning(f"Failed to predict {code}: {e}")
                continue

        # 按预测涨幅排序
        results.sort(key=lambda x: x["predicted_change_pct"], reverse=True)

        return PredictionResponse(data={
            "rising_stocks": results[:limit],
            "total_scanned": scanned,
            "total_rising": len(results),
            "prediction_days": days,
            "min_confidence": min_confidence,
        })
    except Exception as e:
        logger.error(f"Rising stocks scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
