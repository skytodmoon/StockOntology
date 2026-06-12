"""
LLM 服务

提供大语言模型的集成服务，支持多种兼容 OpenAI 格式的 LLM 服务。
增强功能：
- 本体约束 Prompt（去幻觉）
- 推理链上下文注入
- 输出溯源留痕
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.config import settings


# 本体约束的系统提示词
ONTOLOGY_CONSTRAINED_SYSTEM_PROMPT = """你是一位专业的股票分析师，你的分析必须遵循以下约束：

1. **数据约束**：所有关联逻辑必须基于提供的知识图谱数据，禁止编造不存在的关系
2. **推理约束**：所有传导逻辑必须基于提供的因果推理链，不得自行推导未验证的传导路径
3. **诚实约束**：如果信息不足，必须明确说明"基于现有信息无法确定"，不得猜测
4. **溯源约束**：每个结论必须标注依据来源（图谱节点ID或推理链ID）
5. **格式约束**：输出格式必须包含：
   - 结论：明确的判断
   - 依据：支撑结论的数据和事实
   - 推理链：从事件到结论的传导路径（如果有）
   - 置信度：对结论的信心程度（高/中/低）
   - 风险提示：可能的不确定性

你的分析应该专业、严谨、可追溯。"""


class LLMService:
    """LLM 服务 - 支持多种兼容 OpenAI 格式的提供商"""

    def __init__(self, model_name: str = None, provider: str = None):
        """
        初始化 LLM 服务

        Args:
            model_name: 模型名称
            provider: LLM 提供商 (openai, ollama, vllm, local, deepseek, qwen)
        """
        self.provider = provider or settings.LLM_PROVIDER
        self.model_name = model_name or self._get_model_for_provider()
        self._client = None
        self._initialized = False

    def _get_model_for_provider(self) -> str:
        """根据提供商获取默认模型"""
        model_map = {
            "openai": settings.OPENAI_MODEL,
            "ollama": settings.OLLAMA_MODEL,
            "vllm": settings.VLLM_MODEL,
            "local": settings.LOCAL_LLM_MODEL,
            "deepseek": "deepseek-chat",
            "qwen": "qwen-turbo",
            "xiaomi": settings.XIAOMI_MODEL,
        }
        return model_map.get(self.provider, settings.OPENAI_MODEL)

    def _get_api_base_url(self) -> str:
        """根据提供商获取 API 基础地址"""
        url_map = {
            "openai": settings.OPENAI_API_BASE_URL or "https://api.openai.com/v1",
            "ollama": f"{settings.OLLAMA_HOST}/v1",
            "vllm": f"{settings.VLLM_HOST}/v1",
            "local": settings.LOCAL_LLM_URL,
            "deepseek": settings.DEEPSEEK_API_BASE_URL,
            "qwen": settings.QWEN_API_BASE_URL,
            "xiaomi": settings.XIAOMI_API_BASE_URL,
        }
        return url_map.get(self.provider, settings.LLM_API_BASE_URL)

    def _get_api_key(self) -> Optional[str]:
        """根据提供商获取 API 密钥"""
        key_map = {
            "openai": settings.OPENAI_API_KEY,
            "ollama": None,  # Ollama 不需要 API 密钥
            "vllm": settings.LLM_API_KEY,
            "local": settings.LLM_API_KEY,
            "deepseek": settings.DEEPSEEK_API_KEY,
            "qwen": settings.QWEN_API_KEY,
            "xiaomi": settings.XIAOMI_API_KEY,
        }
        return key_map.get(self.provider, settings.LLM_API_KEY)

    def _init_client(self):
        """初始化客户端 - 根据提供商选择合适的配置"""
        if self._initialized:
            return

        try:
            from langchain_openai import ChatOpenAI

            api_base_url = self._get_api_base_url()
            api_key = self._get_api_key()
            model_name = self.model_name

            # 构建参数
            client_kwargs = {
                "model": model_name,
                "temperature": settings.OPENAI_TEMPERATURE,
                "max_tokens": settings.OPENAI_MAX_TOKENS,
                "base_url": api_base_url,
            }

            # 仅当 API 密钥存在时添加
            if api_key:
                client_kwargs["api_key"] = api_key
            else:
                # 对于不需要 API 密钥的服务（如 Ollama）
                client_kwargs["api_key"] = "dummy-key"

            self._client = ChatOpenAI(**client_kwargs)
            self._initialized = True
            logger.info(f"LLM service initialized with provider: {self.provider}, model: {model_name}")

        except ImportError:
            logger.error("LangChain not installed. Install with: pip install langchain langchain-openai")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")

    def chat(self, message: str, system_prompt: str = None) -> Optional[str]:
        """
        聊天接口

        Args:
            message: 用户消息
            system_prompt: 系统提示

        Returns:
            回复内容
        """
        self._init_client()

        if not self._client:
            logger.error("LLM client not initialized")
            return None

        try:
            from langchain.schema import HumanMessage, SystemMessage

            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=message))

            response = self._client.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            return None

    def chat_with_messages(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        多轮对话接口

        Args:
            messages: 消息列表，格式: [{"role": "user/system/assistant", "content": "..."}]

        Returns:
            回复内容
        """
        self._init_client()

        if not self._client:
            logger.error("LLM client not initialized")
            return None

        try:
            from langchain.schema import HumanMessage, SystemMessage, AIMessage

            langchain_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
                else:
                    langchain_messages.append(HumanMessage(content=content))

            response = self._client.invoke(langchain_messages)
            return response.content

        except Exception as e:
            logger.error(f"LLM multi-turn chat failed: {e}")
            return None

    def analyze_stock(self, stock_info: Dict[str, Any]) -> Optional[str]:
        """
        分析股票

        Args:
            stock_info: 股票信息

        Returns:
            分析结果
        """
        prompt = f"""
请分析以下股票信息，并给出投资建议：

股票代码：{stock_info.get('stockCode', '')}
股票名称：{stock_info.get('stockName', '')}
所属行业：{stock_info.get('industry', '')}
市值：{stock_info.get('marketCap', '')}
市盈率：{stock_info.get('peRatio', '')}
市净率：{stock_info.get('pbRatio', '')}
净资产收益率：{stock_info.get('roe', '')}

请从以下几个方面进行分析：
1. 公司基本面
2. 行业地位
3. 估值水平
4. 风险因素
5. 投资建议
"""

        system_prompt = "你是一位专业的股票分析师，请基于提供的信息进行专业分析。"

        return self.chat(prompt, system_prompt)

    def analyze_event_impact(self, event_info: Dict[str, Any]) -> Optional[str]:
        """
        分析事件影响

        Args:
            event_info: 事件信息

        Returns:
            分析结果
        """
        prompt = f"""
请分析以下市场事件的影响：

事件标题：{event_info.get('title', '')}
事件类型：{event_info.get('eventType', '')}
事件日期：{event_info.get('eventDate', '')}
影响级别：{event_info.get('impactLevel', '')}
事件内容：{event_info.get('content', '')}

请分析：
1. 事件的性质和背景
2. 对市场的影响
3. 对相关行业的影响
4. 对相关公司的影响
5. 投资者应对策略
"""

        system_prompt = "你是一位专业的金融分析师，请基于提供的事件信息进行专业分析。"

        return self.chat(prompt, system_prompt)

    def generate_report(
        self,
        stock_code: str,
        stock_name: str,
        financial_data: Dict[str, Any],
        news: List[str] = None,
    ) -> Optional[str]:
        """
        生成分析报告

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            financial_data: 财务数据
            news: 相关新闻

        Returns:
            分析报告
        """
        news_text = "\n".join([f"- {n}" for n in (news or [])[:5]])

        prompt = f"""
请为 {stock_name}({stock_code}) 生成一份投资分析报告。

财务数据：
- 营业收入：{financial_data.get('revenue', 'N/A')}
- 净利润：{financial_data.get('netProfit', 'N/A')}
- 每股收益：{financial_data.get('eps', 'N/A')}
- 净资产收益率：{financial_data.get('roe', 'N/A')}
- 市盈率：{financial_data.get('peRatio', 'N/A')}
- 市净率：{financial_data.get('pbRatio', 'N/A')}

相关新闻：
{news_text}

请生成包含以下部分的报告：
1. 公司概况
2. 财务分析
3. 行业分析
4. 风险提示
5. 投资评级和目标价
"""

        system_prompt = "你是一位专业的股票分析师，请生成专业的投资分析报告。"

        return self.chat(prompt, system_prompt)

    def extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词

        Args:
            text: 文本

        Returns:
            关键词列表
        """
        prompt = f"""
