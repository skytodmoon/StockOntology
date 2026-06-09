"""
预测服务

提供股价预测功能。
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
        self._models = {}

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
