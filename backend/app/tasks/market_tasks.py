"""
行情数据采集任务

定时采集股票行情数据，写入 Neo4j StockPrice 节点。
触发链：行情采集 → 本体更新 → 预测刷新
"""

from typing import List
from loguru import logger


def collect_daily_market_data():
    """
    每日行情数据采集

    触发时间：交易日 18:00（收盘后）
    流程：
    1. 从 Neo4j 获取所有 Company 节点
    2. 调用 AKShare 获取当日行情
    3. 写入 StockPrice 节点
    4. 创建 HAS_PRICE 关系
    5. 触发本体更新
    """
    from datetime import datetime, timedelta
    from app.core.database import get_neo4j_client
    from app.core.graph import GraphBuilder

    logger.info("[定时任务] 开始每日行情数据采集...")

    try:
        neo4j = get_neo4j_client()
        builder = GraphBuilder()

        # 1. 获取所有公司
        companies = neo4j.execute_query(
            "MATCH (c:Company) RETURN c.stockCode AS code, c.stockName AS name"
        )
        stock_codes = [dict(c)["code"] for c in companies]
        logger.info(f"  待采集公司: {len(stock_codes)} 家")

        # 2. 采集行情数据
        from app.core.data_sources import get_data_source_manager
        ds_manager = get_data_source_manager()

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

        success_count = 0
        fail_count = 0
        total_records = 0

        for code in stock_codes:
            try:
                # 使用数据源管理器获取K线数据
                kline_data = ds_manager.execute_with_fallback(
                    "get_daily_kline",
                    code,
                    start_date,
                    end_date,
                    5
                )

                if not kline_data:
                    fail_count += 1
                    continue

                # 写入数据
                for item in kline_data:
                    trade_date = item.get("trade_date", "")
                    # 检查是否已存在
                    existing = neo4j.execute_query(
                        "MATCH (sp:StockPrice {stockCode: $code, tradeDate: $date}) RETURN sp",
                        {"code": code, "date": trade_date}
                    )
                    if existing:
                        continue

                    price_data = {
                        "stock_code": code, "stockCode": code,
                        "trade_date": trade_date, "tradeDate": trade_date,
                        "open": float(item.get("open", 0)),
                        "high": float(item.get("high", 0)),
                        "low": float(item.get("low", 0)),
                        "close": float(item.get("close", 0)),
                        "volume": int(item.get("volume", 0)),
                        "amount": float(item.get("amount", 0)),
                        "change_pct": float(item.get("change_pct", 0)),
                        "turnover": float(item.get("turnover", 0)),
                    }
                    builder.create_stock_price(price_data)
                    total_records += 1

                success_count += 1

            except Exception as e:
                logger.warning(f"  采集 {code} 失败: {e}")
                fail_count += 1

        # 3. 创建 HAS_PRICE 关系（增量）
        neo4j.execute_query("""
            MATCH (sp:StockPrice)
            MATCH (c:Company {stockCode: sp.stockCode})
            WHERE NOT (c)-[:HAS_PRICE]->(sp)
            MERGE (c)-[:HAS_PRICE]->(sp)
        """)

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "companies_total": len(stock_codes),
            "companies_success": success_count,
            "companies_failed": fail_count,
            "new_records": total_records,
        }
        logger.info(f"[定时任务] 行情采集完成: {result}")

        # 4. 触发本体更新
        from .ontology_tasks import update_ontology_after_data_change
        try:
            update_ontology_after_data_change("market")
        except Exception as e:
            logger.warning(f"触发本体更新失败: {e}")

        return result

    except Exception as e:
        logger.error(f"[定时任务] 行情采集异常: {e}")
        return {"status": "error", "message": str(e)}


def collect_realtime_data( stock_codes: List[str] = None):
    """
    实时行情采集（盘中）

    Args:
        stock_codes: 股票代码列表，None 则采集所有
    """
    from datetime import datetime
    from app.core.collectors.market_collector import MarketDataCollector

    logger.info(f"[定时任务] 实时行情采集: {stock_codes or '所有股票'}")

    try:
        collector = MarketDataCollector()
        data = collector.collect_realtime(stock_codes or [])

        # 写入 Redis 缓存（实时数据不入图谱）
        from app.core.database import get_redis_client
        redis = get_redis_client()

        import json
        for item in data:
            code = item.get("stockCode", item.get("code", ""))
            if code:
                redis.set(
                    f"realtime:{code}",
                    json.dumps(item, ensure_ascii=False),
                    ex=300  # 5 分钟过期
                )

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "count": len(data),
        }
        logger.info(f"[定时任务] 实时行情采集完成: {result}")
        return result

    except Exception as e:
        logger.error(f"[定时任务] 实时行情采集异常: {e}")
        raise self.retry(exc=e, countdown=30)
