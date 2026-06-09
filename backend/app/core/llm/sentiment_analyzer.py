"""
情感分析器

提供文本情感分析功能。
"""

from typing import Any, Dict, List, Optional
from loguru import logger


class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self):
        """初始化情感分析器"""
        self._model = None
        self._tokenizer = None

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感

        Args:
            text: 文本

        Returns:
            情感分析结果
        """
        # 简单的基于关键词的情感分析
        positive_words = [
            "上涨", "增长", "利好", "突破", "新高", "强势", "看多",
            "买入", "增持", "推荐", "优秀", "龙头", "领军", "创新高",
        ]

        negative_words = [
            "下跌", "下降", "利空", "破位", "新低", "弱势", "看空",
            "卖出", "减持", "回避", "风险", "亏损", "下滑", "创新低",
        ]

        neutral_words = [
            "震荡", "盘整", "观望", "持平", "稳定", "维持",
        ]

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        neutral_count = sum(1 for word in neutral_words if word in text_lower)

        total = positive_count + negative_count + neutral_count

        if total == 0:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "positive": 0.33,
                "negative": 0.33,
                "neutral": 0.34,
                "keywords": [],
            }

        positive_ratio = positive_count / total
        negative_ratio = negative_count / total
        neutral_ratio = neutral_count / total

        # 计算情感分数 (0-1, 越高越积极)
        score = (positive_count - negative_count) / total
        normalized_score = (score + 1) / 2  # 归一化到 0-1

        # 确定情感类别
        if positive_ratio > negative_ratio and positive_ratio > neutral_ratio:
            sentiment = "positive"
        elif negative_ratio > positive_ratio and negative_ratio > neutral_ratio:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # 提取关键词
        keywords = []
        for word in positive_words + negative_words + neutral_words:
            if word in text_lower:
                keywords.append(word)

        return {
            "sentiment": sentiment,
            "score": normalized_score,
            "positive": positive_ratio,
            "negative": negative_ratio,
            "neutral": neutral_ratio,
            "keywords": keywords[:10],
        }

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        批量分析情感

        Args:
            texts: 文本列表

        Returns:
            情感分析结果列表
        """
        return [self.analyze(text) for text in texts]

    def analyze_news(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析新闻情感

        Args:
            news_list: 新闻列表

        Returns:
            新闻情感分析结果
        """
        if not news_list:
            return {
                "overall_sentiment": "neutral",
                "overall_score": 0.5,
                "news_count": 0,
                "sentiment_distribution": {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                },
            }

        sentiments = []
        for news in news_list:
            title = news.get("title", "")
            content = news.get("content", "")
            text = f"{title} {content}"
            sentiment = self.analyze(text)
            sentiments.append(sentiment)

        # 计算整体情感
        avg_score = sum(s["score"] for s in sentiments) / len(sentiments)

        positive_count = sum(1 for s in sentiments if s["sentiment"] == "positive")
        negative_count = sum(1 for s in sentiments if s["sentiment"] == "negative")
        neutral_count = sum(1 for s in sentiments if s["sentiment"] == "neutral")

        if positive_count > negative_count and positive_count > neutral_count:
            overall_sentiment = "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        return {
            "overall_sentiment": overall_sentiment,
            "overall_score": avg_score,
            "news_count": len(news_list),
            "sentiment_distribution": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
            },
            "details": sentiments,
        }

    def get_sentiment_label(self, score: float) -> str:
        """
        获取情感标签

        Args:
            score: 情感分数

        Returns:
            情感标签
        """
        if score >= 0.7:
            return "非常积极"
        elif score >= 0.6:
            return "积极"
        elif score >= 0.4:
            return "中性"
        elif score >= 0.3:
            return "消极"
        else:
            return "非常消极"

    def calculate_market_sentiment(
        self,
        news_sentiments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        计算市场情绪

        Args:
            news_sentiments: 新闻情感列表

        Returns:
            市场情绪
        """
        if not news_sentiments:
            return {
                "market_sentiment": "neutral",
                "confidence": 0.5,
                "description": "无足够数据判断市场情绪",
            }

        avg_score = sum(s["score"] for s in news_sentiments) / len(news_sentiments)

        if avg_score >= 0.65:
            sentiment = "bullish"
            description = "市场情绪乐观，投资者信心较强"
        elif avg_score >= 0.55:
            sentiment = "slightly_bullish"
            description = "市场情绪偏乐观"
        elif avg_score >= 0.45:
            sentiment = "neutral"
            description = "市场情绪中性，投资者观望为主"
        elif avg_score >= 0.35:
            sentiment = "slightly_bearish"
            description = "市场情绪偏悲观"
        else:
            sentiment = "bearish"
            description = "市场情绪悲观，投资者信心不足"

        # 计算置信度
        score_variance = sum((s["score"] - avg_score) ** 2 for s in news_sentiments) / len(news_sentiments)
        confidence = max(0.3, min(0.9, 1 - score_variance))

        return {
            "market_sentiment": sentiment,
            "score": avg_score,
            "confidence": confidence,
            "description": description,
            "sample_size": len(news_sentiments),
        }
