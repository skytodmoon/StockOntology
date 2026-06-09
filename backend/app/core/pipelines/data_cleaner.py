"""
数据清洗器

提供数据清洗功能。
"""

from typing import Any, Callable, Dict, List, Optional
from loguru import logger


class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        """初始化数据清洗器"""
        self._rules: List[Dict[str, Any]] = []

    def add_rule(
        self,
        name: str,
        condition: Callable,
        action: str = "remove",
        replacement: Any = None,
    ) -> "DataCleaner":
        """
        添加清洗规则

        Args:
            name: 规则名称
            condition: 条件函数
            action: 动作（remove/replace/flag）
            replacement: 替换值

        Returns:
            清洗器实例
        """
        self._rules.append({
            "name": name,
            "condition": condition,
            "action": action,
            "replacement": replacement,
        })
        return self

    def clean(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行数据清洗

        Args:
            data: 输入数据

        Returns:
            清洗后的数据
        """
        cleaned_data = []

        for item in data:
            should_keep = True

            for rule in self._rules:
                try:
                    if rule["condition"](item):
                        if rule["action"] == "remove":
                            should_keep = False
                            break
                        elif rule["action"] == "replace":
                            # 替换处理
                            pass
                        elif rule["action"] == "flag":
                            item["_flagged"] = True
                            item["_flag_reason"] = rule["name"]
                except Exception as e:
                    logger.warning(f"Rule {rule['name']} failed: {e}")

            if should_keep:
                cleaned_data.append(item)

        return cleaned_data

    def remove_nulls(
        self,
        data: List[Dict[str, Any]],
        required_fields: List[str],
    ) -> List[Dict[str, Any]]:
        """
        移除空值记录

        Args:
            data: 输入数据
            required_fields: 必填字段列表

        Returns:
            清洗后的数据
        """
        cleaned = []
        for item in data:
            has_null = False
            for field in required_fields:
                if field not in item or item[field] is None:
                    has_null = True
                    break
            if not has_null:
                cleaned.append(item)
        return cleaned

    def remove_duplicates(
        self,
        data: List[Dict[str, Any]],
        key_fields: List[str],
    ) -> List[Dict[str, Any]]:
        """
        移除重复记录

        Args:
            data: 输入数据
            key_fields: 关键字段列表

        Returns:
            去重后的数据
        """
        seen = set()
        unique_data = []

        for item in data:
            key = tuple(item.get(f) for f in key_fields)
            if key not in seen:
                seen.add(key)
                unique_data.append(item)

        return unique_data

    def normalize_values(
        self,
        data: List[Dict[str, Any]],
        field: str,
        mapping: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """
        标准化字段值

        Args:
            data: 输入数据
            field: 字段名
            mapping: 值映射

        Returns:
            标准化后的数据
        """
        for item in data:
            if field in item:
                value = item[field]
                if value in mapping:
                    item[field] = mapping[value]
        return data

    def fill_defaults(
        self,
        data: List[Dict[str, Any]],
        defaults: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        填充默认值

        Args:
            data: 输入数据
            defaults: 默认值字典

        Returns:
            填充后的数据
        """
        for item in data:
            for field, default_value in defaults.items():
                if field not in item or item[field] is None:
                    item[field] = default_value
        return data
