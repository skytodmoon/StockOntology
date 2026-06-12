"""
推理 API

提供本体推理接口，支持：
- 因果传导链推导
- 历史因果链查询
- 预测结果校验
- 累积影响分数计算
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.core.reasoning import OntologyReasoner
from app.core.graph import GraphBuilder

router = APIRouter()


class ReasoningResponse(BaseModel):
    """推理响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


def _get_reasoner():
    """获取推理引擎"""
    return OntologyReasoner()

def _get_graph_builder():
    """获取图谱构建器"""
    return GraphBuilder()


@router.post("/trace-chain", response_model=ReasoningResponse)
async def trace_chain(
    event_id: str,
    max_depth: int = Query(3, ge=1, le=5),
    include_competition: bool = Query(True),
    save_to_graph: bool = Query(True, description="是否将推理结果写入图谱"),
):
    """
    推导事件的因果传导链

    给定一个事件 ID，自动推导 4 种传导路径：
    1. 直接传导：Event → Company
    2. 行业传导：Event → Industry → Company
    3. 产业链传导：Event → CompanyA → CompanyB
    4. 竞争传导：Event → CompanyA → CompanyB（竞争替代）
    """
    try:
        reasoner = _get_reasoner()
        chain = reasoner.trace_impact_chain(
            event_id=event_id,
            max_depth=max_depth,
            include_competition=include_competition,
        )

        # 写入图谱（留痕）
        if save_to_graph and chain.steps:
            try:
                builder = _get_graph_builder()
                builder.save_causal_chain(chain)
                logger.info(f"Causal chain {chain.chain_id} saved to graph")
            except Exception as e:
                logger.warning(f"Failed to save causal chain to graph: {e}")

        return ReasoningResponse(data=chain.to_dict())
    except Exception as e:
        logger.error(f"Trace chain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains/{stock_code}", response_model=ReasoningResponse)
async def get_chains(
    stock_code: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
):
    """
    查询影响某股票的历史因果链

    从图谱中读取已记录的 CausalChain 节点。
    """
    try:
        reasoner = _get_reasoner()
        chains = reasoner.get_all_chains_for_stock(
            stock_code=stock_code,
            days=days,
            limit=limit,
        )

        return ReasoningResponse(data={
            "stock_code": stock_code,
            "period_days": days,
            "chain_count": len(chains),
            "chains": chains,
        })
    except Exception as e:
        logger.error(f"Get chains failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ReasoningResponse)
async def validate_prediction(
    stock_code: str,
    prediction: str = Query(..., description="预测方向：up/down/neutral"),
):
    """
    基于本体规则校验预测结果的合理性

    检查预测方向是否与近期事件影响矛盾。
    """
    try:
        reasoner = _get_reasoner()
        validation = reasoner.predict_with_ontology_rules(stock_code, prediction)

        return ReasoningResponse(data=validation)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/impact/{stock_code}", response_model=ReasoningResponse)
async def get_accumulated_impact(
    stock_code: str,
    days: int = Query(30, ge=1, le=365),
):
    """
    计算某股票在时间窗口内的累积事件影响分数

    返回正面/负面/中性事件的分数分解。
    """
    try:
        reasoner = _get_reasoner()
        impact = reasoner.get_accumulated_impact(stock_code, days)

        return ReasoningResponse(data=impact)
    except Exception as e:
        logger.error(f"Get impact failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify-event", response_model=ReasoningResponse)
async def classify_event(
    event_text: str,
):
    """
    基于本体约束自动分类事件类型

    判断事件属于 PolicyEvent、CompanyEvent 还是 MacroEvent。
    """
    try:
        reasoner = _get_reasoner()
        classification = reasoner.classify_event(event_text)

        return ReasoningResponse(data=classification)
    except Exception as e:
        logger.error(f"Classify event failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-instance", response_model=ReasoningResponse)
async def validate_instance(
    entity_type: str,
    entity_data: Dict[str, Any],
):
    """
    基于 OWL 公理约束校验图谱实例

    检查实体数据是否满足本体定义的约束（如 Company 必须属于 Industry）。
    """
    try:
        from app.core.ontology import OntologyValidator, OntologyManager

        manager = OntologyManager()
        manager.load()
        validator = OntologyValidator(manager)
        result = validator.validate_graph_instance(entity_type, entity_data)

        return ReasoningResponse(data=result.to_dict())
    except Exception as e:
        logger.error(f"Validate instance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
