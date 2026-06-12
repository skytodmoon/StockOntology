"""
知识图谱嵌入模块

提供 TransE 等知识图谱嵌入模型，用于：
- 实体相似度计算
- 链接预测
- GNN 输入特征
"""

from .transe import TransE, train_transe, get_entity_embedding

__all__ = ["TransE", "train_transe", "get_entity_embedding"]
