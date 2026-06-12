"""
RAG 服务

提供检索增强生成功能。
增强功能：
- 注入因果推理链作为上下文
- 注入本体 schema 告知 LLM 数据语义类型
- 注入历史分析结果作为参考
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.config import settings
from app.core.graph import GraphQuery


class RAGService:
    """RAG 服务"""

    def __init__(self):
        """初始化 RAG 服务"""
        self._graph_query = None
        self._llm_service = None
        self._reasoner = None
        self._vector_store = None

    @property
    def graph_query(self):
        """获取图谱查询服务"""
        if self._graph_query is None:
            self._graph_query = GraphQuery()
        return self._graph_query

    @property
    def llm_service(self):
        """获取 LLM 服务"""
        if self._llm_service is None:
            from .llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    @property
    def reasoner(self):
        """获取推理引擎"""
        if self._reasoner is None:
            from app.core.reasoning import OntologyReasoner
            self._reasoner = OntologyReasoner()
        return self._reasoner

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        回答问题

        Args:
            question: 用户问题

        Returns:
            回答结果
        """
        # 1. 解析问题，提取实体
        entities = self._extract_entities(question)

        # 2. 从知识图谱获取相关信息
        context = self._retrieve_context(question, entities)

        # 3. 使用 LLM 生成回答
        answer = self._generate_answer(question, context)

        return {
            "question": question,
            "answer": answer,
            "entities": entities,
            "context": context,
        }

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        提取实体

        Args:
            text: 文本

        Returns:
            实体字典
        """
        entities = {
            "stock_codes": [],
            "stock_names": [],
            "industries": [],
            "keywords": [],
        }

        # 提取股票代码（6位数字）
        import re
        codes = re.findall(r'\b\d{6}\b', text)
        entities["stock_codes"] = list(set(codes))

        # 常见股票名称映射
        stock_name_map = {
            "茅台": "600519",
            "平安": "601318",
            "招行": "600036",
            "宁德时代": "300750",
            "比亚迪": "002594",
        }

        for name, code in stock_name_map.items():
            if name in text:
                entities["stock_names"].append(name)
                if code not in entities["stock_codes"]:
                    entities["stock_codes"].append(code)

        # 关键词
        keywords = ["行业", "财报", "业绩", "增长", "下跌", "上涨", "风险", "投资"]
        entities["keywords"] = [kw for kw in keywords if kw in text]

        return entities

    def _retrieve_context(
        self,
        question: str,
        entities: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """
        检索上下文（增强版）

        除了原有的公司/财务/事件信息，还注入：
        - 因果推理链
        - 本体特征
        - 累积影响分数

        Args:
            question: 问题
            entities: 实体

        Returns:
            上下文信息
        """
        context = {
            "companies": [],
            "industries": [],
            "events": [],
            "financial": [],
            "causal_chains": [],
            "ontology_features": {},
        }

        # 获取公司信息
        for code in entities["stock_codes"][:3]:
            company = self.graph_query.get_company_info(code)
            if company:
                context["companies"].append(company)

            # 获取财务数据
            reports = self.graph_query.get_company_financial_reports(code, limit=2)
            context["financial"].extend(reports)

            # 获取因果推理链（增强）
            try:
                chains = self.reasoner.get_all_chains_for_stock(code, days=30, limit=3)
                context["causal_chains"].extend(chains)
            except Exception as e:
                logger.warning(f"Failed to get causal chains for {code}: {e}")

            # 获取累积影响分数（增强）
            try:
                impact = self.reasoner.get_accumulated_impact(code, days=30)
                context["ontology_features"][code] = impact
            except Exception as e:
                logger.warning(f"Failed to get impact for {code}: {e}")

        # 获取相关事件
        for code in entities["stock_codes"][:2]:
            events = self.graph_query.get_company_events(code, days=30, limit=5)
            context["events"].extend(events)

        return context

    def _generate_answer(
        self,
        question: str,
        context: Dict[str, Any],
    ) -> str:
        """
        生成回答

        Args:
            question: 问题
            context: 上下文

        Returns:
            回答内容
        """
        # 构建上下文文本
        context_text = self._build_context_text(context)

        prompt = f"""
