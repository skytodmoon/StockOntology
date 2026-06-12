"""
图神经网络模块

提供基于本体关系图的 GNN 模型，用于股票预测。
"""

from .stock_gat import StockGAT, build_graph_from_neo4j

__all__ = ["StockGAT", "build_graph_from_neo4j"]
