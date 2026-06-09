"""
字符串工具函数
"""

import re
from typing import Optional


def is_valid_stock_code(code: str) -> bool:
    """
    验证股票代码格式

    Args:
        code: 股票代码

    Returns:
        是否有效
    """
    # 6位数字
    return bool(re.match(r'^\d{6}$', code))


def format_stock_code(code: str, market: str = None) -> str:
    """
    格式化股票代码

    Args:
        code: 股票代码
        market: 市场代码（SH/SZ/BJ）

    Returns:
        格式化后的股票代码
    """
    # 移除空格
    code = code.strip()

    # 如果包含市场前缀，移除
    if code.startswith(('sh', 'sz', 'bj', 'SH', 'SZ', 'BJ')):
        code = code[2:]

    # 补齐6位
    code = code.zfill(6)

    return code


def get_stock_market(code: str) -> Optional[str]:
    """
    根据股票代码判断市场

    Args:
        code: 股票代码

    Returns:
        市场代码（SH/SZ/BJ），无法判断返回 None
    """
    code = format_stock_code(code)

    if code.startswith(('6', '9')):
        return 'SH'
    elif code.startswith(('0', '2', '3')):
        return 'SZ'
    elif code.startswith(('4', '8')):
        return 'BJ'
    return None


def extract_stock_codes(text: str) -> list[str]:
    """
    从文本中提取股票代码

    Args:
        text: 文本

    Returns:
        股票代码列表
    """
    # 匹配6位数字
    pattern = r'\b\d{6}\b'
    codes = re.findall(pattern, text)
    return list(set(codes))


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        s: 原字符串
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def camel_to_snake(name: str) -> str:
    """
    驼峰命名转下划线命名

    Args:
        name: 驼峰命名字符串

    Returns:
        下划线命名字符串
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name: str) -> str:
    """
    下划线命名转驼峰命名

    Args:
        name: 下划线命名字符串

    Returns:
        驼峰命名字符串
    """
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def clean_text(text: str) -> str:
    """
    清理文本

    Args:
        text: 原文本

    Returns:
        清理后的文本
    """
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾空白
    text = text.strip()
    return text


def extract_keywords(text: str, top_k: int = 10) -> list[str]:
    """
    提取关键词（简单实现）

    Args:
        text: 文本
        top_k: 返回数量

    Returns:
        关键词列表
    """
    # 简单的基于词频的关键词提取
    import jieba.analyse
    keywords = jieba.analyse.extract_tags(text, topK=top_k)
    return keywords
