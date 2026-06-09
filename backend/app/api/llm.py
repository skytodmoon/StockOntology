"""
LLM 智能分析 API

提供 LLM 智能分析接口。
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.core.llm import LLMService, RAGService, SentimentAnalyzer

router = APIRouter()


class LLMResponse(BaseModel):
    """LLM 响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    stock_code: Optional[str] = None
    system_prompt: Optional[str] = None


class SentimentRequest(BaseModel):
    """情感分析请求模型"""
    text: str


def _get_llm_service():
    """获取 LLM 服务"""
    return LLMService()

def _get_rag_service():
    """获取 RAG 服务"""
    return RAGService()

def _get_sentiment_analyzer():
    """获取情感分析器"""
    return SentimentAnalyzer()


@router.post("/chat", response_model=LLMResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    try:
        llm = _get_llm_service()
        response = llm.chat(request.message, request.system_prompt)
        return LLMResponse(data={"response": response})
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/chat", response_model=LLMResponse)
async def rag_chat(request: ChatRequest):
    """RAG 聊天接口"""
    try:
        rag = _get_rag_service()
        result = rag.chat_with_context(request.message, request.stock_code)
        return LLMResponse(data=result)
    except Exception as e:
        logger.error(f"RAG chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/question", response_model=LLMResponse)
async def rag_question(question: str):
    """RAG 问答接口"""
    try:
        rag = _get_rag_service()
        result = rag.answer_question(question)
        return LLMResponse(data=result)
    except Exception as e:
        logger.error(f"RAG question failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/stock", response_model=LLMResponse)
async def analyze_stock(stock_code: str):
    """分析股票"""
    try:
        from app.core.graph import GraphQuery
        query = GraphQuery()

        # 获取公司信息
        company = query.get_company_info(stock_code)
        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")

        # 获取财务数据
        reports = query.get_company_financial_reports(stock_code, limit=1)
        if reports:
            company.update(reports[0])

        llm = _get_llm_service()
        analysis = llm.analyze_stock(company)

        return LLMResponse(data={
            "stock_code": stock_code,
            "analysis": analysis,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/event", response_model=LLMResponse)
async def analyze_event(event_id: str):
    """分析事件影响"""
    try:
        from app.core.graph import GraphQuery
        query = GraphQuery()

        # 获取事件信息
        cypher_query = """
            MATCH (e:MarketEvent {eventId: $eventId})
            RETURN e
        """
        result = query.execute_query(cypher_query, {"eventId": event_id})
        if not result:
            raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")

        event = dict(result[0]["e"])

        llm = _get_llm_service()
        analysis = llm.analyze_event_impact(event)

        return LLMResponse(data={
            "event_id": event_id,
            "analysis": analysis,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/sentiment", response_model=LLMResponse)
async def analyze_sentiment(request: SentimentRequest):
    """情感分析"""
    try:
        analyzer = _get_sentiment_analyzer()
        result = analyzer.analyze(request.text)
        return LLMResponse(data=result)
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/news-sentiment", response_model=LLMResponse)
async def analyze_news_sentiment(news_list: List[Dict[str, str]]):
    """新闻情感分析"""
    try:
        analyzer = _get_sentiment_analyzer()
        result = analyzer.analyze_news(news_list)
        return LLMResponse(data=result)
    except Exception as e:
        logger.error(f"News sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/report", response_model=LLMResponse)
async def generate_report(stock_code: str):
    """生成分析报告"""
    try:
        from app.core.graph import GraphQuery
        query = GraphQuery()

        # 获取公司信息
        company = query.get_company_info(stock_code)
        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{stock_code}' not found")

        # 获取财务数据
        reports = query.get_company_financial_reports(stock_code, limit=1)
        financial_data = reports[0] if reports else {}

        # 获取相关新闻
        events = query.get_company_events(stock_code, days=30, limit=5)
        news = [e.get("title", "") for e in events]

        llm = _get_llm_service()
        report = llm.generate_report(
            stock_code,
            company.get("stockName", ""),
            financial_data,
            news,
        )

        return LLMResponse(data={
            "stock_code": stock_code,
            "report": report,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/keywords", response_model=LLMResponse)
async def extract_keywords(text: str):
    """提取关键词"""
    try:
        llm = _get_llm_service()
        keywords = llm.extract_keywords(text)
        return LLMResponse(data={"keywords": keywords})
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize", response_model=LLMResponse)
async def summarize(text: str, max_length: int = 200):
    """文本摘要"""
    try:
        llm = _get_llm_service()
        summary = llm.summarize(text, max_length)
        return LLMResponse(data={"summary": summary})
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
