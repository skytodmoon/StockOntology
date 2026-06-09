"""
数据采集模块

提供多源数据采集功能。
"""

from .base_collector import BaseCollector
from .collector_manager import CollectorManager

__all__ = [
    "BaseCollector",
    "CollectorManager",
]
