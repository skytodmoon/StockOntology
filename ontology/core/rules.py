"""
SWRL 传导规则定义

本模块定义股票领域的四种核心传导规则，用于本体推理引擎。
规则以 Python 数据结构表示，由 OntologyReasoner 执行。

传导规则：
1. 政策传导：PolicyEvent → Industry → Company
2. 产业链传导：Event → CompanyA →[supplyTo] → CompanyB
3. 竞争传导：Event 利好 CompanyA →[competesWith] → CompanyB（竞争替代效应）
4. 行业层级传导：subIndustryOf 传递性
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class RuleType(str, Enum):
    """规则类型枚举"""
    POLICY_TRANSMISSION = "policy_transmission"
    SUPPLY_CHAIN_TRANSMISSION = "supply_chain_transmission"
    COMPETITION_TRANSMISSION = "competition_transmission"
    INDUSTRY_HIERARCHY_TRANSMISSION = "industry_hierarchy_transmission"
    DIRECT_IMPACT = "direct_impact"


class ImpactDirection(str, Enum):
    """影响方向"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class TransmissionRule:
    """传导规则定义"""
    rule_id: str
    rule_type: RuleType
    name: str
    description: str
    # 规则的前提条件（Cypher 查询模板）
    precondition_query: str
    # 规则的传导逻辑（Cypher 查询模板）
    transmission_query: str
    # 规则的置信度衰减系数（每传导一步，置信度乘以此系数）
    confidence_decay: float = 0.8
    # 规则的最大传导深度
    max_depth: int = 3


# ==================== 规则 1：政策传导 ====================
# 逻辑：PolicyEvent impacts Industry AND Company belongsTo Industry
#       → PolicyEvent impacts Company（间接）
POLICY_TRANSMISSION = TransmissionRule(
    rule_id="R001",
    rule_type=RuleType.POLICY_TRANSMISSION,
    name="政策传导",
    description="政策事件通过影响行业，间接影响行业内所有公司。"
                "例如：央行降准 → 银行业利好 → 银行股上涨",
    # 前置条件：查找政策事件直接影响的行业
    precondition_query="""
        MATCH (e:MarketEvent {eventType: 'PolicyEvent'})-[:IMPACTS]->(i:Industry)
        WHERE e.eventId = $event_id
        RETURN e, i
    """,
    # 传导逻辑：查找行业内所有公司
    transmission_query="""
        MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(i:Industry)
              <-[:BELONGS_TO]-(c:Company)
        WHERE c.stockCode <> $source_company_code OR $source_company_code IS NULL
        RETURN c.stockCode AS stock_code,
               c.stockName AS stock_name,
               i.name AS industry_name,
               'policy_transmission' AS rule_applied,
               e.impactLevel AS impact_level
    """,
    confidence_decay=0.8,
    max_depth=2,
)

# ==================== 规则 2：产业链传导 ====================
# 逻辑：Event impacts CompanyA AND CompanyA supplyTo CompanyB
#       → Event impacts CompanyB
SUPPLY_CHAIN_TRANSMISSION = TransmissionRule(
    rule_id="R002",
    rule_type=RuleType.SUPPLY_CHAIN_TRANSMISSION,
    name="产业链传导",
    description="事件影响上游供应商时，通过供应链关系传导至下游客户。"
                "例如：锂矿涨价 → 宁德时代成本上升 → 车企成本上升",
    # 前置条件：查找事件直接影响的公司
    precondition_query="""
        MATCH (e:MarketEvent)-[:IMPACTS]->(c:Company)
        WHERE e.eventId = $event_id
        RETURN e, c
    """,
    # 传导逻辑：沿供应链传导（上游→下游）
    transmission_query="""
        MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(source:Company)
              -[:SUPPLY_TO]->(target:Company)
        RETURN target.stockCode AS stock_code,
               target.stockName AS stock_name,
               source.stockName AS source_name,
               'supply_chain_transmission' AS rule_applied,
               e.impactLevel AS impact_level
        UNION
        MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(source:Company)
              <-[:SUPPLY_TO]-(target:Company)
        RETURN target.stockCode AS stock_code,
               target.stockName AS stock_name,
               source.stockName AS source_name,
               'supply_chain_transmission_reverse' AS rule_applied,
               e.impactLevel AS impact_level
    """,
    confidence_decay=0.7,
    max_depth=3,
)

# ==================== 规则 3：竞争传导 ====================
# 逻辑：Event positively impacts CompanyA AND CompanyA competesWith CompanyB
#       → Event negatively impacts CompanyB（竞争替代效应）
COMPETITION_TRANSMISSION = TransmissionRule(
    rule_id="R003",
    rule_type=RuleType.COMPETITION_TRANSMISSION,
    name="竞争传导",
    description="事件利好某公司时，其竞争对手可能受到负面影响（竞争替代效应）。"
                "例如：茅台获政策利好 → 五粮液市场份额受压",
    # 前置条件：查找事件直接影响的公司
    precondition_query="""
        MATCH (e:MarketEvent)-[:IMPACTS]->(c:Company)
        WHERE e.eventId = $event_id
        RETURN e, c
    """,
    # 传导逻辑：查找竞争对手
    transmission_query="""
        MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(source:Company)
              -[:COMPETES_WITH]->(target:Company)
        RETURN target.stockCode AS stock_code,
               target.stockName AS stock_name,
               source.stockName AS source_name,
               'competition_transmission' AS rule_applied,
               e.impactLevel AS impact_level
    """,
    confidence_decay=0.6,
    max_depth=1,
)

