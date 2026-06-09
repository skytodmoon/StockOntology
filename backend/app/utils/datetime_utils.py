"""
日期时间工具函数
"""

from datetime import date, datetime, timedelta
from typing import Optional


def format_date(d: date, format_str: str = "%Y-%m-%d") -> str:
    """
    格式化日期

    Args:
        d: 日期对象
        format_str: 格式字符串

    Returns:
        格式化后的日期字符串
    """
    return d.strftime(format_str)


def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[date]:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串
        format_str: 格式字符串

    Returns:
        日期对象，解析失败返回 None
    """
    try:
        return datetime.strptime(date_str, format_str).date()
    except ValueError:
        return None


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间

    Args:
        dt: 日期时间对象
        format_str: 格式字符串

    Returns:
        格式化后的日期时间字符串
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    解析日期时间字符串

    Args:
        dt_str: 日期时间字符串
        format_str: 格式字符串

    Returns:
        日期时间对象，解析失败返回 None
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        return None


def get_today() -> date:
    """获取今天的日期"""
    return date.today()


def get_now() -> datetime:
    """获取当前时间"""
    return datetime.now()


def add_days(d: date, days: int) -> date:
    """
    日期加减天数

    Args:
        d: 日期
        days: 天数（可以为负数）

    Returns:
        计算后的日期
    """
    return d + timedelta(days=days)


def get_trade_dates(
    start_date: date,
    end_date: date,
) -> list[date]:
    """
    获取交易日期列表（排除周末）

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        交易日期列表
    """
    trade_dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 0-4 是周一到周五
            trade_dates.append(current)
        current += timedelta(days=1)
    return trade_dates


def is_trade_day(d: date) -> bool:
    """
    判断是否是交易日（仅排除周末，不考虑节假日）

    Args:
        d: 日期

    Returns:
        是否是交易日
    """
    return d.weekday() < 5


def get_recent_trade_day(d: date = None) -> date:
    """
    获取最近的交易日

    Args:
        d: 日期，默认为今天

    Returns:
        最近的交易日
    """
    if d is None:
        d = date.today()

    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d
