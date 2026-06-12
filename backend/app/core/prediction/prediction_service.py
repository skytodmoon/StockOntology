"""
预测服务

提供股价预测功能。
增强功能：
- 本体特征融合预测
- 预测结果本体校验
- 可解释性输出
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from loguru import logger

from .feature_engineering import FeatureEngineering


class PredictionService:
    """预测服务"""

    def __init__(self):
        """初始化预测服务"""
        self._feature_engineering = FeatureEngineering()
        self._ontology_feature_extractor = None
        self._reasoner = None
        self._models = {}

    @property
    def ontology_features(self):
        """获取本体特征提取器"""
        if self._ontology_feature_extractor is None:
            from .ontology_features import OntologyFeatureExtractor
            self._ontology_feature_extractor = OntologyFeatureExtractor()
        return self._ontology_feature_extractor

    @property
    def reasoner(self):
        """获取推理引擎"""
        if self._reasoner is None:
            from app.core.reasoning import OntologyReasoner
            self._reasoner = OntologyReasoner()
        return self._reasoner

    def predict_price(
        self,
        stock_code: str,
        price_data: List[Dict[str, Any]],
        days: int = 5,
        model_type: str = "simple",
    ) -> Dict[str, Any]:
        """
        预测股价

        Args:
            stock_code: 股票代码
            price_data: 历史价格数据
            days: 预测天数
            model_type: 模型类型

        Returns:
            预测结果
        """
        if len(price_data) < 20:
            return {
                "stock_code": stock_code,
                "error": "Insufficient data",
                "predictions": [],
            }

        # 准备特征
        features = self._feature_engineering.prepare_features(price_data)

        if not features:
            return {
                "stock_code": stock_code,
                "error": "Feature preparation failed",
                "predictions": [],
            }

        # 使用简单移动平均预测
        predictions = self._simple_prediction(price_data, days)

        return {
            "stock_code": stock_code,
            "model_type": model_type,
            "predictions": predictions,
            "confidence": 0.6,
            "generated_at": datetime.now().isoformat(),
        }

    def _simple_prediction(
        self,
        price_data: List[Dict[str, Any]],
        days: int,
    ) -> List[Dict[str, Any]]:
        """
        简单预测（基于移动平均）

        Args:
            price_data: 价格数据
            days: 预测天数

        Returns:
            预测结果
        """
        closes = [d.get("close", 0) for d in price_data]

        # 计算移动平均
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        ma20 = sum(closes[-20:]) / 20

        # 计算趋势
        recent_trend = (closes[-1] - closes[-5]) / closes[-5]

        predictions = []
        current_price = closes[-1]

        for i in range(days):
            # 简单趋势外推
            predicted_change = recent_trend * (1 - i * 0.1)  # 趋势衰减
            predicted_price = current_price * (1 + predicted_change)

            # 计算置信区间
            std = self._calculate_std(closes[-20:])
            confidence_interval = {
                "lower": predicted_price - 1.96 * std * (i + 1) ** 0.5,
                "upper": predicted_price + 1.96 * std * (i + 1) ** 0.5,
            }

            predictions.append({
                "day": i + 1,
                "predicted_price": round(predicted_price, 2),
                "confidence_interval": confidence_interval,
                "trend": "up" if predicted_change > 0 else "down",
            })

            current_price = predicted_price

        return predictions

    def _calculate_std(self, data: List[float]) -> float:
        """计算标准差"""
        if len(data) < 2:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
        return variance ** 0.5

    def predict_trend(
        self,
        stock_code: str,
        price_data: List[Dict[str, Any]],
        period: str = "week",
    ) -> Dict[str, Any]:
        """
        预测趋势

        Args:
            stock_code: 股票代码
            price_data: 价格数据
            period: 预测周期

        Returns:
            趋势预测
        """
        if len(price_data) < 10:
            return {
                "stock_code": stock_code,
                "trend": "unknown",
                "confidence": 0,
            }

        closes = [d.get("close", 0) for d in price_data]

        # 计算各种指标
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        current = closes[-1]

        # 判断趋势
        signals = []

        # MA 交叉
        if ma5 > ma10:
            signals.append("bullish")
        else:
            signals.append("bearish")

        # 价格相对于 MA
        if current > ma5:
            signals.append("bullish")
        else:
            signals.append("bearish")

        # 计算 RSI
        rsi = self._feature_engineering._calculate_rsi(closes, 14)
        if rsi and rsi[-1] is not None:
            if rsi[-1] > 70:
                signals.append("overbought")
            elif rsi[-1] < 30:
                signals.append("oversold")
            else:
                signals.append("neutral")

        # 综合判断
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")

        if bullish_count > bearish_count:
            trend = "bullish"
            confidence = bullish_count / len(signals)
        elif bearish_count > bullish_count:
            trend = "bearish"
            confidence = bearish_count / len(signals)
        else:
            trend = "neutral"
            confidence = 0.5

        return {
            "stock_code": stock_code,
            "period": period,
            "trend": trend,
            "confidence": round(confidence, 2),
            "signals": signals,
            "indicators": {
                "ma5": round(ma5, 2),
                "ma10": round(ma10, 2),
                "rsi": round(rsi[-1], 2) if rsi and rsi[-1] is not None else None,
            },
        }

    def calculate_risk_score(
        self,
        stock_code: str,
        price_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        计算风险分数

        Args:
            stock_code: 股票代码
            price_data: 价格数据

        Returns:
            风险评估
        """
        if len(price_data) < 20:
            return {
                "stock_code": stock_code,
                "risk_score": 50,
                "risk_level": "medium",
            }

        closes = [d.get("close", 0) for d in price_data]

        # 计算波动率
        returns = []
        for i in range(1, len(closes)):
            returns.append((closes[i] - closes[i - 1]) / closes[i - 1])

        volatility = self._calculate_std(returns) * (252 ** 0.5)  # 年化波动率

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(closes)

        # 计算风险分数 (0-100)
        risk_score = min(100, max(0, int(volatility * 100 + max_drawdown * 50)))

        # 确定风险等级
        if risk_score < 30:
            risk_level = "low"
        elif risk_score < 60:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "stock_code": stock_code,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "volatility": round(volatility, 4),
            "max_drawdown": round(max_drawdown, 4),
            "factors": self._identify_risk_factors(closes, returns),
        }

    def _calculate_max_drawdown(self, prices: List[float]) -> float:
        """计算最大回撤"""
        max_dd = 0
        peak = prices[0]

        for price in prices:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            max_dd = max(max_dd, dd)

        return max_dd

    def _identify_risk_factors(
        self,
        prices: List[float],
        returns: List[float],
    ) -> List[str]:
        """识别风险因素"""
        factors = []

        # 高波动率
        volatility = self._calculate_std(returns)
        if volatility > 0.03:
            factors.append("高波动率")

        # 连续下跌
        recent_returns = returns[-5:] if len(returns) >= 5 else returns
        if all(r < 0 for r in recent_returns):
            factors.append("连续下跌")

        # RSI 超买/超卖
        rsi = self._feature_engineering._calculate_rsi(prices, 14)
        if rsi and rsi[-1] is not None:
            if rsi[-1] > 70:
                factors.append("RSI超买")
            elif rsi[-1] < 30:
                factors.append("RSI超卖")

        # 价格偏离均线
        ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1]
        deviation = (prices[-1] - ma20) / ma20
        if abs(deviation) > 0.1:
            factors.append("价格偏离均线")

        return factors

    def find_similar_patterns(
        self,
        stock_code: str,
        price_data: List[Dict[str, Any]],
        pattern_length: int = 10,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        查找相似模式

        Args:
            stock_code: 股票代码
            price_data: 价格数据
            pattern_length: 模式长度
            top_k: 返回数量

        Returns:
            相似模式列表
        """
        if len(price_data) < pattern_length * 2:
            return []

        closes = [d.get("close", 0) for d in price_data]

        # 获取最近的模式
        recent_pattern = closes[-pattern_length:]

        # 归一化
        recent_normalized = self._normalize_pattern(recent_pattern)

        # 在历史数据中查找相似模式
        similar_patterns = []

        for i in range(len(closes) - pattern_length * 2):
            historical_pattern = closes[i:i + pattern_length]
            historical_normalized = self._normalize_pattern(historical_pattern)

            # 计算相似度（欧氏距离）
            distance = sum(
                (a - b) ** 2
                for a, b in zip(recent_normalized, historical_normalized)
            ) ** 0.5

            # 获取后续走势
            next_prices = closes[i + pattern_length:i + pattern_length + 5]
            if next_prices:
                next_return = (next_prices[-1] - closes[i + pattern_length - 1]) / closes[i + pattern_length - 1]
            else:
                next_return = 0

            similar_patterns.append({
                "start_index": i,
                "distance": distance,
                "next_return": next_return,
            })

        # 按相似度排序
        similar_patterns.sort(key=lambda x: x["distance"])

        return similar_patterns[:top_k]

    def _normalize_pattern(self, pattern: List[float]) -> List[float]:
        """归一化模式"""
        if not pattern:
            return []

        min_val = min(pattern)
        max_val = max(pattern)

        if max_val == min_val:
            return [0.5] * len(pattern)

        return [(p - min_val) / (max_val - min_val) for p in pattern]

    def predict_with_ontology(
        self,
        stock_code: str,
        price_data: List[Dict[str, Any]],
        days: int = 5,
    ) -> Dict[str, Any]:
        """
        本体增强预测

        融合技术指标 + 本体特征，预测结果接受本体规则校验。

        本体特征的独特价值：
        1. 事件影响分：近30天累积事件影响（正面/负面）
        2. 供应链风险：上下游公司集中度
        3. 竞争压力：同行业排名和竞对数量
        4. 机构情绪：机构持仓比例和变化
        5. 图谱中心性：公司在知识图谱中的重要性

        Args:
            stock_code: 股票代码
            price_data: 历史价格数据
            days: 预测天数

        Returns:
            包含技术预测、本体特征、校验结果的完整预测
        """
        # 1. 技术指标预测
        tech_prediction = self.predict_price(stock_code, price_data, days)

        # 2. 趋势判断
        trend = "neutral"
        if tech_prediction.get("predictions"):
            first_pred = tech_prediction["predictions"][0]
            trend = first_pred.get("trend", "neutral")

        # 3. 本体特征提取
        ontology_feats = self.ontology_features.extract_all(stock_code, days=30)
        flat_features = self.ontology_features.to_flat_dict(ontology_feats)

        # 4. 本体规则校验
        validation = self.reasoner.predict_with_ontology_rules(stock_code, trend)

        # 5. 融合置信度
        tech_confidence = tech_prediction.get("confidence", 0.5)
        ontology_confidence_adj = 0.0

        # 根据本体特征调整置信度
        event_impact = flat_features.get("event_impact_score", 0)
        if trend == "up" and event_impact > 0.5:
            ontology_confidence_adj += 0.1  # 正面事件支持看涨
        elif trend == "down" and event_impact < -0.5:
            ontology_confidence_adj += 0.1  # 负面事件支持看跌
        elif trend == "up" and event_impact < -0.5:
            ontology_confidence_adj -= 0.15  # 矛盾：看涨但事件负面
        elif trend == "down" and event_impact > 0.5:
            ontology_confidence_adj -= 0.15  # 矛盾：看跌但事件正面

        # 机构情绪调整
        inst_sentiment = flat_features.get("institutional_sentiment", 0)
        if (trend == "up" and inst_sentiment > 0) or (trend == "down" and inst_sentiment < 0):
            ontology_confidence_adj += 0.05

        final_confidence = max(0.1, min(0.95, tech_confidence + ontology_confidence_adj))

        return {
            "stock_code": stock_code,
            "model_type": "ontology_enhanced",
            "predictions": tech_prediction.get("predictions", []),
            "confidence": round(final_confidence, 4),
            "trend": trend,
            "ontology_features": ontology_feats,
            "ontology_features_flat": flat_features,
            "ontology_validation": validation,
            "is_consistent": validation.get("is_consistent", True),
            "contradictions": validation.get("contradictions", []),
            "explanation": self._generate_explanation(
                stock_code, trend, flat_features, validation
            ),
            "generated_at": datetime.now().isoformat(),
        }

    def _generate_explanation(
        self,
        stock_code: str,
        trend: str,
        features: Dict[str, float],
        validation: Dict[str, Any],
    ) -> str:
        """
        生成可解释的预测说明

        Args:
            stock_code: 股票代码
            trend: 预测趋势
            features: 本体特征
            validation: 校验结果

        Returns:
            可读的解释文本
        """
        trend_text = {"up": "看涨", "down": "看跌", "neutral": "中性"}.get(trend, "中性")

        lines = [f"预测 {stock_code} {trend_text}，理由如下："]

        # 事件影响
        event_score = features.get("event_impact_score", 0)
        if abs(event_score) > 0.3:
            direction = "正面" if event_score > 0 else "负面"
            lines.append(
                f"  - 近期事件影响{direction}（累积分数: {event_score:.2f}），"
                f"涉及 {int(features.get('event_count', 0))} 个事件"
            )

        # 机构情绪
        inst_sentiment = features.get("institutional_sentiment", 0)
        inst_count = int(features.get("institutional_count", 0))
        if inst_count > 0:
            sentiment_text = {1.0: "增持", -1.0: "减持", 0.0: "持平"}.get(inst_sentiment, "持平")
            lines.append(f"  - 机构情绪: {sentiment_text}（{inst_count} 家机构持仓）")

        # 竞争压力
        pressure = features.get("competition_pressure", 0)
        if pressure > 0.5:
            rank = int(features.get("industry_rank", 0))
            lines.append(f"  - 竞争压力较大（行业排名第 {rank}）")

        # 供应链风险
        supply_risk = features.get("supply_chain_risk", 0)
        if supply_risk > 0.5:
            lines.append(f"  - 供应链集中度风险较高（风险分数: {supply_risk:.2f}）")

        # 矛盾提示
        contradictions = validation.get("contradictions", [])
        if contradictions:
            lines.append("  ⚠️ 注意：存在以下矛盾：")
            for c in contradictions:
                lines.append(f"    - {c.get('message', '')}")

        return "\n".join(lines)