# ==================== 规则 4：行业层级传导 ====================
# 逻辑：Event impacts IndustryA AND IndustryA subIndustryOf IndustryB
#       → Event impacts IndustryB（传递性已在 OWL 中定义）
# 这里实现具体的查询逻辑
INDUSTRY_HIERARCHY_TRANSMISSION = TransmissionRule(
    rule_id="R004",
    rule_type=RuleType.INDUSTRY_HIERARCHY_TRANSMISSION,
    name="行业层级传导",
    description="事件影响子行业时，通过行业层级关系传导至上级行业，"
                "再影响上级行业下的其他子行业公司。"
                "例如：白酒行业利好 → 消费品行业受益 → 食品饮料板块上涨",
    # 前置条件：查找事件影响的行业
    precondition_query="""
        MATCH (e:MarketEvent)-[:IMPACTS]->(i:Industry)
        WHERE e.eventId = $event_id
        RETURN e, i
    """,
    # 传导逻辑：沿行业层级向上、向下传导
    transmission_query="""
        // 向上传导：子行业 → 上级行业
        MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(child:Industry)
              -[:SUB_INDUSTRY_OF]->(parent:Industry)
              <-[:BELONGS_TO]-(c:Company)
        WHERE NOT (e)-[:IMPACTS]->(c)
        RETURN c.stockCode AS stock_code,
               c.stockName AS stock_name,
               parent.name AS via_industry,
               'industry_hierarchy_up' AS rule_applied,
               e.impactLevel AS impact_level
        UNION
        // 向下传导：上级行业 → 子行业 → 公司
        MATCH (e:MarketEvent {eventId: $event_id})-[:IMPACTS]->(parent:Industry)
              <-[:SUB_INDUSTRY_OF]-(child:Industry)
              <-[:BELONGS_TO]-(c:Company)
        WHERE NOT (e)-[:IMPACTS]->(c)
        RETURN c.stockCode AS stock_code,
               c.stockName AS stock_name,
               child.name AS via_industry,
               'industry_hierarchy_down' AS rule_applied,
               e.impactLevel AS impact_level
    """,
    confidence_decay=0.75,
    max_depth=2,
)

# ==================== 规则 5：直接影响（基础规则） ====================
# 逻辑：Event directly impacts Company
DIRECT_IMPACT = TransmissionRule(
    rule_id="R005",
    rule_type=RuleType.DIRECT_IMPACT,
    name="直接影响",
    description="事件直接影响公司（最基础的传导关系）",
    precondition_query="""
        MATCH (e:MarketEvent)-[:IMPACTS]->(c:Company)
        WHERE e.eventId = $event_id
        RETURN e, c
    """,
    transmission_query="""
        MATCH (e:MarketEvent {eventId: $event_id})-[r:IMPACTS]->(c:Company)
        RETURN c.stockCode AS stock_code,
               c.stockName AS stock_name,
               'direct_impact' AS rule_applied,
               e.impactLevel AS impact_level,
               r.impactDirection AS direction
    """,
    confidence_decay=1.0,  # 直接影响不衰减
    max_depth=1,
)


# ==================== 规则注册表 ====================
ALL_RULES: List[TransmissionRule] = [
    DIRECT_IMPACT,
    POLICY_TRANSMISSION,
    SUPPLY_CHAIN_TRANSMISSION,
    COMPETITION_TRANSMISSION,
    INDUSTRY_HIERARCHY_TRANSMISSION,
]

# 按规则类型索引
RULES_BY_TYPE = {rule.rule_type: rule for rule in ALL_RULES}

# 按规则 ID 索引
RULES_BY_ID = {rule.rule_id: rule for rule in ALL_RULES}


def get_rule(rule_id: str) -> Optional[TransmissionRule]:
    """根据规则 ID 获取规则"""
    return RULES_BY_ID.get(rule_id)


def get_rules_by_type(rule_type: RuleType) -> List[TransmissionRule]:
    """根据规则类型获取规则列表"""
    return [r for r in ALL_RULES if r.rule_type == rule_type]


def get_applicable_rules(event_type: str) -> List[TransmissionRule]:
    """
    根据事件类型获取适用的传导规则

    Args:
        event_type: 事件类型（PolicyEvent, CompanyEvent, MacroEvent）

    Returns:
        适用的规则列表
    """
    rules = [DIRECT_IMPACT]  # 所有事件都有直接影响

    if event_type == "PolicyEvent":
        rules.extend([
            POLICY_TRANSMISSION,
            INDUSTRY_HIERARCHY_TRANSMISSION,
            COMPETITION_TRANSMISSION,
        ])
    elif event_type == "CompanyEvent":
        rules.extend([
            SUPPLY_CHAIN_TRANSMISSION,
            COMPETITION_TRANSMISSION,
        ])
    elif event_type == "MacroEvent":
        rules.extend([
            POLICY_TRANSMISSION,
            INDUSTRY_HIERARCHY_TRANSMISSION,
            SUPPLY_CHAIN_TRANSMISSION,
        ])

    return rules
