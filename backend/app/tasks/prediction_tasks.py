"""
预测刷新任务

自动扫描所有股票，运行本体增强预测，筛选看涨股票。
"""

from loguru import logger


def daily_prediction_scan():
    """
    每日预测扫描

    触发时间：每日 20:00
    流程：
    1. 扫描所有有行情数据的股票
    2. 运行本体增强预测
    3. 筛选出看涨股票
    4. 结果写入 Redis 缓存
    """
    from datetime import datetime
    from app.core.database import get_neo4j_client, get_redis_client
    from app.core.prediction import PredictionService

    logger.info("[预测任务] 开始每日预测扫描...")

    try:
        neo4j = get_neo4j_client()
        redis = get_redis_client()
        service = PredictionService()

        # 1. 获取有行情数据的公司
        companies = neo4j.execute_query("""
            MATCH (c:Company)-[:HAS_PRICE]->(sp:StockPrice)
            WITH c, count(sp) AS priceCount
            WHERE priceCount >= 30
            RETURN c.stockCode AS code, c.stockName AS name,
                   c.leaderTag AS tag, c.industry AS industry
        """)

        logger.info(f"  待预测公司: {len(companies)} 家")

        # 2. 获取价格数据函数
        def get_price_data(code, limit=60):
            result = neo4j.execute_query("""
                MATCH (sp:StockPrice {stockCode: $code})
                RETURN sp ORDER BY sp.tradeDate ASC LIMIT $limit
            """, {"code": code, "limit": limit})
            if not result:
                return []
            price_data = []
            for r in result:
                sp = dict(r["sp"])
                price_data.append({
                    "open": float(sp.get("open", 0)),
                    "high": float(sp.get("high", 0)),
                    "low": float(sp.get("low", 0)),
                    "close": float(sp.get("close", 0)),
                    "volume": int(sp.get("volume", 0)),
                })
            return price_data

        # 3. 逐个预测
        rising_stocks = []
        scanned = 0
        failed = 0

        for comp in companies:
            comp_data = dict(comp)
            code = comp_data["code"]

            try:
                price_data = get_price_data(code, 60)
                if len(price_data) < 20:
                    continue

                scanned += 1

                # 趋势预测
                trend_result = service.predict_trend(code, price_data, "week")
                trend = trend_result.get("trend", "neutral")
                confidence = trend_result.get("confidence", 0)

                # 只保留看涨的
                if trend != "bullish" or confidence < 0.5:
                    continue

                # 价格预测
                price_pred = service.predict_price(code, price_data, 5)
                predictions = price_pred.get("predictions", [])

                current_price = price_data[-1].get("close", 0)
                predicted_price = predictions[-1].get("predicted_price", current_price) if predictions else current_price
                change_pct = ((predicted_price - current_price) / current_price * 100) if current_price > 0 else 0

                rising_stocks.append({
                    "stock_code": code,
                    "stock_name": comp_data.get("name", ""),
                    "leader_tag": comp_data.get("tag", ""),
                    "industry": comp_data.get("industry", ""),
                    "current_price": round(current_price, 2),
                    "predicted_price": round(predicted_price, 2),
                    "predicted_change_pct": round(change_pct, 2),
                    "confidence": round(confidence, 2),
                    "indicators": trend_result.get("indicators", {}),
                })

            except Exception as e:
                failed += 1
                continue

        # 4. 按涨幅排序
        rising_stocks.sort(key=lambda x: x["predicted_change_pct"], reverse=True)

        # 5. 写入 Redis 缓存
        import json
        cache_data = {
            "scan_time": datetime.now().isoformat(),
            "total_scanned": scanned,
            "total_rising": len(rising_stocks),
            "rising_stocks": rising_stocks,
        }
        redis.set(
            "daily_rising_stocks",
            json.dumps(cache_data, ensure_ascii=False),
            ex=86400  # 24 小时过期
        )

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "scanned": scanned,
            "failed": failed,
            "rising_count": len(rising_stocks),
            "top_5": [
                {"code": s["stock_code"], "name": s["stock_name"], "change": s["predicted_change_pct"]}
                for s in rising_stocks[:5]
            ],
        }
        logger.info(f"[预测任务] 每日预测扫描完成: {result}")
        return result

    except Exception as e:
        logger.error(f"[预测任务] 每日预测扫描异常: {e}")
        raise self.retry(exc=e, countdown=120)


def refresh_stock_prediction( stock_code: str):
    """
    刷新单只股票的预测

    Args:
        stock_code: 股票代码

    用途：用户主动触发
    """
    from datetime import datetime
    from app.core.database import get_neo4j_client, get_redis_client
    from app.core.prediction import PredictionService

    logger.info(f"[预测任务] 刷新预测: {stock_code}")

    try:
        neo4j = get_neo4j_client()
        redis = get_redis_client()
        service = PredictionService()

        # 获取价格数据
        result = neo4j.execute_query("""
            MATCH (sp:StockPrice {stockCode: $code})
            RETURN sp ORDER BY sp.tradeDate ASC LIMIT 60
        """, {"code": stock_code})

        if not result:
            return {"status": "error", "message": f"No price data for {stock_code}"}

        price_data = []
        for r in result:
            sp = dict(r["sp"])
            price_data.append({
                "open": float(sp.get("open", 0)),
                "high": float(sp.get("high", 0)),
                "low": float(sp.get("low", 0)),
                "close": float(sp.get("close", 0)),
                "volume": int(sp.get("volume", 0)),
            })

        # 运行本体增强预测
        prediction = service.predict_with_ontology(stock_code, price_data, 5)

        # 写入 Redis
        import json
        redis.set(
            f"prediction:{stock_code}",
            json.dumps(prediction, ensure_ascii=False, default=str),
            ex=3600  # 1 小时过期
        )

        logger.info(f"[预测任务] 预测刷新完成: {stock_code}")
        return {
            "status": "success",
            "stock_code": stock_code,
            "trend": prediction.get("trend"),
            "confidence": prediction.get("confidence"),
        }

    except Exception as e:
        logger.error(f"[预测任务] 预测刷新异常: {e}")
        return {"status": "error", "stock_code": stock_code, "message": str(e)}
