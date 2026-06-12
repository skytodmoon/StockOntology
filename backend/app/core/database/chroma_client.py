"""
ChromaDB 向量数据库客户端

提供向量存储和检索功能，用于文档嵌入和语义搜索。
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from loguru import logger
import os

from app.config import settings


class ChromaClient:
    """ChromaDB 客户端"""

    _instance: Optional[chromadb.Client] = None
    _collection_cache: Dict[str, chromadb.Collection] = {}

    def __init__(
        self,
        host: str = None,
        port: int = None,
        persist_directory: str = None,
        is_persistent: bool = True,
    ):
        """
        初始化 ChromaDB 客户端

        Args:
            host: ChromaDB 服务器地址（用于服务器模式）
            port: ChromaDB 服务器端口（用于服务器模式）
            persist_directory: 数据持久化目录（用于本地模式）
            is_persistent: 是否使用持久化存储
        """
        self.host = host or settings.CHROMA_HOST
        self.port = port or settings.CHROMA_PORT
        self.persist_directory = persist_directory or os.path.join(
            os.getcwd(), "data", "chroma"
        )
        self.is_persistent = is_persistent

        # 默认嵌入函数（使用 sentence-transformers）
        self._embedding_function = None

    def connect(self) -> chromadb.Client:
        """
        连接到 ChromaDB

        Returns:
            ChromaDB 客户端实例
        """
        if self._instance is not None:
            return self._instance

        try:
            if self.is_persistent:
                # 本地持久化模式 - 使用新的 API
                logger.info(
                    f"Connecting to ChromaDB (persistent mode) at {self.persist_directory}"
                )
                os.makedirs(self.persist_directory, exist_ok=True)
                self._instance = chromadb.PersistentClient(path=self.persist_directory)
            else:
                # 服务器模式
                logger.info(
                    f"Connecting to ChromaDB server at {self.host}:{self.port}"
                )
                self._instance = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                )

            logger.info("ChromaDB connection established")
            return self._instance

        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise

    def get_client(self) -> chromadb.Client:
        """
        获取 ChromaDB 客户端

        Returns:
            ChromaDB 客户端实例
        """
        if self._instance is None:
            self.connect()
        return self._instance

    def get_embedding_function(
        self, model_name: str = "all-MiniLM-L6-v2"
    ) -> embedding_functions.EmbeddingFunction:
        """
        获取嵌入函数

        Args:
            model_name: 嵌入模型名称

        Returns:
            嵌入函数
        """
        if self._embedding_function is None:
            try:
                self._embedding_function = (
                    embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=model_name
                    )
                )
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.warning(
                    f"Failed to load SentenceTransformer model: {e}, using default"
                )
                # 使用默认嵌入函数
                self._embedding_function = embedding_functions.DefaultEmbeddingFunction()

        return self._embedding_function

    def get_collection(
        self,
        name: str,
        embedding_function: Optional[embedding_functions.EmbeddingFunction] = None,
        create_if_not_exists: bool = True,
    ) -> chromadb.Collection:
        """
        获取或创建集合

        Args:
            name: 集合名称
            embedding_function: 嵌入函数
            create_if_not_exists: 如果不存在是否创建

        Returns:
            集合实例
        """
        if name in self._collection_cache:
            return self._collection_cache[name]

        client = self.get_client()

        try:
            # 尝试获取现有集合
            collection = client.get_collection(
                name=name,
                embedding_function=embedding_function or self.get_embedding_function(),
            )
            logger.info(f"Retrieved existing collection: {name}")
        except Exception as e:
            if create_if_not_exists:
                # 创建新集合
                collection = client.create_collection(
                    name=name,
                    embedding_function=embedding_function or self.get_embedding_function(),
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"Created new collection: {name}")
            else:
                logger.error(f"Collection {name} not found: {e}")
                raise

        self._collection_cache[name] = collection
        return collection

    def list_collections(self) -> List[str]:
        """
        列出所有集合

        Returns:
            集合名称列表
        """
        client = self.get_client()
        collections = client.list_collections()
        return [c.name for c in collections]

    def delete_collection(self, name: str) -> bool:
        """
        删除集合

        Args:
            name: 集合名称

        Returns:
            是否成功删除
        """
        try:
            client = self.get_client()
            client.delete_collection(name=name)
            if name in self._collection_cache:
                del self._collection_cache[name]
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            return False

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        向集合添加文档

        Args:
            collection_name: 集合名称
            documents: 文档列表
            ids: 文档ID列表
            metadatas: 元数据列表

        Returns:
            是否成功添加
        """
        try:
            collection = self.get_collection(collection_name)
            collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas,
            )
            logger.info(f"Added {len(documents)} documents to {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        查询相似文档

        Args:
            collection_name: 集合名称
            query_texts: 查询文本列表
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        Returns:
            查询结果
        """
        try:
            collection = self.get_collection(collection_name)
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document,
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query documents: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

    def get_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取文档

        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            where: 元数据过滤条件
            limit: 返回数量限制

        Returns:
            文档数据
        """
        try:
            collection = self.get_collection(collection_name)
            results = collection.get(
                ids=ids,
                where=where,
                limit=limit,
            )
            return results
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        更新文档

        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            documents: 新文档内容列表
            metadatas: 新元数据列表

        Returns:
            是否成功更新
        """
        try:
            collection = self.get_collection(collection_name)
            collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"Updated {len(ids)} documents in {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update documents: {e}")
            return False

    def delete_documents(
        self,
        collection_name: str,
        ids: List[str],
    ) -> bool:
        """
        删除文档

        Args:
            collection_name: 集合名称
            ids: 文档ID列表

        Returns:
            是否成功删除
        """
        try:
            collection = self.get_collection(collection_name)
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    def count_documents(self, collection_name: str) -> int:
        """
        统计文档数量

        Args:
            collection_name: 集合名称

        Returns:
            文档数量
        """
        try:
            collection = self.get_collection(collection_name)
            return collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取 ChromaDB 统计信息

        Returns:
            统计信息
        """
        try:
            client = self.get_client()
            collections = self.list_collections()

            stats = {
                "collections": collections,
                "collection_count": len(collections),
                "persist_directory": self.persist_directory if self.is_persistent else None,
                "mode": "persistent" if self.is_persistent else "server",
            }

            # 获取每个集合的文档数量
            collection_stats = {}
            for name in collections:
                try:
                    count = self.count_documents(name)
                    collection_stats[name] = {"document_count": count}
                except Exception:
                    collection_stats[name] = {"document_count": 0}

            stats["collection_stats"] = collection_stats
            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "collections": [],
                "collection_count": 0,
                "error": str(e),
            }

    def close(self):
        """
        关闭连接
        """
        if self._instance is not None:
            try:
                # ChromaDB 没有显式的关闭方法
                # 持久化模式下数据会自动保存
                self._collection_cache.clear()
                logger.info("ChromaDB connection closed")
            except Exception as e:
                logger.error(f"Error closing ChromaDB: {e}")
            finally:
                self._instance = None


# 全局客户端实例
_chroma_client: Optional[ChromaClient] = None


def get_chroma_client() -> ChromaClient:
    """
    获取 ChromaDB 客户端单例

    Returns:
        ChromaClient 实例
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
        _chroma_client.connect()
    return _chroma_client


def init_chroma_collection(name: str = "stock_docs") -> chromadb.Collection:
    """
    初始化默认集合

    Args:
        name: 集合名称

    Returns:
        集合实例
    """
    client = get_chroma_client()
    return client.get_collection(name, create_if_not_exists=True)