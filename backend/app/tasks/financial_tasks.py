"""
财务数据采集任务

定时采集财务报告和公司基本信息。
"""

from loguru import logger


def collect_financial_reports():
    """
    财务数据采集

    触发时间：每周一 09:00 / 财报季加密
    流程：
    1. 从 Neo4j 获取所有公司
    2. 调用 FinancialDataCollector 采集最新财报
    3. 写入 FinancialReport 节点
    4. 创建公司-报告关系
    """
    from datetime import datetime
    from app.core.database import get_neo4j_client
    from app.core.graph import GraphBuilder
    from app.core.collectors.market_collector import MarketDataCollector

    neo4j = get_neo4j_client()
    builder = GraphBuilder()

    # 获取所有公司
    result = neo4j.execute_query('''
        MATCH (c:Company)
        RETURN c.stockCode AS code, c.stockName AS name
    ''')
    companies = [dict(r) for r in result]

    if not companies:
        return

    success = 0
    for comp in companies:
        code = comp["code"]
        name = comp["name"]

        try:
            # 采集最新财报
            collector = MarketDataCollector()
            raw_data = collector.collect(stock_codes=[code])
            if not raw_data:
                continue

            # 取最新的一条
            latest = raw_data[-1]
            report_data = {
                "stockCode": code,
                "reportDate": latest.get("tradeDate", datetime.now().strftime("%Y-%m-%d")),
                "reportType": "quarterly",
                "eps": latest.get("eps", 0),
                "revenue": latest.get("revenue", 0),
                "netProfit": latest.get("netProfit", 0),
            }

            # 写入图谱
            builder.create_financial_report(report_data)
            builder.create_company_report_relationship(
                code, report_data["reportDate"], report_data["reportType"]
            )
            success += 1

        except Exception as e:
            logger.warning(f"Failed to collect financial data for {code}: {e}")

    logger.info(f"Financial data collection completed: {success}/{len(companies)}")
