"""
工具函数测试
"""

import pytest
from datetime import date, datetime, timedelta

from app.utils.datetime_utils import (
    format_date,
    parse_date,
    format_datetime,
    parse_datetime,
    get_today,
    get_now,
    add_days,
    get_trade_dates,
    is_trade_day,
    get_recent_trade_day,
)
from app.utils.string_utils import (
    is_valid_stock_code,
    format_stock_code,
    get_stock_market,
    extract_stock_codes,
    truncate_string,
    camel_to_snake,
    snake_to_camel,
    clean_text,
)
from app.utils.number_utils import (
    format_number,
    format_percentage,
    format_large_number,
    format_market_cap,
    calculate_change,
    format_change,
    safe_divide,
    calculate_moving_average,
    calculate_ema,
    normalize_value,
)


class TestDatetimeUtils:
    """日期时间工具测试"""

    def test_format_date(self):
        """测试日期格式化"""
        d = date(2024, 1, 15)
        assert format_date(d) == "2024-01-15"
        assert format_date(d, "%Y/%m/%d") == "2024/01/15"

    def test_parse_date(self):
        """测试日期解析"""
        d = parse_date("2024-01-15")
        assert d == date(2024, 1, 15)

        # 无效日期
        assert parse_date("invalid") is None

    def test_format_datetime(self):
        """测试日期时间格式化"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        assert format_datetime(dt) == "2024-01-15 10:30:00"

    def test_parse_datetime(self):
        """测试日期时间解析"""
        dt = parse_datetime("2024-01-15 10:30:00")
        assert dt == datetime(2024, 1, 15, 10, 30, 0)

    def test_get_today(self):
        """测试获取今天"""
        today = get_today()
        assert isinstance(today, date)

    def test_get_now(self):
        """测试获取当前时间"""
        now = get_now()
        assert isinstance(now, datetime)

    def test_add_days(self):
        """测试日期加减"""
        d = date(2024, 1, 15)
        assert add_days(d, 5) == date(2024, 1, 20)
        assert add_days(d, -5) == date(2024, 1, 10)

    def test_is_trade_day(self):
        """测试是否是交易日"""
        # 周一
        monday = date(2024, 1, 15)
        assert is_trade_day(monday) is True

        # 周六
        saturday = date(2024, 1, 13)
        assert is_trade_day(saturday) is False

    def test_get_trade_dates(self):
        """测试获取交易日期"""
        start = date(2024, 1, 13)  # 周六
        end = date(2024, 1, 19)  # 周五
        trade_dates = get_trade_dates(start, end)
        assert len(trade_dates) == 5  # 周一到周五

    def test_get_recent_trade_day(self):
        """测试获取最近交易日"""
        # 如果今天是交易日，返回今天
        today = get_today()
        recent = get_recent_trade_day(today)
        assert recent.weekday() < 5


class TestStringUtils:
    """字符串工具测试"""

    def test_is_valid_stock_code(self):
        """测试股票代码验证"""
        assert is_valid_stock_code("600519") is True
        assert is_valid_stock_code("000001") is True
        assert is_valid_stock_code("abc") is False
        assert is_valid_stock_code("12345") is False

    def test_format_stock_code(self):
        """测试股票代码格式化"""
        assert format_stock_code("600519") == "600519"
        assert format_stock_code("519") == "000519"
        assert format_stock_code("SH600519") == "600519"

    def test_get_stock_market(self):
        """测试获取股票市场"""
        assert get_stock_market("600519") == "SH"  # 上海
        assert get_stock_market("000001") == "SZ"  # 深圳
        assert get_stock_market("300001") == "SZ"  # 创业板
        assert get_stock_market("430001") == "BJ"  # 北京

    def test_extract_stock_codes(self):
        """测试提取股票代码"""
        text = "贵州茅台600519和五粮液000858都是白酒股"
        codes = extract_stock_codes(text)
        assert "600519" in codes
        assert "000858" in codes

    def test_truncate_string(self):
        """测试截断字符串"""
        s = "这是一段很长的文本"
        assert len(truncate_string(s, 5)) == 5
        assert truncate_string(s, 100) == s

    def test_camel_to_snake(self):
        """测试驼峰转下划线"""
        assert camel_to_snake("stockCode") == "stock_code"
        assert camel_to_snake("marketCap") == "market_cap"

    def test_snake_to_camel(self):
        """测试下划线转驼峰"""
        assert snake_to_camel("stock_code") == "stockCode"
        assert snake_to_camel("market_cap") == "marketCap"

    def test_clean_text(self):
        """测试清理文本"""
        text = "  这是  一段   文本  "
        assert clean_text(text) == "这是 一段 文本"


class TestNumberUtils:
    """数字工具测试"""

    def test_format_number(self):
        """测试数字格式化"""
        assert format_number(1234567.89) == "1,234,567.89"
        assert format_number(1234567.89, use_comma=False) == "1234567.89"
        assert format_number(None) == "N/A"

    def test_format_percentage(self):
        """测试百分比格式化"""
        assert format_percentage(0.1234) == "12.34%"
        assert format_percentage(12.34, multiply=False) == "12.34%"
        assert format_percentage(None) == "N/A"

    def test_format_large_number(self):
        """测试大数字格式化"""
        assert "万亿" in format_large_number(1500000000000)
        assert "亿" in format_large_number(150000000)
        assert "万" in format_large_number(15000)

    def test_format_market_cap(self):
        """测试市值格式化"""
        assert "万亿" in format_market_cap(2100000000000)

    def test_calculate_change(self):
        """测试计算变化"""
        change, rate = calculate_change(110, 100)
        assert change == 10
        assert rate == 0.1

    def test_format_change(self):
        """测试格式化变化"""
        assert "+" in format_change(10, 0.1)
        assert "-" in format_change(-10, -0.1)

    def test_safe_divide(self):
        """测试安全除法"""
        assert safe_divide(10, 2) == 5
        assert safe_divide(10, 0) == 0
        assert safe_divide(10, 0, default=-1) == -1

    def test_calculate_moving_average(self):
        """测试移动平均"""
        data = [1, 2, 3, 4, 5]
        ma = calculate_moving_average(data, 3)
        assert ma[0] is None
        assert ma[1] is None
        assert ma[2] == 2.0
        assert ma[3] == 3.0
        assert ma[4] == 4.0

    def test_calculate_ema(self):
        """测试指数移动平均"""
        data = [1, 2, 3, 4, 5]
        ema = calculate_ema(data, 3)
        assert ema[0] is None
        assert ema[1] is None
        assert ema[2] == 2.0  # 第一个 EMA 是 SMA

    def test_normalize_value(self):
        """测试归一化"""
        assert normalize_value(5, 0, 10, 0, 1) == 0.5
        assert normalize_value(0, 0, 10, 0, 1) == 0
        assert normalize_value(10, 0, 10, 0, 1) == 1
