"""
新闻情报采集任务

定时采集新闻情报，通过 LLM 自动识别事件类型和受影响实体。
触发链：新闻采集 → LLM 事件分类 → 图谱写入 → 因果链推理
"""

from loguru import logger


def collect_news_and_events():
    """
    新闻情报采集

    触发时间：每小时 9:00-23:00
    流程：
    1. 调用 NewsCollector 采集热点新闻
    2. LLM 自动分类事件类型（PolicyEvent/CompanyEvent/MacroEvent）
    3. LLM 提取受影响公司/行业
    4. 写入 MarketEvent 节点
    5. 创建 IMPACTS 关系
    6. 触发因果链推理
    """
    from datetime import datetime
    from app.core.collectors.news_collector import NewsCollector
    from app.core.database import get_neo4j_client, get_redis_client
    from app.core.graph import GraphBuilder

    logger.info("[定时任务] 开始新闻情报采集...")

    try:
        neo4j = get_neo4j_client()
        builder = GraphBuilder()
        redis = get_redis_client()

        # 1. 采集新闻
        collector = NewsCollector()
        news_list = collector.start(keyword=None, stock_code=None, limit=50)

        if not news_list:
            logger.info("[定时任务] 未采集到新闻")
            return {"status": "success", "count": 0}

        logger.info(f"  采集到 {len(news_list)} 条新闻")

        # 2. 去重（与已有事件对比）
        new_events = []
        for news in news_list:
            title = news.get("title", "")
            if not title:
                continue

            # 检查是否已存在
            existing = neo4j.execute_query(
                "MATCH (e:MarketEvent {title: $title}) RETURN e",
                {"title": title}
            )
            if existing:
                continue

            new_events.append(news)

        if not new_events:
            logger.info("[定时任务] 无新事件")
            return {"status": "success", "count": 0, "new": 0}

        logger.info(f"  新事件: {len(new_events)} 条")

        # 3. LLM 事件分类
        try:
            from app.core.reasoning import OntologyReasoner
            reasoner = OntologyReasoner()
        except Exception:
            reasoner = None

        events_created = 0
        for i, news in enumerate(new_events[:20]):  # 限制每批处理 20 条
            try:
                title = news.get("title", "")
                content = news.get("content", title)

                # LLM 分类
                event_type = "CompanyEvent"  # 默认
                impact_level = "Low"
                affected_companies = []

                if reasoner:
                    classification = reasoner.classify_event(content)
                    event_type = classification.get("event_type", "CompanyEvent")

                    # 根据影响级别判断
                    if classification.get("confidence", 0) > 0.7:
                        impact_level = "Medium"
                    if any(kw in content for kw in ["重大", "突发", "紧急", "全球"]):
                        impact_level = "High"

                # 生成事件 ID
                event_id = f"EVT_{datetime.now().strftime('%Y%m%d')}_{i:04d}"

                # 4. 写入 MarketEvent 节点
                event_data = {
                    "eventId": event_id,
                    "title": title,
                    "content": content,
                    "eventType": event_type,
                    "eventDate": datetime.now().strftime("%Y-%m-%d"),
                    "impactLevel": impact_level,
                    "source": news.get("source", "news"),
                    "url": news.get("url", ""),
                }
                builder.create_event(event_data)
                events_created += 1

                # 5. 尝试关联公司（通过关键词匹配）
                companies = neo4j.execute_query(
                    "MATCH (c:Company) RETURN c.stockCode AS code, c.stockName AS name"
                )
                for comp in companies:
                    comp_data = dict(comp)
                    if comp_data["name"] in content or comp_data["code"] in content:
                        builder.create_event_impact_relationship(
                            event_id, comp_data["code"], "Company",
                            {"impactDirection": "neutral", "reason": "新闻提及"}
                        )

                logger.info(f"  [{i+1}] {event_type}: {title[:30]}...")

            except Exception as e:
                logger.warning(f"  处理新闻失败: {e}")
                continue

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_collected": len(news_list),
            "new_events": len(new_events),
            "events_created": events_created,
        }
        logger.info(f"[定时任务] 新闻采集完成: {result}")

        # 6. 触发因果链推理
        if events_created > 0:
            from .reasoning_tasks import auto_reason_new_events
            try:
                auto_reason_new_events()
            except Exception as e:
                logger.warning(f"触发因果链推理失败: {e}")

        return result

    except Exception as e:
        logger.error(f"[定时任务] 新闻采集异常: {e}")
        return {"status": "error", "message": str(e)}


def collect_hot_topics():
    """
    热门概念/题材采集

    采集市场热门概念板块，用于补充行业分类。
    """
    from datetime import datetime
    from app.core.collectors.news_collector import NewsCollector
    from app.core.database import get_redis_client

    logger.info("[定时任务] 采集热门概念...")

    try:
        collector = NewsCollector()
        topics = collector.collect_hot_topics()

        # 写入 Redis 缓存
        import json
        redis = get_redis_client()
        redis.set(
            "hot_topics",
            json.dumps(topics, ensure_ascii=False),
            ex=3600  # 1 小时过期
        )

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "count": len(topics),
        }
        logger.info(f"[定时任务] 热门概念采集完成: {result}")
        return result

    except Exception as e:
        logger.error(f"[定时任务] 热门概念采集异常: {e}")
        raise self.retry(exc=e, countdown=30)
