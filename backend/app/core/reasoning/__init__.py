"""
本体推理模块

提供基于 OWL 公理和 SWRL 规则的股票领域推理能力。
核心功能：
1. 因果传导链推导（政策传导、产业链传导、竞争传导、行业层级传导）
2. 事件自动分类
3. 基于本体约束的数据一致性校验
4. 累积影响分数计算
"""

from .causal_chain import CausalChain, ReasoningStep
from .ontology_reasoner import OntologyReasoner

__all__ = [
    "CausalChain",
    "ReasoningStep",
    "OntologyReasoner",
]
