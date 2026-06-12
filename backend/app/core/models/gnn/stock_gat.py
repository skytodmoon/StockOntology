"""
StockGAT - 基于图注意力网络的股票预测模型

利用本体定义的关系（belongs_to, competes_with, supply_to, impacts）
构建图结构，通过 GAT 学习节点嵌入，用于股票涨跌预测。

本体的独特价值：
- 关系类型来自本体定义，不是任意连接
- 每种关系有不同的语义含义，GAT 的注意力机制自动学习权重
- 传导链路径可以作为图结构的先验知识
"""

from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed. GNN features will be limited.")

from app.core.database import get_neo4j_client


if TORCH_AVAILABLE:
    class GraphAttentionLayer(nn.Module):
        """图注意力层（GAT Layer）"""

        def __init__(
            self,
            in_features: int,
            out_features: int,
            num_heads: int = 4,
            dropout: float = 0.6,
            concat: bool = True,
        ):
            super().__init__()
            self.in_features = in_features
            self.out_features = out_features
            self.num_heads = num_heads
            self.concat = concat

            # 每个头的线性变换
            self.W = nn.Parameter(torch.empty(num_heads, in_features, out_features))
            self.a = nn.Parameter(torch.empty(num_heads, 2 * out_features, 1))

            if dropout > 0:
                self.dropout = nn.Dropout(dropout)
            else:
                self.dropout = None

            self.leaky_relu = nn.LeakyReLU(0.2)
            self._reset_parameters()

        def _reset_parameters(self):
            nn.init.xavier_uniform_(self.W)
            nn.init.xavier_uniform_(self.a)

        def forward(self, h, adj):
            """
            Args:
                h: 节点特征 (N, in_features)
                adj: 邻接矩阵 (N, N)
            Returns:
                更新后的节点特征 (N, out_features * num_heads) 或 (N, out_features)
            """
            N = h.size(0)

            # 线性变换: (num_heads, N, out_features)
            Wh = torch.einsum("nd,hdo->hno", h, self.W)

            # 计算注意力系数
            # a_input: (num_heads, N, N, 2*out_features)
            a_input = torch.cat([
                Wh.unsqueeze(2).expand(-1, -1, N, -1),
                Wh.unsqueeze(1).expand(-1, N, -1, -1),
            ], dim=-1)

            # e: (num_heads, N, N)
            e = self.leaky_relu(torch.einsum("hnoi,hio->hno", a_input, self.a.squeeze(-1)))

            # 掩码非邻接节点
            mask = (adj == 0).unsqueeze(0)
            e = e.masked_fill(mask, float("-inf"))

            # 注意力权重
            alpha = F.softmax(e, dim=-1)
            if self.dropout:
                alpha = self.dropout(alpha)

            # 聚合: (num_heads, N, out_features)
            out = torch.einsum("hnm,hmd->hnd", alpha, Wh)

            if self.concat:
                # 拼接所有头: (N, num_heads * out_features)
                return out.permute(1, 0, 2).reshape(N, -1)
            else:
                # 平均所有头: (N, out_features)
                return out.mean(dim=0)

    class StockGAT(nn.Module):
        """
        基于图注意力网络的股票预测模型

        输入：
        - 节点特征：公司基本面 + 技术指标 + 本体特征
        - 边：本体定义的关系（belongs_to, competes_with, supply_to）

        输出：
        - 节点级别的涨跌预测（每个公司一个预测值）
        """

        def __init__(
            self,
            in_features: int,
            hidden_features: int = 64,
            out_features: int = 1,
            num_heads: int = 4,
            num_layers: int = 2,
            dropout: float = 0.6,
        ):
            super().__init__()

            self.layers = nn.ModuleList()

            # 第一层
            self.layers.append(
                GraphAttentionLayer(in_features, hidden_features, num_heads, dropout, concat=True)
            )

            # 中间层
            for _ in range(num_layers - 2):
                self.layers.append(
                    GraphAttentionLayer(
                        hidden_features * num_heads, hidden_features, num_heads, dropout, concat=True
                    )
                )

            # 最后一层（不拼接，取平均）
            self.layers.append(
                GraphAttentionLayer(
                    hidden_features * num_heads, hidden_features, num_heads, dropout, concat=False
                )
            )

            # 预测头
            self.predictor = nn.Sequential(
                nn.Linear(hidden_features, hidden_features // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_features // 2, out_features),
                nn.Sigmoid(),  # 输出 0-1，0=跌，1=涨
            )

        def forward(self, x, adj):
            """
            Args:
                x: 节点特征 (N, in_features)
                adj: 邻接矩阵 (N, N)

            Returns:
                预测结果 (N, out_features)
            """
            for layer in self.layers:
                x = F.elu(layer(x, adj))

            return self.predictor(x)

        def get_node_embeddings(self, x, adj):
            """
            获取节点嵌入（用于可视化或下游任务）

            Args:
                x: 节点特征
                adj: 邻接矩阵

            Returns:
                节点嵌入 (N, hidden_features)
            """
            for layer in self.layers:
                x = F.elu(layer(x, adj))
            return x


def build_graph_from_neo4j(
    stock_codes: Optional[List[str]] = None,
    max_nodes: int = 100,
) -> Dict[str, Any]:
    """
    从 Neo4j 构建图数据（用于 GNN 输入）

    Args:
        stock_codes: 股票代码列表（None 则获取所有）
        max_nodes: 最大节点数

    Returns:
        包含 node_features, adj_matrix, node_mapping 的字典
    """
    neo4j = get_neo4j_client()

    # 获取公司节点
    if stock_codes:
        query = """
            MATCH (c:Company)
            WHERE c.stockCode IN $codes
            RETURN c.stockCode AS code, c.stockName AS name,
                   c.marketCap AS cap, c.peRatio AS pe
            LIMIT $limit
        """
        result = neo4j.execute_query(query, {"codes": stock_codes, "limit": max_nodes})
    else:
        query = """
            MATCH (c:Company)
            RETURN c.stockCode AS code, c.stockName AS name,
                   c.marketCap AS cap, c.peRatio AS pe
            ORDER BY c.marketCap DESC
            LIMIT $limit
        """
        result = neo4j.execute_query(query, {"limit": max_nodes})

    if not result:
        return {"node_features": None, "adj_matrix": None, "node_mapping": {}}

    # 构建节点映射
    nodes = [dict(r) for r in result]
    node_mapping = {node["code"]: i for i, node in enumerate(nodes)}
    N = len(nodes)

    # 节点特征：[marketCap_normalized, pe_ratio]
    import torch
    features = torch.zeros(N, 2)
    for i, node in enumerate(nodes):
        cap = node.get("cap", 0) or 0
        pe = node.get("pe", 0) or 0
        features[i, 0] = cap / 1e12 if cap else 0  # 万亿为单位
        features[i, 1] = pe / 100 if pe else 0  # 归一化

    # 邻接矩阵：基于本体关系
    adj = torch.zeros(N, N)

    # 获取关系
    codes = list(node_mapping.keys())
    rel_query = """
        MATCH (c1:Company)-[r]-(c2:Company)
        WHERE c1.stockCode IN $codes AND c2.stockCode IN $codes
              AND c1.stockCode < c2.stockCode
        RETURN c1.stockCode AS code1, c2.stockCode AS code2, type(r) AS rel_type
    """
    rel_result = neo4j.execute_query(rel_query, {"codes": codes})

    for record in rel_result:
        r = dict(record)
        code1, code2 = r["code1"], r["code2"]
        if code1 in node_mapping and code2 in node_mapping:
            i, j = node_mapping[code1], node_mapping[code2]
            adj[i, j] = 1
            adj[j, i] = 1

    # 添加自环
    adj += torch.eye(N)

    return {
        "node_features": features,
        "adj_matrix": adj,
        "node_mapping": node_mapping,
        "nodes": nodes,
    }
