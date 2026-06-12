"""
TransE - 知识图谱嵌入模型

将本体中的实体和关系映射到低维向量空间，使得：
  h + r ≈ t （头实体 + 关系 ≈ 尾实体）

用途：
- 实体相似度计算：找到与某公司相似的其他公司
- 链接预测：预测缺失的关系
- 作为 GNN 的输入特征

本体价值：
- 训练数据直接来自 Neo4j 中的本体实例化关系
- 嵌入空间编码了本体的语义结构
"""

from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed. KG Embedding features will be limited.")

from app.core.database import get_neo4j_client


if TORCH_AVAILABLE:
    class TransE(nn.Module):
        """
        TransE 知识图谱嵌入模型

        训练目标：对于正确三元组 (h, r, t)，使 ||h + r - t|| 尽可能小
                 对于错误三元组 (h, r, t')，使 ||h + r - t'|| 尽可能大
        """

        def __init__(
            self,
            num_entities: int,
            num_relations: int,
            embedding_dim: int = 128,
            margin: float = 1.0,
            norm: int = 2,
        ):
            super().__init__()
            self.num_entities = num_entities
            self.num_relations = num_relations
            self.embedding_dim = embedding_dim
            self.margin = margin
            self.norm = norm

            self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
            self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)

            # 初始化
            nn.init.xavier_uniform_(self.entity_embeddings.weight)
            nn.init.xavier_uniform_(self.relation_embeddings.weight)
            # 关系向量归一化
            with torch.no_grad():
                self.relation_embeddings.weight.data = F.normalize(
                    self.relation_embeddings.weight.data, p=2, dim=-1
                )

        def forward(self, head, relation, tail):
            """
            计算三元组的得分（距离）

            Args:
                head: 头实体索引 (batch,)
                relation: 关系索引 (batch,)
                tail: 尾实体索引 (batch,)

            Returns:
                得分（距离），越小越好
            """
            h = self.entity_embeddings(head)
            r = self.relation_embeddings(relation)
            t = self.entity_embeddings(tail)

            # ||h + r - t||
            score = torch.norm(h + r - t, p=self.norm, dim=-1)
            return score

        def loss(self, positive_score, negative_score):
            """
            计算 margin-based ranking loss

            Args:
                positive_score: 正样本距离
                negative_score: 负样本距离

            Returns:
                损失值
            """
            return torch.relu(positive_score - negative_score + self.margin).mean()

        def get_entity_embedding(self, entity_idx):
            """获取实体嵌入"""
            return self.entity_embeddings(entity_idx)

        def get_relation_embedding(self, relation_idx):
            """获取关系嵌入"""
            return self.relation_embeddings(relation_idx)

        def find_similar_entities(
            self, entity_idx: int, top_k: int = 10
        ) -> List[Tuple[int, float]]:
            """
            找到与给定实体最相似的实体

            Args:
                entity_idx: 实体索引
                top_k: 返回数量

            Returns:
                [(entity_idx, distance), ...] 按距离排序
            """
            with torch.no_grad():
                target = self.entity_embeddings.weight[entity_idx]
                distances = torch.norm(
                    self.entity_embeddings.weight - target.unsqueeze(0),
                    p=self.norm,
                    dim=-1
                )
                # 排除自身
                distances[entity_idx] = float("inf")
                top_indices = torch.topk(distances, top_k, largest=False)
                return [
                    (idx.item(), dist.item())
                    for idx, dist in zip(top_indices.indices, top_indices.values)
                ]


    import torch.nn.functional as F


