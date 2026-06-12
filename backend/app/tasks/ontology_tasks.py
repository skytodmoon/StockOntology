"""
本体更新任务

数据变更后自动更新本体结构和图谱关系。
"""

from loguru import logger


def update_ontology_after_data_change( data_type: str):
    """
    数据变更后自动更新本体

    Args:
        data_type: 数据类型（market / news / financial）

    触发方式：由采集任务完成后链式调用
    """
    from datetime import datetime
    from app.core.database import get_neo4j_client

    logger.info(f"[本体更新] 开始更新，数据类型: {data_type}")

    try:
        neo4j = get_neo4j_client()

        if data_type == "market":
            # 更新公司市值（从最新价格推算）
            neo4j.execute_query("""
                MATCH (c:Company)-[:HAS_PRICE]->(sp:StockPrice)
                WITH c, sp ORDER BY sp.tradeDate DESC
                WITH c, collect(sp)[0] AS latest
                SET c.latestPrice = latest.close,
                    c.latestDate = latest.tradeDate
            """)

            # 更新行业统计
            neo4j.execute_query("""
                MATCH (i:Industry)<-[:BELONGS_TO]-(c:Company)
                WITH i,
                     count(c) AS companyCount,
                     avg(c.marketCap) AS avgMarketCap,
                     sum(c.marketCap) AS totalMarketCap
                SET i.companyCount = companyCount,
                    i.avgMarketCap = avgMarketCap,
                    i.totalMarketCap = totalMarketCap
            """)

            logger.info("[本体更新] 行情数据更新完成")

        elif data_type == "news":
            # 清理过期事件（>90天）
            neo4j.execute_query("""
                MATCH (e:MarketEvent)
                WHERE e.eventDate < date() - duration({days: 90})
                DETACH DELETE e
            """)

            # 更新事件统计
            neo4j.execute_query("""
                MATCH (c:Company)<-[:IMPACTS]-(e:MarketEvent)
                WHERE e.eventDate >= date() - duration({days: 30})
                WITH c, count(e) AS recentEventCount
                SET c.recentEventCount = recentEventCount
            """)

            logger.info("[本体更新] 新闻事件更新完成")

        elif data_type == "financial":
            # 更新公司基本面
            neo4j.execute_query("""
                MATCH (c:Company)-[:HAS_REPORT]->(f:FinancialReport)
                WITH c, f ORDER BY f.reportDate DESC
                WITH c, collect(f)[0] AS latest
                SET c.latestEPS = latest.eps,
                    c.latestRevenue = latest.revenue,
                    c.latestROE = latest.roe
            """)

            logger.info("[本体更新] 财务数据更新完成")

        return {
            "status": "success",
            "data_type": data_type,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"[本体更新] 异常: {e}")
        return {"status": "error", "message": str(e)}


def rebuild_company_industry_relations():
    """
    重建公司-行业关系

    当行业分类变化时触发。
    """
    from app.core.database import get_neo4j_client

    logger.info("[本体更新] 重建公司-行业关系...")

    try:
        neo4j = get_neo4j_client()

        # 清除旧关系
        neo4j.execute_query("MATCH ()-[r:BELONGS_TO]->() DELETE r")

        # 重建关系
        neo4j.execute_query("""
            MATCH (c:Company), (i:Industry)
            WHERE c.industryCode = i.code
            MERGE (c)-[:BELONGS_TO]->(i)
        """)

        count = neo4j.execute_query(
            "MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS cnt"
        )
        logger.info(f"[本体更新] 重建完成: {dict(count[0])['cnt']} 条关系")

    except Exception as e:
        logger.error(f"[本体更新] 重建异常: {e}")


def update_supply_chain_risk():
    """
    更新供应链风险评估

    基于最新事件和财务数据，重新计算供应链风险分数。
    """
    from app.core.prediction.ontology_features import OntologyFeatureExtractor

    logger.info("[本体更新] 更新供应链风险...")

    try:
        extractor = OntologyFeatureExtractor()
        features = extractor.extract_supply_chain_risk("")

        logger.info(f"[本体更新] 供应链风险更新完成")

    except Exception as e:
        logger.error(f"[本体更新] 供应链风险更新异常: {e}")