基于以下信息回答问题：

上下文信息：
{context_text}

问题：{question}

请提供准确、专业的回答。
"""

        system_prompt = """你是一位专业的股票分析师和投资顾问。
请基于提供的知识图谱信息回答用户问题。
如果信息不足，请说明并给出一般性建议。"""

        answer = self.llm_service.chat(prompt, system_prompt)
        return answer or "抱歉，无法生成回答。"

    def _build_context_text(self, context: Dict[str, Any]) -> str:
        """
        构建上下文文本（增强版）

        包含因果推理链和本体特征，为 LLM 提供结构化知识。

        Args:
            context: 上下文信息

        Returns:
            上下文文本
        """
        parts = []

        # 公司信息
        if context.get("companies"):
            parts.append("【公司信息】（来源：知识图谱）")
            for company in context["companies"]:
                parts.append(
                    f"- {company.get('stockName', '')}({company.get('stockCode', '')}): "
                    f"行业={company.get('industry', '')}, 市值={company.get('marketCap', '')}"
                )

        # 财务数据
        if context.get("financial"):
            parts.append("\n【财务数据】（来源：知识图谱 FinancialReport）")
            for report in context["financial"][:3]:
                parts.append(
                    f"- {report.get('reportDate', '')}: "
                    f"营收={report.get('revenue', '')}, 净利润={report.get('netProfit', '')}"
                )

        # 事件
        if context.get("events"):
            parts.append("\n【相关事件】（来源：知识图谱 MarketEvent）")
            for event in context["events"][:3]:
                parts.append(f"- {event.get('eventDate', '')}: {event.get('title', '')}")

        # 因果推理链（增强）
        if context.get("causal_chains"):
            parts.append("\n【因果推理链】（来源：本体推理引擎）")
            for chain in context["causal_chains"][:3]:
                if isinstance(chain, dict):
                    event_name = chain.get("event_name", chain.get("event", {}).get("name", ""))
                    conclusion = chain.get("conclusion", "")
                    confidence = chain.get("overall_confidence", 0)
                    parts.append(f"- 事件 [{event_name}]：{conclusion}（置信度: {confidence:.2f}）")

        # 本体特征（增强）
        if context.get("ontology_features"):
            parts.append("\n【本体特征】（来源：知识图谱结构化分析）")
            for code, impact in context["ontology_features"].items():
                if isinstance(impact, dict):
                    score = impact.get("accumulated_score", 0)
                    count = impact.get("event_count", 0)
                    parts.append(f"- {code}: 累积影响分数={score}, 近期事件数={count}")

        return "\n".join(parts) if parts else "暂无相关信息"

    def chat_with_context(
        self,
        message: str,
        stock_code: str = None,
    ) -> Dict[str, Any]:
        """
        带上下文的聊天

        Args:
            message: 用户消息
            stock_code: 股票代码

        Returns:
            聊天结果
        """
        context = {}

        if stock_code:
            # 获取公司信息
            company = self.graph_query.get_company_info(stock_code)
            if company:
                context["company"] = company

            # 获取最新财报
            reports = self.graph_query.get_company_financial_reports(stock_code, limit=1)
            if reports:
                context["latest_report"] = reports[0]

        # 构建提示
        context_text = ""
        if context.get("company"):
            c = context["company"]
            context_text += f"公司：{c.get('stockName', '')}({c.get('stockCode', '')})\n"
            context_text += f"行业：{c.get('industry', '')}\n"

        if context.get("latest_report"):
            r = context["latest_report"]
            context_text += f"最新财报：{r.get('reportDate', '')}\n"
            context_text += f"营收：{r.get('revenue', '')}, 净利润：{r.get('netProfit', '')}\n"

        prompt = f"""
{f'背景信息：{context_text}' if context_text else ''}

用户问题：{message}

请回答用户的问题。
"""

        answer = self.llm_service.chat(prompt)

        return {
            "message": message,
            "answer": answer,
            "context": context,
        }
