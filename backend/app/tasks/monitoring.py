"""
任务监控

提供任务状态查询、执行日志、缓存清理等运维功能。
"""

from loguru import logger


def clear_expired_cache():
    """
    清除过期缓存

    触发时间：每日 03:00
    流程：
    1. 清除过期的 Redis 缓存
    2. 清除过期的预测结果
    3. 清除过期的因果链（>90天）
    """
    from datetime import datetime
    from app.core.database import get_redis_client, get_neo4j_client

    logger.info("[监控任务] 清除过期缓存...")

    try:
        redis = get_redis_client()
        neo4j = get_neo4j_client()

        # 1. 清除过期的实时行情缓存
        realtime_keys = redis.keys("realtime:*")
        if realtime_keys:
            redis.delete(*realtime_keys)
            logger.info(f"  清除实时行情缓存: {len(realtime_keys)} 个")

        # 2. 清除过期的预测缓存（保留 daily_rising_stocks）
        prediction_keys = redis.keys("prediction:*")
        if prediction_keys:
            redis.delete(*prediction_keys)
            logger.info(f"  清除预测缓存: {len(prediction_keys)} 个")

        # 3. 清除过期的因果链
        neo4j.execute_query("""
            MATCH (cc:CausalChain)
            WHERE cc.timestamp < datetime() - duration({days: 90})
            DETACH DELETE cc
        """)

        # 4. 清除过期的推理步骤
        neo4j.execute_query("""
            MATCH (rs:ReasoningStep)
            WHERE rs.timestamp < datetime() - duration({days: 90})
            DETACH DELETE rs
        """)

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "cleared_realtime_keys": len(realtime_keys or []),
            "cleared_prediction_keys": len(prediction_keys or []),
        }
        logger.info(f"[监控任务] 缓存清理完成: {result}")
        return result

    except Exception as e:
        logger.error(f"[监控任务] 缓存清理异常: {e}")
        return {"status": "error", "message": str(e)}


def get_task_status():
    """
    获取所有任务状态

    Returns:
        任务状态字典
    """
    from datetime import datetime
    from app.core.database import get_redis_client

    try:
        redis = get_redis_client()

        # 获取任务状态
        status = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {},
        }

        # 检查各任务的最后执行时间
        task_names = [
            "collect_daily_market_data",
            "collect_news_and_events",
            "collect_financial_reports",
            "auto_reason_new_events",
            "daily_prediction_scan",
        ]

        for task_name in task_names:
            last_run = redis.get(f"task_last_run:{task_name}")
            status["tasks"][task_name] = {
                "last_run": last_run.decode() if last_run else "never",
            }

        # 检查缓存状态
        status["cache"] = {
            "daily_rising_stocks": redis.exists("daily_rising_stocks"),
            "hot_topics": redis.exists("hot_topics"),
        }

        return status

    except Exception as e:
        logger.error(f"[监控任务] 获取状态异常: {e}")
        return {"status": "error", "message": str(e)}


def record_task_execution(task_name: str, status: str, duration: float = 0):
    """
    记录任务执行日志

    Args:
        task_name: 任务名称
        status: 执行状态（success/error）
        duration: 执行时长（秒）
    """
    from datetime import datetime
    from app.core.database import get_redis_client
    import json

    try:
        redis = get_redis_client()

        # 记录最后执行时间
        redis.set(f"task_last_run:{task_name}", datetime.now().isoformat())

        # 记录执行日志（保留最近 100 条）
        log_entry = {
            "task": task_name,
            "status": status,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

        log_key = f"task_log:{task_name}"
        redis.lpush(log_key, json.dumps(log_entry))
        redis.ltrim(log_key, 0, 99)  # 保留最近 100 条

    except Exception as e:
        logger.warning(f"记录任务执行日志失败: {e}")