请从以下文本中提取5-10个关键词，用逗号分隔：

{text[:500]}
"""

        result = self.chat(prompt)
        if result:
            return [kw.strip() for kw in result.split(",")]
        return []

    def summarize(self, text: str, max_length: int = 200) -> Optional[str]:
        """
        文本摘要

        Args:
            text: 文本
            max_length: 最大长度

        Returns:
            摘要
        """
        prompt = f"""
请将以下文本总结为不超过{max_length}字的摘要：

{text[:1000]}
"""

        return self.chat(prompt)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        生成文本嵌入向量

        Args:
            text: 文本

        Returns:
            嵌入向量
        """
        try:
            from langchain_openai import OpenAIEmbeddings

            api_base_url = self._get_api_base_url()
            api_key = self._get_api_key() or "dummy-key"

            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                base_url=api_base_url,
                api_key=api_key,
            )

            result = embeddings.embed_query(text)
            return result

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def analyze_stock_with_ontology(
        self,
        stock_code: str,
        company_info: Dict[str, Any],
        causal_chains: List[Dict[str, Any]] = None,
        ontology_features: Dict[str, Any] = None,
        financial_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        本体约束的股票分析

        所有输出必须基于提供的图谱数据和推理链，禁止编造。

        Args:
            stock_code: 股票代码
            company_info: 公司信息（来自图谱）
            causal_chains: 因果推理链列表（来自推理引擎）
            ontology_features: 本体特征（来自特征提取器）
            financial_data: 财务数据

        Returns:
            分析结果，包含结论、依据、推理链、置信度
        """
        # 构建上下文
        context_parts = []

        # 公司信息
        if company_info:
            context_parts.append(f"""
【公司信息】（来源：知识图谱 Company 节点）
- 股票代码：{company_info.get('stockCode', stock_code)}
- 公司名称：{company_info.get('stockName', '未知')}
- 所属行业：{company_info.get('industry', '未知')}
- 市值：{company_info.get('marketCap', '未知')}
""")

        # 财务数据
        if financial_data:
            context_parts.append(f"""
【财务数据】（来源：知识图谱 FinancialReport 节点）
- 营业收入：{financial_data.get('revenue', 'N/A')}
- 净利润：{financial_data.get('netProfit', 'N/A')}
- 每股收益：{financial_data.get('eps', 'N/A')}
- 净资产收益率：{financial_data.get('roe', 'N/A')}
""")

        # 因果推理链
        if causal_chains:
            chains_text = "\n".join([
                f"  - 事件 [{c.get('event', {}).get('name', '')}]：{c.get('conclusion', '')}"
                for c in causal_chains[:5]
            ])
            context_parts.append(f"""
【因果推理链】（来源：本体推理引擎 OntologyReasoner）
{chains_text}
""")

        # 本体特征
        if ontology_features:
            impact = ontology_features.get("event_impact", {})
            inst = ontology_features.get("institutional_sentiment", {})
            comp = ontology_features.get("competition_pressure", {})
            context_parts.append(f"""
【本体特征】（来源：知识图谱结构化分析）
- 事件影响分数：{impact.get('accumulated_score', 0)}
- 近期事件数量：{impact.get('event_count', 0)}
- 机构投资者数量：{inst.get('investor_count', 0)}
- 机构持仓比例：{inst.get('total_ratio', 0)}
- 竞争对手数量：{comp.get('competitor_count', 0)}
- 行业排名：第 {comp.get('rank', '?')} 名
""")

        context = "\n".join(context_parts) if context_parts else "暂无图谱数据"

        prompt = f"""
请基于以下知识图谱数据，对 {stock_code} 进行专业分析。

{context}

请严格按照以下格式输出：

## 结论
[明确的判断：看涨/看跌/中性]

## 依据
[支撑结论的具体数据，必须引用上述图谱数据]

## 推理链
[从事件到结论的传导路径，如有因果链请引用]

## 置信度
[高/中/低，并说明理由]

## 风险提示
[可能的不确定性因素]
"""

        answer = self.chat(prompt, ONTOLOGY_CONSTRAINED_SYSTEM_PROMPT)

        return {
            "stock_code": stock_code,
            "analysis": answer,
            "context_used": {
                "has_company_info": company_info is not None,
                "has_causal_chains": bool(causal_chains),
                "has_ontology_features": ontology_features is not None,
                "has_financial_data": financial_data is not None,
            },
            "constraint": "ontology_constrained",
        }

    def analyze_event_with_ontology(
        self,
        event_info: Dict[str, Any],
        causal_chain: Dict[str, Any] = None,
        affected_companies: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        本体约束的事件影响分析

        Args:
            event_info: 事件信息
            causal_chain: 因果推理链
            affected_companies: 受影响公司列表

        Returns:
            分析结果
        """
        context_parts = []

        # 事件信息
        context_parts.append(f"""
【事件信息】（来源：知识图谱 MarketEvent 节点）
- 事件标题：{event_info.get('title', '')}
- 事件类型：{event_info.get('eventType', '')}
- 事件日期：{event_info.get('eventDate', '')}
- 影响级别：{event_info.get('impactLevel', '')}
""")

        # 因果推理链
        if causal_chain:
            chain_text = causal_chain.get("chain_text", "")
            context_parts.append(f"""
【因果推理链】（来源：本体推理引擎）
{chain_text}
综合置信度：{causal_chain.get('overall_confidence', 0)}
受影响公司数：{causal_chain.get('total_affected_companies', 0)}
""")

        # 受影响公司
        if affected_companies:
            companies_text = "\n".join([
                f"  - {c.get('stock_name', '')}（{c.get('stock_code', '')}）"
                f"，传导路径：{c.get('via_rule', '')}，置信度：{c.get('confidence', 0):.2f}"
                for c in affected_companies[:10]
            ])
            context_parts.append(f"""
【受影响公司】（来源：推理引擎传导分析）
{companies_text}
""")

        context = "\n".join(context_parts)

        prompt = f"""
请基于以下知识图谱数据和推理链，分析事件影响。

{context}

请严格按照以下格式输出：

## 事件性质
[事件的本质和背景]

## 传导分析
[引用因果推理链，说明影响如何传导]

## 受影响公司
[列出受影响的公司，引用图谱数据]

## 投资建议
[基于传导分析的建议]

## 置信度
[高/中/低，引用推理链置信度]
"""

        answer = self.chat(prompt, ONTOLOGY_CONSTRAINED_SYSTEM_PROMPT)

        return {
            "event_id": event_info.get("eventId", ""),
            "analysis": answer,
            "causal_chain_used": causal_chain is not None,
            "affected_companies_count": len(affected_companies) if affected_companies else 0,
            "constraint": "ontology_constrained",
        }