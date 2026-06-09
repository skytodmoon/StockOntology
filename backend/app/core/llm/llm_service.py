"""
LLM 服务

提供大语言模型的集成服务，支持多种兼容 OpenAI 格式的 LLM 服务。
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.config import settings


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