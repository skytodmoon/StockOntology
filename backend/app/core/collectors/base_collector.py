"""
采集器基类

提供数据采集的基础抽象类。
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger


class BaseCollector(ABC):
    """
    采集器基类

    所有数据采集器都需要继承此基类。
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        初始化采集器

        Args:
            name: 采集器名称
            config: 配置参数
        """
        self.name = name
        self.config = config or {}
        self._is_running = False
        self._last_run = None
        self._collected_count = 0

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running

    @property
    def last_run(self) -> Optional[datetime]:
        """上次运行时间"""
        return self._last_run

    @property
    def collected_count(self) -> int:
        """已采集数量"""
        return self._collected_count

    @abstractmethod
    def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """
        执行采集

        Args:
            **kwargs: 采集参数

        Returns:
            采集的数据列表
        """
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证数据

        Args:
            data: 待验证的数据

        Returns:
            数据是否有效
        """
        pass

    def start(self, **kwargs) -> bool:
        """
        启动采集

        Args:
            **kwargs: 采集参数

        Returns:
            是否启动成功
        """
        if self._is_running:
            logger.warning(f"Collector {self.name} is already running")
            return False

        try:
            self._is_running = True
            logger.info(f"Starting collector: {self.name}")

            data = self.collect(**kwargs)

            # 验证数据
            valid_data = []
            for item in data:
                if self.validate_data(item):
                    valid_data.append(item)
                else:
                    logger.warning(f"Invalid data: {item}")

            self._collected_count += len(valid_data)
            self._last_run = datetime.now()
            self._is_running = False

            logger.info(f"Collector {self.name} completed: {len(valid_data)} items collected")
            return valid_data

        except Exception as e:
            logger.error(f"Collector {self.name} failed: {e}")
            self._is_running = False
            return []

    def stop(self):
        """停止采集"""
        self._is_running = False
        logger.info(f"Collector {self.name} stopped")

    def get_status(self) -> Dict[str, Any]:
        """
        获取采集器状态

        Returns:
            状态信息
        """
        return {
            "name": self.name,
            "is_running": self._is_running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "collected_count": self._collected_count,
        }

    def reset(self):
        """重置采集器"""
        self._is_running = False
        self._last_run = None
        self._collected_count = 0
        logger.info(f"Collector {self.name} reset")
