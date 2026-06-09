"""
采集器管理器

管理所有数据采集器的生命周期。
"""

from typing import Any, Dict, List, Optional, Type
from loguru import logger

from .base_collector import BaseCollector


class CollectorManager:
    """采集器管理器"""

    def __init__(self):
        """初始化采集器管理器"""
        self._collectors: Dict[str, BaseCollector] = {}
        self._collector_classes: Dict[str, Type[BaseCollector]] = {}

    def register(self, collector_class: Type[BaseCollector]):
        """
        注册采集器类

        Args:
            collector_class: 采集器类
        """
        name = collector_class.__name__
        self._collector_classes[name] = collector_class
        logger.info(f"Registered collector: {name}")

    def create(
        self,
        name: str,
        collector_name: str = None,
        config: Dict[str, Any] = None,
    ) -> Optional[BaseCollector]:
        """
        创建采集器实例

        Args:
            name: 采集器类名
            collector_name: 实例名称
            config: 配置参数

        Returns:
            采集器实例
        """
        if name not in self._collector_classes:
            logger.error(f"Collector class not found: {name}")
            return None

        instance_name = collector_name or name
        collector_class = self._collector_classes[name]
        collector = collector_class(instance_name, config)
        self._collectors[instance_name] = collector

        logger.info(f"Created collector: {instance_name}")
        return collector

    def get(self, name: str) -> Optional[BaseCollector]:
        """
        获取采集器实例

        Args:
            name: 实例名称

        Returns:
            采集器实例
        """
        return self._collectors.get(name)

    def remove(self, name: str) -> bool:
        """
        移除采集器实例

        Args:
            name: 实例名称

        Returns:
            是否移除成功
        """
        if name in self._collectors:
            collector = self._collectors[name]
            if collector.is_running:
                collector.stop()
            del self._collectors[name]
            logger.info(f"Removed collector: {name}")
            return True
        return False

    def list_collectors(self) -> List[Dict[str, Any]]:
        """
        列出所有采集器

        Returns:
            采集器列表
        """
        return [collector.get_status() for collector in self._collectors.values()]

    def list_classes(self) -> List[str]:
        """
        列出所有注册的采集器类

        Returns:
            类名列表
        """
        return list(self._collector_classes.keys())

    def start_all(self, **kwargs) -> Dict[str, Any]:
        """
        启动所有采集器

        Args:
            **kwargs: 采集参数

        Returns:
            运行结果
        """
        results = {}
        for name, collector in self._collectors.items():
            try:
                result = collector.start(**kwargs)
                results[name] = {
                    "success": True,
                    "count": len(result) if isinstance(result, list) else 0,
                }
            except Exception as e:
                results[name] = {
                    "success": False,
                    "error": str(e),
                }
        return results

    def stop_all(self):
        """停止所有采集器"""
        for collector in self._collectors.values():
            if collector.is_running:
                collector.stop()

    def get_status(self) -> Dict[str, Any]:
        """
        获取所有采集器状态

        Returns:
            状态信息
        """
        return {
            "total_collectors": len(self._collectors),
            "running_collectors": sum(
                1 for c in self._collectors.values() if c.is_running
            ),
            "collectors": self.list_collectors(),
        }

    def clear(self):
        """清空所有采集器"""
        self.stop_all()
        self._collectors.clear()
        logger.info("Cleared all collectors")