def load_triples_from_neo4j(
    max_triples: int = 10000,
) -> Tuple[List[Tuple[str, str, str]], Dict[str, int], Dict[str, int]]:
    """
    从 Neo4j 加载三元组

    Returns:
        (triples, entity_to_idx, relation_to_idx)
    """
    neo4j = get_neo4j_client()

    query = """
        MATCH (h)-[r]->(t)
        WHERE h.stockCode IS NOT NULL OR h.code IS NOT NULL OR h.eventId IS NOT NULL
        RETURN
            COALESCE(h.stockCode, h.code, h.eventId, h.investorId, toString(elementId(h))) AS head,
            type(r) AS relation,
            COALESCE(t.stockCode, t.code, t.eventId, t.investorId, toString(elementId(t))) AS tail
        LIMIT $limit
    """
    result = neo4j.execute_query(query, {"limit": max_triples})

    triples = []
    entities = set()
    relations = set()

    for record in result:
        r = dict(record)
        h, rel, t = r["head"], r["relation"], r["tail"]
        triples.append((h, rel, t))
        entities.add(h)
        entities.add(t)
        relations.add(rel)

    entity_to_idx = {e: i for i, e in enumerate(sorted(entities))}
    relation_to_idx = {r: i for i, r in enumerate(sorted(relations))}

    return triples, entity_to_idx, relation_to_idx


def train_transe(
    embedding_dim: int = 128,
    epochs: int = 100,
    learning_rate: float = 0.01,
    batch_size: int = 256,
    margin: float = 1.0,
) -> Optional[Dict[str, Any]]:
    """
    训练 TransE 模型

    Args:
        embedding_dim: 嵌入维度
        epochs: 训练轮数
        learning_rate: 学习率
        batch_size: 批次大小
        margin: margin 参数

    Returns:
        训练结果，包含模型状态和实体/关系映射
    """
    if not TORCH_AVAILABLE:
        logger.error("PyTorch not available")
        return None

    try:
        triples, entity_to_idx, relation_to_idx = load_triples_from_neo4j()

        if len(triples) < 10:
            logger.warning("Too few triples for training")
            return None

        num_entities = len(entity_to_idx)
        num_relations = len(relation_to_idx)

        model = TransE(num_entities, num_relations, embedding_dim, margin)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

        # 转换为索引
        import random
        triple_indices = [
            (entity_to_idx[h], relation_to_idx[r], entity_to_idx[t])
            for h, r, t in triples
        ]

        for epoch in range(epochs):
            random.shuffle(triple_indices)
            total_loss = 0

            for i in range(0, len(triple_indices), batch_size):
                batch = triple_indices[i:i + batch_size]
                if len(batch) < 2:
                    continue

                heads = torch.LongTensor([t[0] for t in batch])
                relations = torch.LongTensor([t[1] for t in batch])
                tails = torch.LongTensor([t[2] for t in batch])

                # 负采样：随机替换头或尾
                neg_tails = torch.randint(0, num_entities, tails.shape)

                pos_score = model(heads, relations, tails)
                neg_score = model(heads, relations, neg_tails)

                loss = model.loss(pos_score, neg_score)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            if (epoch + 1) % 20 == 0:
                logger.info(f"TransE epoch {epoch + 1}/{epochs}, loss: {total_loss:.4f}")

        return {
            "model_state": model.state_dict(),
            "entity_to_idx": entity_to_idx,
            "relation_to_idx": relation_to_idx,
            "num_entities": num_entities,
            "num_relations": num_relations,
            "embedding_dim": embedding_dim,
        }

    except Exception as e:
        logger.error(f"TransE training failed: {e}")
        return None


def get_entity_embedding(
    stock_code: str,
    model_state: Optional[Dict] = None,
) -> Optional[List[float]]:
    """
    获取公司实体的嵌入向量

    Args:
        stock_code: 股票代码
        model_state: 训练好的模型状态（如果为 None 则尝试加载）

    Returns:
        嵌入向量（列表），失败返回 None
    """
    if not TORCH_AVAILABLE:
        return None

    if model_state is None:
        logger.warning("No model state provided")
        return None

    try:
        entity_to_idx = model_state.get("entity_to_idx", {})
        if stock_code not in entity_to_idx:
            return None

        idx = entity_to_idx[stock_code]
        model = TransE(
            model_state["num_entities"],
            model_state["num_relations"],
            model_state["embedding_dim"],
        )
        model.load_state_dict(model_state["model_state"])

        with torch.no_grad():
            embedding = model.get_entity_embedding(torch.LongTensor([idx]))
            return embedding.squeeze().tolist()

    except Exception as e:
        logger.error(f"Failed to get entity embedding: {e}")
        return None
