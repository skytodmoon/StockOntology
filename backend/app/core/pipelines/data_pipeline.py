"""
数据处理管道

提供数据处理的管道功能。
"""

from typing import Any, Callable, Dict, List, Optional
from loguru import logger


class DataPipeline:
    """数据处理管道"""

    def __init__(self, name: str = "default"):
        """
        初始化数据管道

        Args:
            name: 管道名称
        """
        self.name = name
        self._steps: List[Dict[str, Any]] = []
        self._is_running = False

    def add_step(
        self,
        name: str,
        processor: Callable,
        **kwargs,
    ) -> "DataPipeline":
        """
        添加处理步骤

        Args:
            name: 步骤名称
            processor: 处理函数
            **kwargs: 额外参数

        Returns:
            管道实例（支持链式调用）
        """
        self._steps.append({
            "name": name,
            "processor": processor,
            "kwargs": kwargs,
        })
        return self

    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行管道处理

        Args:
            data: 输入数据

        Returns:
            处理后的数据
        """
        self._is_running = True
        current_data = data

        for step in self._steps:
            step_name = step["name"]
            processor = step["processor"]
            kwargs = step["kwargs"]

            try:
                logger.info(f"Executing step: {step_name}")
                current_data = processor(current_data, **kwargs)
                logger.info(f"Step {step_name} completed: {len(current_data)} items")
            except Exception as e:
                logger.error(f"Step {step_name} failed: {e}")
                raise

        self._is_running = False
        return current_data

    def clear(self):
        """清空管道步骤"""
        self._steps.clear()

    def get_steps(self) -> List[str]:
        """
        获取管道步骤列表

        Returns:
            步骤名称列表
        """
        return [step["name"] for step in self._steps]

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
