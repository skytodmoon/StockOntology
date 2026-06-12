"""
因果链推理任务

自动推理新事件的影响链，更新累积影响分数。
"""

from loguru import logger


def auto_reason_new_events():
    """
    自动推理新事件的影响链

    触发方式：新事件入库后链式调用 / 每小时 30 分
    流程：
    1. 查询最近 1 小时内新增的 MarketEvent
    2. 对每个事件调用 OntologyReasoner.trace_impact_chain()
    3. 将因果链写入图谱
    4. 更新受影响公司的累积影响分数
    """
    from datetime import datetime
    from app.core.database import get_neo4j_client
    from app.core.graph import GraphBuilder
    from app.core.reasoning import OntologyReasoner

    logger.info("[推理任务] 开始自动推理新事件...")

    try:
        neo4j = get_neo4j_client()
        builder = GraphBuilder()
        reasoner = OntologyReasoner()

        # 1. 查询最近新增的事件（最近 2 小时内创建的）
        events = neo4j.execute_query("""
            MATCH (e:MarketEvent)
            WHERE e.createdAt IS NOT NULL
              AND datetime(e.createdAt) >= datetime() - duration({hours: 2})
            RETURN e.eventId AS eventId, e.title AS title, e.eventType AS eventType
            ORDER BY e.eventDate DESC
            LIMIT 20
        """)

        # 如果没有 createdAt 字段，查询最近的事件
        if not events:
            events = neo4j.execute_query("""
                MATCH (e:MarketEvent)
                WHERE NOT exists((e)-[:HAS_CHAIN]->(:CausalChain))
                RETURN e.eventId AS eventId, e.title AS title, e.eventType AS eventType
                ORDER BY e.eventDate DESC
                LIMIT 10
            """)

        if not events:
            logger.info("[推理任务] 无新事件需要推理")
            return {"status": "success", "events_reasoned": 0}

        logger.info(f"  待推理事件: {len(events)} 个")

        # 2. 对每个事件推理
        chains_created = 0
        for event in events:
            event_data = dict(event)
            event_id = event_data.get("eventId")
            title = event_data.get("title", "")

            try:
                # 推理因果链
                chain = reasoner.trace_impact_chain(event_id)

                if chain and chain.steps:
                    # 写入图谱
                    builder.save_causal_chain(chain)
                    chains_created += 1
                    logger.info(f"  ✓ {title[:30]}... → {len(chain.steps)} 步推理")

            except Exception as e:
                logger.warning(f"  ✗ 推理失败 [{event_id}]: {e}")
                continue

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "events_total": len(events),
            "chains_created": chains_created,
        }
        logger.info(f"[推理任务] 自动推理完成: {result}")

        # 3. 触发预测刷新
        if chains_created > 0:
            from .prediction_tasks import daily_prediction_scan
            # 不自动触发全量预测，太耗时
            # daily_prediction_scan.delay()

        return result

    except Exception as e:
        logger.error(f"[推理任务] 自动推理异常: {e}")
        raise self.retry(exc=e, countdown=60)


def daily_reasoning_refresh():
    """
    每日推理刷新

    触发时间：每日 19:00
    流程：
    1. 重新推理近 30 天的活跃事件
    2. 更新累积影响分数
    3. 清除过期因果链（>90天）
    """
    from datetime import datetime
    from app.core.database import get_neo4j_client
    from app.core.reasoning import OntologyReasoner

    logger.info("[推理任务] 开始每日推理刷新...")

    try:
        neo4j = get_neo4j_client()
        reasoner = OntologyReasoner()

        # 1. 获取近 30 天的事件
        events = neo4j.execute_query("""
            MATCH (e:MarketEvent)
            WHERE e.eventDate >= date() - duration({days: 30})
            RETURN e.eventId AS eventId, e.title AS title
            ORDER BY e.eventDate DESC
            LIMIT 50
        """)

        logger.info(f"  活跃事件: {len(events)} 个")

        # 2. 重新推理
        refreshed = 0
        for event in events:
            event_data = dict(event)
            event_id = event_data.get("eventId")

            try:
                chain = reasoner.trace_impact_chain(event_id)
                if chain and chain.steps:
                    # 删除旧的因果链
                    neo4j.execute_query("""
                        MATCH (cc:CausalChain {eventId: $eventId})
                        DETACH DELETE cc
                    """, {"eventId": event_id})

                    # 写入新的
                    from app.core.graph import GraphBuilder
                    builder = GraphBuilder()
                    builder.save_causal_chain(chain)
                    refreshed += 1

            except Exception as e:
                logger.warning(f"  刷新失败 [{event_id}]: {e}")
                continue

        # 3. 清除过期因果链
        neo4j.execute_query("""
            MATCH (cc:CausalChain)
            WHERE cc.timestamp < datetime() - duration({days: 90})
            DETACH DELETE cc
        """)

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "events_total": len(events),
            "chains_refreshed": refreshed,
        }
        logger.info(f"[推理任务] 每日推理刷新完成: {result}")
        return result

    except Exception as e:
        logger.error(f"[推理任务] 每日推理刷新异常: {e}")
        return {"status": "error", "message": str(e)}


def reason_single_event( event_id: str):
    """
    推理单个事件的影响链

    Args:
        event_id: 事件 ID

    用途：手动触发或事件驱动
    """
    from app.core.reasoning import OntologyReasoner
    from app.core.graph import GraphBuilder

    logger.info(f"[推理任务] 推理事件: {event_id}")

    try:
        reasoner = OntologyReasoner()
        builder = GraphBuilder()

        chain = reasoner.trace_impact_chain(event_id)

        if chain and chain.steps:
            builder.save_causal_chain(chain)
            logger.info(f"[推理任务] 完成: {len(chain.steps)} 步推理")
            return {
                "status": "success",
                "event_id": event_id,
                "steps": len(chain.steps),
                "confidence": chain.overall_confidence,
                "affected_companies": chain.total_affected_companies,
            }
        else:
            logger.info(f"[推理任务] 无推理步骤")
            return {"status": "success", "event_id": event_id, "steps": 0}

    except Exception as e:
        logger.error(f"[推理任务] 推理异常: {e}")
        return {"status": "error", "event_id": event_id, "message": str(e)}
