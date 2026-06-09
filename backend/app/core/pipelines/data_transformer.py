"""
数据转换器

提供数据转换功能。
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from loguru import logger


class DataTransformer:
    """数据转换器"""

    def __init__(self):
        """初始化数据转换器"""
        self._transformers: List[Dict[str, Any]] = []

    def add_transformer(
        self,
        name: str,
        transform: Callable,
    ) -> "DataTransformer":
        """
        添加转换器

        Args:
            name: 转换器名称
            transform: 转换函数

        Returns:
            转换器实例
        """
        self._transformers.append({
            "name": name,
            "transform": transform,
        })
        return self

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行数据转换

        Args:
            data: 输入数据

        Returns:
            转换后的数据
        """
        current_data = data

        for transformer in self._transformers:
            try:
                name = transformer["name"]
                transform = transformer["transform"]
                current_data = transform(current_data)
                logger.info(f"Transformer {name} completed: {len(current_data)} items")
            except Exception as e:
                logger.error(f"Transformer {name} failed: {e}")

        return current_data

    @staticmethod
    def rename_fields(
        data: List[Dict[str, Any]],
        mapping: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """
        重命名字段

        Args:
            data: 输入数据
            mapping: 字段映射（旧名->新名）

        Returns:
            转换后的数据
        """
        result = []
        for item in data:
            new_item = {}
            for key, value in item.items():
                new_key = mapping.get(key, key)
                new_item[new_key] = value
            result.append(new_item)
        return result

    @staticmethod
    def select_fields(
        data: List[Dict[str, Any]],
        fields: List[str],
    ) -> List[Dict[str, Any]]:
        """
        选择字段

        Args:
            data: 输入数据
            fields: 字段列表

        Returns:
            转换后的数据
        """
        result = []
        for item in data:
            new_item = {f: item.get(f) for f in fields if f in item}
            result.append(new_item)
        return result

    @staticmethod
    def add_computed_field(
        data: List[Dict[str, Any]],
        field_name: str,
        compute_func: Callable,
    ) -> List[Dict[str, Any]]:
        """
        添加计算字段

        Args:
            data: 输入数据
            field_name: 字段名
            compute_func: 计算函数

        Returns:
            转换后的数据
        """
        result = []
        for item in data:
            new_item = item.copy()
            new_item[field_name] = compute_func(item)
            result.append(new_item)
        return result

    @staticmethod
    def flatten_nested(
        data: List[Dict[str, Any]],
        parent_key: str = "",
        separator: str = ".",
    ) -> List[Dict[str, Any]]:
        """
        展平嵌套字段

        Args:
            data: 输入数据
            parent_key: 父键
            separator: 分隔符

        Returns:
            转换后的数据
        """
        def _flatten(obj, prefix=""):
            items = {}
            for key, value in obj.items():
                new_key = f"{prefix}{separator}{key}" if prefix else key
                if isinstance(value, dict):
                    items.update(_flatten(value, new_key))
                else:
                    items[new_key] = value
            return items

        return [_flatten(item) for item in data]

    @staticmethod
    def convert_types(
        data: List[Dict[str, Any]],
        type_mapping: Dict[str, type],
    ) -> List[Dict[str, Any]]:
        """
        转换字段类型

        Args:
            data: 输入数据
            type_mapping: 类型映射

        Returns:
            转换后的数据
        """
        result = []
        for item in data:
            new_item = item.copy()
            for field, target_type in type_mapping.items():
                if field in new_item:
                    try:
                        new_item[field] = target_type(new_item[field])
                    except (ValueError, TypeError):
                        pass
            result.append(new_item)
        return result

    @staticmethod
    def add_timestamp(
        data: List[Dict[str, Any]],
        field_name: str = "_timestamp",
    ) -> List[Dict[str, Any]]:
        """
        添加时间戳

        Args:
            data: 输入数据
            field_name: 时间戳字段名

        Returns:
            转换后的数据
        """
        timestamp = datetime.now().isoformat()
        for item in data:
            item[field_name] = timestamp
        return data

    @staticmethod
    def group_by(
        data: List[Dict[str, Any]],
        key_field: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按字段分组

        Args:
            data: 输入数据
            key_field: 分组字段

        Returns:
            分组后的数据
        """
        groups = {}
        for item in data:
            key = item.get(key_field)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
