"""
Celery 应用配置

提供 Celery 实例、定时任务调度（beat schedule）和任务自动发现。
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "stock_ontology",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery 配置
celery_app.conf.update(
    # 序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,

    # 任务执行
    task_track_started=True,
    task_time_limit=600,          # 单任务最大执行时间 10 分钟
    task_soft_time_limit=300,     # 软超时 5 分钟
    task_acks_late=True,          # 任务完成后确认
    worker_prefetch_multiplier=1, # 每次只预取 1 个任务

    # 重试策略
    task_default_retry_delay=60,  # 默认重试间隔 60 秒
    task_max_retries=3,           # 最大重试次数

    # 结果过期
    result_expires=3600,          # 结果保留 1 小时

    # 日志
    worker_hijack_root_logger=False,
)

# ==================== 定时任务调度表 ====================
celery_app.conf.beat_schedule = {
    # ---- 行情数据采集 ----
    "collect-daily-market-data": {
        "task": "app.tasks.market_tasks.collect_daily_market_data",
        "schedule": crontab(hour=18, minute=0, day_of_week="mon-fri"),
        "args": (),
        "options": {"queue": "default"},
    },

    # ---- 新闻情报采集 ----
    "collect-news-hourly": {
        "task": "app.tasks.news_tasks.collect_news_and_events",
        "schedule": crontab(minute=0, hour="9-23"),  # 9:00-23:00 每小时
        "args": (),
        "options": {"queue": "default"},
    },

    # ---- 财务数据采集 ----
    "collect-financial-weekly": {
        "task": "app.tasks.financial_tasks.collect_financial_reports",
        "schedule": crontab(hour=9, minute=0, day_of_week="mon"),
        "args": (),
        "options": {"queue": "default"},
    },

    # ---- 公司信息更新 ----
    "update-company-info-daily": {
        "task": "app.tasks.financial_tasks.update_company_info",
        "schedule": crontab(hour=18, minute=30, day_of_week="mon-fri"),
        "args": (),
        "options": {"queue": "default"},
    },

    # ---- 新事件自动推理 ----
    "auto-reason-new-events": {
        "task": "app.tasks.reasoning_tasks.auto_reason_new_events",
        "schedule": crontab(minute=30, hour="9-23"),  # 每小时 30 分
        "args": (),
        "options": {"queue": "default"},
    },

    # ---- 每日推理刷新 ----
    "daily-reasoning-refresh": {
        "task": "app.tasks.reasoning_tasks.daily_reasoning_refresh",
        "schedule": crontab(hour=19, minute=0, day_of_week="mon-fri"),
        "args": (),
        "options": {"queue": "default"},
    },

    # ---- 每日预测扫描 ----
    "daily-prediction-scan": {
        "task": "app.tasks.prediction_tasks.daily_prediction_scan",
        "schedule": crontab(hour=20, minute=0, day_of_week="mon-fri"),
        "args": (),
        "options": {"queue": "default"},
    },

    # ---- 缓存清理 ----
    "clear-expired-cache": {
        "task": "app.tasks.monitoring.clear_expired_cache",
        "schedule": crontab(hour=3, minute=0),
        "args": (),
        "options": {"queue": "default"},
    },
}

# 自动发现任务模块
celery_app.autodiscover_tasks([
    "app.tasks.market_tasks",
    "app.tasks.news_tasks",
    "app.tasks.financial_tasks",
    "app.tasks.ontology_tasks",
    "app.tasks.reasoning_tasks",
    "app.tasks.prediction_tasks",
    "app.tasks.monitoring",
])
