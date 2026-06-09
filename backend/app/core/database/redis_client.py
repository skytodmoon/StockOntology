"""
Redis 客户端

提供 Redis 连接管理和常用缓存操作。
"""

from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import json
import pickle
from datetime import timedelta
import redis
from redis import Redis, ConnectionPool
from loguru import logger

from app.config import settings


class RedisClient:
    """Redis 客户端"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        password: str = None,
        db: int = None,
        max_connections: int = 10,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        decode_responses: bool = True,
    ):
        """
        初始化 Redis 客户端

        Args:
            host: 主机地址
            port: 端口号
            password: 密码
            db: 数据库编号
            max_connections: 最大连接数
            socket_timeout: 套接字超时时间
            socket_connect_timeout: 连接超时时间
            decode_responses: 是否自动解码响应
        """
        self.host = host or settings.REDIS_HOST
        self.port = port or settings.REDIS_PORT
        self.password = password or settings.REDIS_PASSWORD
        self.db = db if db is not None else settings.REDIS_DB

        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None

        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.decode_responses = decode_responses

    @property
    def pool(self) -> ConnectionPool:
        """获取或创建连接池"""
        if self._pool is None:
            self._pool = ConnectionPool(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                decode_responses=self.decode_responses,
            )
        return self._pool

    @property
    def client(self) -> Redis:
        """获取或创建 Redis 客户端"""
        if self._client is None:
            self._client = Redis(connection_pool=self.pool)
            logger.info(f"Connected to Redis at {self.host}:{self.port}/{self.db}")
        return self._client

    def close(self):
        """关闭连接"""
        if self._pool is not None:
            self._pool.disconnect()
            self._pool = None
            self._client = None
            logger.info("Redis connection closed")

    def ping(self) -> bool:
        """测试连接"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    # String 操作

    def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        return self.client.get(key)

    def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """设置字符串值"""
        return self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    def get_json(self, key: str) -> Optional[Any]:
        """获取 JSON 值"""
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """设置 JSON 值"""
        return self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ex)

    def get_pickle(self, key: str) -> Optional[Any]:
        """获取 pickle 序列化的值"""
        data = self.client.get(key)
        if data:
            return pickle.loads(data.encode("latin-1"))
        return None

    def set_pickle(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """设置 pickle 序列化的值"""
        return self.client.set(key, pickle.dumps(value).decode("latin-1"), ex=ex)

    def delete(self, *keys: str) -> int:
        """删除键"""
        return self.client.delete(*keys)

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.client.exists(key) > 0

    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return self.client.expire(key, seconds)

    def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        return self.client.ttl(key)

    # Hash 操作

    def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希字段值"""
        return self.client.hget(name, key)

    def hset(self, name: str, key: str, value: str) -> int:
        """设置哈希字段值"""
        return self.client.hset(name, key, value)

    def hgetall(self, name: str) -> Dict[str, str]:
        """获取所有哈希字段"""
        return self.client.hgetall(name)

    def hmset(self, name: str, mapping: Dict[str, str]) -> bool:
        """批量设置哈希字段"""
        return self.client.hmset(name, mapping)

    def hdel(self, name: str, *keys: str) -> int:
        """删除哈希字段"""
        return self.client.hdel(name, *keys)

    # List 操作

    def lpush(self, name: str, *values: str) -> int:
        """从左侧推入列表"""
        return self.client.lpush(name, *values)

    def rpush(self, name: str, *values: str) -> int:
        """从右侧推入列表"""
        return self.client.rpush(name, *values)

    def lpop(self, name: str) -> Optional[str]:
        """从左侧弹出"""
        return self.client.lpop(name)

    def rpop(self, name: str) -> Optional[str]:
        """从右侧弹出"""
        return self.client.rpop(name)

    def lrange(self, name: str, start: int, end: int) -> List[str]:
        """获取列表范围"""
        return self.client.lrange(name, start, end)

    def llen(self, name: str) -> int:
        """获取列表长度"""
        return self.client.llen(name)

    # Set 操作

    def sadd(self, name: str, *values: str) -> int:
        """添加集合成员"""
        return self.client.sadd(name, *values)

    def smembers(self, name: str) -> set:
        """获取所有集合成员"""
        return self.client.smembers(name)

    def sismember(self, name: str, value: str) -> bool:
        """检查是否是集合成员"""
        return self.client.sismember(name, value)

    def srem(self, name: str, *values: str) -> int:
        """删除集合成员"""
        return self.client.srem(name, *values)

    # Sorted Set 操作

    def zadd(self, name: str, mapping: Dict[str, float]) -> int:
        """添加有序集合成员"""
        return self.client.zadd(name, mapping)

    def zrange(self, name: str, start: int, end: int, withscores: bool = False) -> List:
        """获取有序集合范围"""
        return self.client.zrange(name, start, end, withscores=withscores)

    def zrevrange(self, name: str, start: int, end: int, withscores: bool = False) -> List:
        """获取有序集合范围（逆序）"""
        return self.client.zrevrange(name, start, end, withscores=withscores)

    def zscore(self, name: str, member: str) -> Optional[float]:
        """获取成员分数"""
        return self.client.zscore(name, member)

    # 发布/订阅

    def publish(self, channel: str, message: str) -> int:
        """发布消息"""
        return self.client.publish(channel, message)

    def subscribe(self, *channels: str):
        """订阅频道"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(*channels)
        return pubsub

    # 缓存装饰器

    def cache(
        self,
        key_prefix: str,
        ex: int = 3600,
        serialize: str = "json",
    ):
        """
        缓存装饰器

        Args:
            key_prefix: 键前缀
            ex: 过期时间（秒）
            serialize: 序列化方式（json/pickle）
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # 构建缓存键
                cache_key = f"{key_prefix}:{args}:{kwargs}"

                # 尝试从缓存获取
                if serialize == "json":
                    cached = self.get_json(cache_key)
                else:
                    cached = self.get_pickle(cache_key)

                if cached is not None:
                    return cached

                # 执行函数
                result = func(*args, **kwargs)

                # 存入缓存
                if serialize == "json":
                    self.set_json(cache_key, result, ex=ex)
                else:
                    self.set_pickle(cache_key, result, ex=ex)

                return result
            return wrapper
        return decorator

    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的键

        Args:
            pattern: 键模式（如 "user:*"）

        Returns:
            删除的键数量
        """
        keys = self.client.keys(pattern)
        if keys:
            return self.delete(*keys)
        return 0

    def get_info(self) -> Dict[str, Any]:
        """获取 Redis 服务器信息"""
        return self.client.info()

    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用信息"""
        info = self.get_info()
        return {
            "used_memory": info.get("used_memory"),
            "used_memory_human": info.get("used_memory_human"),
            "used_memory_peak": info.get("used_memory_peak"),
            "used_memory_peak_human": info.get("used_memory_peak_human"),
        }


# 全局客户端实例
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    获取 Redis 客户端单例

    Returns:
        RedisClient: Redis 客户端实例
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
