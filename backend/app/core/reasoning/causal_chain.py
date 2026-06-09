"""
因果传导链数据结构

定义 CausalChain 和 ReasoningStep，用于结构化表示推理路径。
所有推理结果通过这些结构记录，支持事后追溯和可视化展示。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ReasoningStep:
    """
    单步推理记录

    记录因果链中的每一步推理，包含：
    - 使用的规则（如"政策传导"、"产业链传导"）
    - 源节点和目标节点
    - 关系类型
    - 证据描述
    - 本步置信度
    """
    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    rule_applied: str = ""          # 使用的规则名称
    rule_id: str = ""               # 规则 ID（如 R001）
    source_node_id: str = ""        # 源节点 ID（Neo4j element_id）
    source_node_type: str = ""      # 源节点类型（Company/Industry/Event）
    source_node_name: str = ""      # 源节点名称（便于展示）
    target_node_id: str = ""        # 目标节点 ID
    target_node_type: str = ""      # 目标节点类型
    target_node_name: str = ""      # 目标节点名称
    relationship: str = ""          # 关系类型（impacts/belongsTo/supplyTo 等）
    evidence: str = ""              # 证据描述
    confidence: float = 1.0         # 本步置信度 (0-1)
    impact_direction: str = "neutral"  # 影响方向（positive/negative/neutral）
    depth: int = 0                  # 在传导链中的深度
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "rule_applied": self.rule_applied,
            "rule_id": self.rule_id,
            "source_node": {
                "id": self.source_node_id,
                "type": self.source_node_type,
                "name": self.source_node_name,
            },
            "target_node": {
                "id": self.target_node_id,
                "type": self.target_node_type,
                "name": self.target_node_name,
            },
            "relationship": self.relationship,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 4),
            "impact_direction": self.impact_direction,
            "depth": self.depth,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CausalChain:
    """
    因果传导链

    记录从源事件到最终影响的完整推理路径。
    每条链包含多个 ReasoningStep，支持：
    - 推理路径回溯
    - 置信度累积计算
    - 可视化展示
    - 写入图谱留痕
    """
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str = ""              # 源事件 ID
    event_name: str = ""            # 源事件名称
    event_type: str = ""            # 事件类型（PolicyEvent/CompanyEvent/MacroEvent）
    steps: List[ReasoningStep] = field(default_factory=list)
    conclusion: str = ""            # 结论描述
    overall_confidence: float = 1.0 # 综合置信度
    total_affected_companies: int = 0  # 受影响公司总数
    created_at: datetime = field(default_factory=datetime.now)

    def add_step(self, step: ReasoningStep):
        """添加推理步骤"""
        step.depth = len(self.steps)
        self.steps.append(step)

    def calculate_overall_confidence(self) -> float:
        """
        计算综合置信度

        综合置信度 = 各步骤置信度的乘积
        （每一步都有衰减，传导越远置信度越低）
        """
        if not self.steps:
            return 0.0

        confidence = 1.0
        for step in self.steps:
            confidence *= step.confidence

        self.overall_confidence = round(confidence, 4)
        return self.overall_confidence

    def get_affected_companies(self) -> List[Dict[str, Any]]:
        """获取所有受影响的公司（去重）"""
        companies = {}
        for step in self.steps:
            if step.target_node_type == "Company":
                companies[step.target_node_id] = {
                    "stock_code": step.target_node_name,  # 通常用股票代码作为名称
                    "stock_name": step.target_node_name,
                    "via_rule": step.rule_applied,
                    "confidence": step.confidence,
                    "impact_direction": step.impact_direction,
                    "depth": step.depth,
                }
        return list(companies.values())

    def get_chain_text(self) -> str:
        """
        获取传导链的文本描述（用于 LLM 上下文）

        Returns:
            可读的传导链描述
        """
        if not self.steps:
            return "无传导路径"

        lines = [f"事件 [{self.event_name}] 的影响传导链："]
        for i, step in enumerate(self.steps, 1):
            direction_emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(
                step.impact_direction, "➡️"
            )
            lines.append(
                f"  {i}. [{step.rule_applied}] "
                f"{step.source_node_name} {direction_emoji} {step.target_node_name} "
                f"(置信度: {step.confidence:.2f})"
            )

        lines.append(f"\n综合置信度: {self.overall_confidence:.2f}")
        lines.append(f"受影响公司数: {self.total_affected_companies}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 API 响应和图谱写入）"""
        return {
            "chain_id": self.chain_id,
            "event": {
                "id": self.event_id,
                "name": self.event_name,
                "type": self.event_type,
            },
            "steps": [step.to_dict() for step in self.steps],
            "conclusion": self.conclusion,
            "overall_confidence": self.overall_confidence,
            "total_affected_companies": self.total_affected_companies,
            "chain_text": self.get_chain_text(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalChain":
        """从字典创建 CausalChain"""
        chain = cls(
            chain_id=data.get("chain_id", str(uuid.uuid4())),
            event_id=data.get("event", {}).get("id", ""),
            event_name=data.get("event", {}).get("name", ""),
            event_type=data.get("event", {}).get("type", ""),
            conclusion=data.get("conclusion", ""),
            overall_confidence=data.get("overall_confidence", 0.0),
            total_affected_companies=data.get("total_affected_companies", 0),
        )
        for step_data in data.get("steps", []):
            step = ReasoningStep(
                step_id=step_data.get("step_id", ""),
                rule_applied=step_data.get("rule_applied", ""),
                rule_id=step_data.get("rule_id", ""),
                source_node_id=step_data.get("source_node", {}).get("id", ""),
                source_node_type=step_data.get("source_node", {}).get("type", ""),
                source_node_name=step_data.get("source_node", {}).get("name", ""),
                target_node_id=step_data.get("target_node", {}).get("id", ""),
                target_node_type=step_data.get("target_node", {}).get("type", ""),
                target_node_name=step_data.get("target_node", {}).get("name", ""),
                relationship=step_data.get("relationship", ""),
                evidence=step_data.get("evidence", ""),
                confidence=step_data.get("confidence", 1.0),
                impact_direction=step_data.get("impact_direction", "neutral"),
                depth=step_data.get("depth", 0),
            )
            chain.steps.append(step)
        return chain
