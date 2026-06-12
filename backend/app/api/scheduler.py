"""
调度器 API

提供定时任务的状态查询、手动触发、执行日志等管理功能。
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger
from datetime import datetime
import asyncio

router = APIRouter()


class SchedulerResponse(BaseModel):
    """调度器响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


# 任务注册表（改为直接调用函数）
TASK_REGISTRY = {
    "collect_market": {
        "module": "app.tasks.market_tasks",
        "function": "collect_daily_market_data",
        "name": "行情数据采集",
        "description": "采集所有公司的每日行情数据（OHLCV）",
    },
    "collect_news": {
        "module": "app.tasks.news_tasks",
        "function": "collect_news_and_events",
        "name": "新闻情报采集",
        "description": "采集热点新闻，LLM 自动分类事件",
    },
    "collect_financial": {
        "module": "app.tasks.financial_tasks",
        "function": "collect_financial_reports",
        "name": "财务数据采集",
        "description": "采集最新财务报告",
    },
    "reason_events": {
        "module": "app.tasks.reasoning_tasks",
        "function": "auto_reason_new_events",
        "name": "事件因果推理",
        "description": "自动推理新事件的影响传导链",
    },
    "refresh_reasoning": {
        "module": "app.tasks.reasoning_tasks",
        "function": "daily_reasoning_refresh",
        "name": "每日推理刷新",
        "description": "重新推理近 30 天活跃事件",
    },
    "scan_predictions": {
        "module": "app.tasks.prediction_tasks",
        "function": "daily_prediction_scan",
        "name": "每日预测扫描",
        "description": "扫描所有股票，筛选看涨标的",
    },
    "clear_cache": {
        "module": "app.tasks.monitoring",
        "function": "clear_expired_cache",
        "name": "缓存清理",
        "description": "清除过期缓存和因果链",
    },
}


@router.get("/status", response_model=SchedulerResponse)
async def get_scheduler_status():
    """获取所有任务状态"""
    try:
        from app.core.database import get_redis_client

        redis = get_redis_client()

        status = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {},
        }

        for task_key, task_info in TASK_REGISTRY.items():
            last_run = redis.get(f"task_last_run:{task_info['function']}")
            status["tasks"][task_key] = {
                "name": task_info["name"],
                "description": task_info["description"],
                "last_run": last_run if last_run else "从未执行",
            }

        # 缓存状态
        status["cache"] = {
            "daily_rising_stocks": bool(redis.exists("daily_rising_stocks")),
            "hot_topics": bool(redis.exists("hot_topics")),
        }

        return SchedulerResponse(data=status)
    except Exception as e:
        logger.error(f"获取调度状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=SchedulerResponse)
async def list_tasks():
    """列出所有可用任务"""
    tasks = []
    for task_key, task_info in TASK_REGISTRY.items():
        tasks.append({
            "key": task_key,
            "name": task_info["name"],
            "description": task_info["description"],
        })
    return SchedulerResponse(data=tasks)


@router.post("/trigger/{task_key}", response_model=SchedulerResponse)
async def trigger_task(task_key: str):
    """
    手动触发任务

    Args:
        task_key: 任务键名（如 collect_market, collect_news 等）
    """
    if task_key not in TASK_REGISTRY:
        raise HTTPException(status_code=404, detail=f"任务 '{task_key}' 不存在")

    try:
        task_info = TASK_REGISTRY[task_key]

        # 动态导入任务模块并直接调用（不使用 Celery）
        module = __import__(task_info["module"], fromlist=[task_info["function"]])
        task_func = getattr(module, task_info["function"])

        logger.info(f"开始执行任务: {task_key}")
        
        # 记录任务开始时间
        from app.core.database import get_redis_client
        redis = get_redis_client()
        redis.set(f"task_last_run:{task_info['function']}", datetime.now().isoformat())

        # 异步执行任务
        if asyncio.iscoroutinefunction(task_func):
            result = await task_func()
        else:
            # 同步函数包装为异步执行
            result = await asyncio.to_thread(task_func)

        logger.info(f"任务执行完成: {task_key}")

        return SchedulerResponse(data={
            "task_key": task_key,
            "task_name": task_info["name"],
            "status": "已完成",
            "result": str(result) if result else None,
        })
    except Exception as e:
        logger.error(f"触发任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{task_key}", response_model=SchedulerResponse)
async def get_task_logs(
    task_key: str,
    limit: int = Query(20, ge=1, le=100),
):
    """
    获取任务执行日志

    Args:
        task_key: 任务键名
        limit: 返回条数
    """
    if task_key not in TASK_REGISTRY:
        raise HTTPException(status_code=404, detail=f"任务 '{task_key}' 不存在")

    try:
        from app.core.database import get_redis_client
        import json

        redis = get_redis_client()
        task_info = TASK_REGISTRY[task_key]

        log_key = f"task_log:{task_info['task']}"
        logs = redis.lrange(log_key, 0, limit - 1)

        log_list = []
        for log in logs:
            try:
                log_list.append(json.loads(log))
            except Exception:
                continue

        return SchedulerResponse(data={
            "task_key": task_key,
            "task_name": task_info["name"],
            "logs": log_list,
        })
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/daily-rising", response_model=SchedulerResponse)
async def get_cached_rising_stocks():
    """获取缓存的每日看涨股票列表"""
    try:
        from app.core.database import get_redis_client
        import json

        redis = get_redis_client()
        cached = redis.get("daily_rising_stocks")

        if not cached:
            return SchedulerResponse(data=None, message="缓存为空，请等待每日预测扫描完成")

        data = json.loads(cached)
        return SchedulerResponse(data=data)
    except Exception as e:
        logger.error(f"获取缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
