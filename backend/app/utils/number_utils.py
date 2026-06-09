"""
数字工具函数
"""

from typing import Optional, Union


def format_number(
    value: Union[int, float],
    precision: int = 2,
    use_comma: bool = True,
) -> str:
    """
    格式化数字

    Args:
        value: 数值
        precision: 小数位数
        use_comma: 是否使用千位分隔符

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "N/A"

    if use_comma:
        return f"{value:,.{precision}f}"
    return f"{value:.{precision}f}"


def format_percentage(
    value: Union[int, float],
    precision: int = 2,
    multiply: bool = True,
) -> str:
    """
    格式化百分比

    Args:
        value: 数值（0.1 表示 10%）
        precision: 小数位数
        multiply: 是否需要乘以100

    Returns:
        格式化后的百分比字符串
    """
    if value is None:
        return "N/A"

    if multiply:
        value = value * 100

    return f"{value:.{precision}f}%"


def format_large_number(value: Union[int, float]) -> str:
    """
    格式化大数字（带单位）

    Args:
        value: 数值

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "N/A"

    if abs(value) >= 1e12:
        return f"{value / 1e12:.2f}万亿"
    elif abs(value) >= 1e8:
        return f"{value / 1e8:.2f}亿"
    elif abs(value) >= 1e4:
        return f"{value / 1e4:.2f}万"
    else:
        return f"{value:.2f}"


def format_market_cap(value: Union[int, float]) -> str:
    """
    格式化市值

    Args:
        value: 市值（元）

    Returns:
        格式化后的字符串
    """
    return format_large_number(value)


def calculate_change(
    current: float,
    previous: float,
) -> tuple[float, float]:
    """
    计算变化量和变化率

    Args:
        current: 当前值
        previous: 之前值

    Returns:
        (变化量, 变化率)
    """
    if previous is None or previous == 0:
        return (0, 0)

    change = current - previous
    change_rate = change / previous

    return (change, change_rate)


def format_change(
    change: float,
    change_rate: float,
) -> str:
    """
    格式化变化

    Args:
        change: 变化量
        change_rate: 变化率

    Returns:
        格式化后的字符串
    """
    if change >= 0:
        return f"+{change:.2f} (+{change_rate * 100:.2f}%)"
    else:
        return f"{change:.2f} ({change_rate * 100:.2f}%)"


def safe_divide(
    numerator: Union[int, float],
    denominator: Union[int, float],
    default: float = 0.0,
) -> float:
    """
    安全除法（避免除零错误）

    Args:
        numerator: 分子
        denominator: 分母
        default: 默认值

    Returns:
        除法结果
    """
    if denominator is None or denominator == 0:
        return default
    return numerator / denominator


def calculate_moving_average(
    data: list[float],
    window: int,
) -> list[Optional[float]]:
    """
    计算移动平均

    Args:
        data: 数据列表
        window: 窗口大小

    Returns:
        移动平均列表
    """
    if len(data) < window:
        return [None] * len(data)

    result = []
    for i in range(len(data)):
        if i < window - 1:
            result.append(None)
        else:
            avg = sum(data[i - window + 1:i + 1]) / window
            result.append(avg)

    return result


def calculate_ema(
    data: list[float],
    window: int,
) -> list[Optional[float]]:
    """
    计算指数移动平均

    Args:
        data: 数据列表
        window: 窗口大小

    Returns:
        指数移动平均列表
    """
    if len(data) < window:
        return [None] * len(data)

    multiplier = 2 / (window + 1)
    result = [None] * (window - 1)

    # 第一个 EMA 使用 SMA
    first_ema = sum(data[:window]) / window
    result.append(first_ema)

    # 后续 EMA
    for i in range(window, len(data)):
        ema = (data[i] - result[-1]) * multiplier + result[-1]
        result.append(ema)

    return result


def normalize_value(
    value: float,
    min_val: float,
    max_val: float,
    new_min: float = 0,
    new_max: float = 1,
) -> float:
    """
    归一化数值

    Args:
        value: 原始值
        min_val: 原始最小值
        max_val: 原始最大值
        new_min: 新最小值
        new_max: 新最大值

    Returns:
        归一化后的值
    """
    if max_val == min_val:
        return (new_min + new_max) / 2

    return (value - min_val) / (max_val - min_val) * (new_max - new_min) + new_min
