"""
基础数据仓库

提供数据访问的抽象基类。
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from abc import ABC, abstractmethod
from loguru import logger

from app.core.database import get_neo4j_client


T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    基础数据仓库抽象类

    提供通用的数据访问方法，子类需要实现具体的方法。
    """

    def __init__(self, node_label: str):
        """
        初始化基础仓库

        Args:
            node_label: Neo4j 节点标签
        """
        self.node_label = node_label
        self._neo4j = None

    @property
    def neo4j(self):
        """获取 Neo4j 客户端"""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    def find_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 查找节点

        Args:
            node_id: 节点 ID

        Returns:
            节点属性字典
        """
        query = f"""
            MATCH (n:{self.node_label})
            WHERE id(n) = $node_id
            RETURN n
        """
        result = self.neo4j.execute_query(query, {"node_id": int(node_id)})
        if result:
            return dict(result[0]["n"])
        return None

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        order_desc: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        查找所有节点

        Args:
            skip: 跳过数量
            limit: 返回数量
            order_by: 排序字段
            order_desc: 是否降序

        Returns:
            节点列表
        """
        order_clause = ""
        if order_by:
            direction = "DESC" if order_desc else "ASC"
            order_clause = f"ORDER BY n.{order_by} {direction}"

        query = f"""
            MATCH (n:{self.node_label})
            RETURN n
            {order_clause}
            SKIP $skip
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, {"skip": skip, "limit": limit})
        return [dict(record["n"]) for record in result]

    def count(self) -> int:
        """
        统计节点数量

        Returns:
            节点数量
        """
        query = f"""
            MATCH (n:{self.node_label})
            RETURN count(n) as count
        """
        result = self.neo4j.execute_query(query)
        return result[0]["count"] if result else 0

    def exists(self, **kwargs) -> bool:
        """
        检查节点是否存在

        Args:
            **kwargs: 查询条件

        Returns:
            是否存在
        """
        where_clauses = []
        params = {}
        for key, value in kwargs.items():
            where_clauses.append(f"n.{key} = ${key}")
            params[key] = value

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"

        query = f"""
            MATCH (n:{self.node_label})
            WHERE {where_clause}
            RETURN count(n) as count
        """
        result = self.neo4j.execute_query(query, params)
        return result[0]["count"] > 0 if result else False

    def create(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建节点

        Args:
            properties: 节点属性

        Returns:
            创建的节点属性
        """
        query = f"""
            CREATE (n:{self.node_label})
            SET n = $properties
            RETURN n
        """
        result = self.neo4j.execute_write(query, {"properties": properties})
        return result

    def update(self, node_id: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新节点

        Args:
            node_id: 节点 ID
            properties: 更新的属性

        Returns:
            更新后的节点属性
        """
        # 移除 None 值
        update_props = {k: v for k, v in properties.items() if v is not None}

        if not update_props:
            return self.find_by_id(node_id)

        set_clauses = [f"n.{key} = ${key}" for key in update_props.keys()]
        set_clause = ", ".join(set_clauses)

        query = f"""
            MATCH (n:{self.node_label})
            WHERE id(n) = $node_id
            SET {set_clause}
            RETURN n
        """
        params = {"node_id": int(node_id), **update_props}
        result = self.neo4j.execute_query(query, params)
        if result:
            return dict(result[0]["n"])
        return None

    def delete(self, node_id: str) -> bool:
        """
        删除节点

        Args:
            node_id: 节点 ID

        Returns:
            是否删除成功
        """
        query = f"""
            MATCH (n:{self.node_label})
            WHERE id(n) = $node_id
            DETACH DELETE n
        """
        try:
            self.neo4j.execute_write(query, {"node_id": int(node_id)})
            return True
        except Exception as e:
            logger.error(f"Failed to delete node {node_id}: {e}")
            return False

    def find_by_property(
        self,
        property_name: str,
        property_value: Any,
    ) -> List[Dict[str, Any]]:
        """
        根据属性查找节点

        Args:
            property_name: 属性名
            property_value: 属性值

        Returns:
            节点列表
        """
        query = f"""
            MATCH (n:{self.node_label})
            WHERE n.{property_name} = $value
            RETURN n
        """
        result = self.neo4j.execute_query(query, {"value": property_value})
        return [dict(record["n"]) for record in result]

    def find_one_by_property(
        self,
        property_name: str,
        property_value: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        根据属性查找单个节点

        Args:
            property_name: 属性名
            property_value: 属性值

        Returns:
            节点属性字典
        """
        query = f"""
            MATCH (n:{self.node_label})
            WHERE n.{property_name} = $value
            RETURN n
            LIMIT 1
        """
        result = self.neo4j.execute_query(query, {"value": property_value})
        if result:
            return dict(result[0]["n"])
        return None

    def find_by_properties(
        self,
        properties: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        根据多个属性查找节点

        Args:
            properties: 属性字典
            skip: 跳过数量
            limit: 返回数量

        Returns:
            节点列表
        """
        where_clauses = []
        params = {}
        for key, value in properties.items():
            where_clauses.append(f"n.{key} = ${key}")
            params[key] = value

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"
        params["skip"] = skip
        params["limit"] = limit

        query = f"""
            MATCH (n:{self.node_label})
            WHERE {where_clause}
            RETURN n
            SKIP $skip
            LIMIT $limit
        """
        result = self.neo4j.execute_query(query, params)
        return [dict(record["n"]) for record in result]

    def find_related(
        self,
        node_id: str,
        relationship_type: str,
        direction: str = "OUTGOING",
    ) -> List[Dict[str, Any]]:
        """
        查找关联节点

        Args:
            node_id: 节点 ID
            relationship_type: 关系类型
            direction: 方向（INCOMING/OUTGOING/BOTH）

        Returns:
            关联节点列表
        """
        if direction == "OUTGOING":
            arrow = f"-[r:{relationship_type}]->"
        elif direction == "INCOMING":
            arrow = f"<-[r:{relationship_type}]-"
        else:
            arrow = f"-[r:{relationship_type}]-"

        query = f"""
            MATCH (n:{self.node_label}){arrow}(m)
            WHERE id(n) = $node_id
            RETURN m, r
        """
        result = self.neo4j.execute_query(query, {"node_id": int(node_id)})
        return [
            {
                "node": dict(record["m"]),
                "relationship": dict(record["r"]) if record["r"] else {},
            }
            for record in result
        ]

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None,
    ) -> bool:
        """
        创建关系

        Args:
            from_id: 源节点 ID
            to_id: 目标节点 ID
            relationship_type: 关系类型
            properties: 关系属性

        Returns:
            是否创建成功
        """
        props_clause = ""
        if properties:
            props_items = [f"{key}: ${key}" for key in properties.keys()]
            props_clause = f" {{{', '.join(props_items)}}}"

        query = f"""
            MATCH (a:{self.node_label}), (b)
            WHERE id(a) = $from_id AND id(b) = $to_id
            CREATE (a)-[r:{relationship_type}{props_clause}]->(b)
            RETURN r
        """
        params = {"from_id": int(from_id), "to_id": int(to_id)}
        if properties:
            params.update(properties)

        try:
            self.neo4j.execute_write(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False

    def delete_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
    ) -> bool:
        """
        删除关系

        Args:
            from_id: 源节点 ID
            to_id: 目标节点 ID
            relationship_type: 关系类型

        Returns:
            是否删除成功
        """
        query = f"""
            MATCH (a:{self.node_label})-[r:{relationship_type}]->(b)
            WHERE id(a) = $from_id AND id(b) = $to_id
            DELETE r
        """
        try:
            self.neo4j.execute_write(query, {"from_id": int(from_id), "to_id": int(to_id)})
            return True
        except Exception as e:
            logger.error(f"Failed to delete relationship: {e}")
            return False

    def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        搜索节点

        Args:
            search_term: 搜索词
            search_fields: 搜索字段列表
            skip: 跳过数量
            limit: 返回数量

        Returns:
            节点列表
        """
        where_clauses = [f"n.{field} CONTAINS $search_term" for field in search_fields]
        where_clause = " OR ".join(where_clauses)

        query = f"""
            MATCH (n:{self.node_label})
            WHERE {where_clause}
            RETURN n
            SKIP $skip
            LIMIT $limit
        """
        result = self.neo4j.execute_query(
            query,
            {"search_term": search_term, "skip": skip, "limit": limit}
        )
        return [dict(record["n"]) for record in result]

    def aggregate(
        self,
        group_by: str,
        agg_field: str,
        agg_function: str = "count",
    ) -> List[Dict[str, Any]]:
        """
        聚合查询

        Args:
            group_by: 分组字段
            agg_field: 聚合字段
            agg_function: 聚合函数（count/sum/avg/min/max）

        Returns:
            聚合结果
        """
        query = f"""
            MATCH (n:{self.node_label})
            RETURN n.{group_by} as group_key, {agg_function}(n.{agg_field}) as agg_value
            ORDER BY group_key
        """
        result = self.neo4j.execute_query(query)
        return [
            {"group": record["group_key"], "value": record["agg_value"]}
            for record in result
        ]

    def batch_create(self, items: List[Dict[str, Any]]) -> int:
        """
        批量创建节点

        Args:
            items: 节点属性列表

        Returns:
            创建的节点数量
        """
        query = f"""
            UNWIND $items AS item
            CREATE (n:{self.node_label})
            SET n = item
            RETURN count(n) as count
        """
        result = self.neo4j.execute_write(query, {"items": items})
        return result

    def batch_update(
        self,
        updates: List[Dict[str, Any]],
        id_field: str = "id",
    ) -> int:
        """
        批量更新节点

        Args:
            updates: 更新数据列表
            id_field: ID 字段名

        Returns:
            更新的节点数量
        """
        count = 0
        for update in updates:
            node_id = update.pop(id_field, None)
            if node_id:
                if self.update(node_id, update):
                    count += 1
        return count

    def batch_delete(self, node_ids: List[str]) -> int:
        """
        批量删除节点

        Args:
            node_ids: 节点 ID 列表

        Returns:
            删除的节点数量
        """
        query = f"""
            MATCH (n:{self.node_label})
            WHERE id(n) IN $node_ids
            DETACH DELETE n
            RETURN count(n) as count
        """
        int_ids = [int(nid) for nid in node_ids]
        result = self.neo4j.execute_write(query, {"node_ids": int_ids})
        return result
