"""
特征工程模块

提供股票预测的特征工程功能。
"""

from typing import Any, Dict, List, Optional
import numpy as np
from loguru import logger


class FeatureEngineering:
    """特征工程"""

    def __init__(self):
        """初始化特征工程"""
        pass

    def calculate_technical_indicators(
        self,
        prices: List[float],
        volumes: List[float] = None,
    ) -> Dict[str, List[float]]:
        """
        计算技术指标

        Args:
            prices: 价格序列
            volumes: 成交量序列

        Returns:
            技术指标字典
        """
        if len(prices) < 2:
            return {}

        indicators = {}

        # 移动平均线
        indicators["ma5"] = self._calculate_ma(prices, 5)
        indicators["ma10"] = self._calculate_ma(prices, 10)
        indicators["ma20"] = self._calculate_ma(prices, 20)

        # RSI
        indicators["rsi14"] = self._calculate_rsi(prices, 14)

        # MACD
        macd, signal, hist = self._calculate_macd(prices)
        indicators["macd"] = macd
        indicators["macd_signal"] = signal
        indicators["macd_hist"] = hist

        # 布林带
        upper, middle, lower = self._calculate_bollinger(prices, 20)
        indicators["boll_upper"] = upper
        indicators["boll_middle"] = middle
        indicators["boll_lower"] = lower

        # 成交量指标
        if volumes:
            indicators["vol_ma5"] = self._calculate_ma(volumes, 5)
            indicators["vol_ma10"] = self._calculate_ma(volumes, 10)

        return indicators

    def _calculate_ma(self, data: List[float], period: int) -> List[Optional[float]]:
        """计算移动平均"""
        result = []
        for i in range(len(data)):
            if i < period - 1:
                result.append(None)
            else:
                avg = sum(data[i - period + 1:i + 1]) / period
                result.append(avg)
        return result

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[Optional[float]]:
        """计算 RSI"""
        if len(prices) < period + 1:
            return [None] * len(prices)

        result = [None] * period
        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        for i in range(period, len(prices)):
            avg_gain = sum(gains[i - period:i]) / period
            avg_loss = sum(losses[i - period:i]) / period

            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                result.append(rsi)

        return result

    def _calculate_macd(
        self,
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> tuple:
        """计算 MACD"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)

        macd = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd.append(ema_fast[i] - ema_slow[i])
            else:
                macd.append(None)

        # 计算信号线
        valid_macd = [m for m in macd if m is not None]
        if len(valid_macd) >= signal:
            signal_line = self._calculate_ema(valid_macd, signal)
            signal_line = [None] * (len(macd) - len(signal_line)) + signal_line
        else:
            signal_line = [None] * len(macd)

        # 计算柱状
        histogram = []
        for i in range(len(macd)):
            if macd[i] is not None and signal_line[i] is not None:
                histogram.append(macd[i] - signal_line[i])
            else:
                histogram.append(None)

        return macd, signal_line, histogram

    def _calculate_ema(self, data: List[float], period: int) -> List[Optional[float]]:
        """计算 EMA"""
        if len(data) < period:
            return [None] * len(data)

        multiplier = 2 / (period + 1)
        result = [None] * (period - 1)

        # 第一个 EMA 使用 SMA
        first_ema = sum(data[:period]) / period
        result.append(first_ema)

        for i in range(period, len(data)):
            ema = (data[i] - result[-1]) * multiplier + result[-1]
            result.append(ema)

        return result

    def _calculate_bollinger(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: int = 2,
    ) -> tuple:
        """计算布林带"""
        upper = []
        middle = []
        lower = []

        for i in range(len(prices)):
            if i < period - 1:
                upper.append(None)
                middle.append(None)
                lower.append(None)
            else:
                window = prices[i - period + 1:i + 1]
                avg = sum(window) / period
                variance = sum((x - avg) ** 2 for x in window) / period
                std = variance ** 0.5

                middle.append(avg)
                upper.append(avg + std_dev * std)
                lower.append(avg - std_dev * std)

        return upper, middle, lower

    def prepare_features(
        self,
        price_data: List[Dict[str, Any]],
        lookback: int = 20,
    ) -> Dict[str, Any]:
        """
        准备预测特征

        Args:
            price_data: 价格数据列表
            lookback: 回看天数

        Returns:
            特征数据
        """
        if len(price_data) < lookback:
            logger.warning(f"Not enough data: {len(price_data)} < {lookback}")
            return {}

        # 提取价格和成交量
        closes = [d.get("close", 0) for d in price_data]
        volumes = [d.get("volume", 0) for d in price_data]
        highs = [d.get("high", 0) for d in price_data]
        lows = [d.get("low", 0) for d in price_data]

        # 计算技术指标
        indicators = self.calculate_technical_indicators(closes, volumes)

        # 准备特征
        features = {
            "close": closes[-lookback:],
            "volume": volumes[-lookback:],
            "high": highs[-lookback:],
            "low": lows[-lookback:],
        }

        # 添加技术指标
        for key, values in indicators.items():
            valid_values = [v for v in values[-lookback:] if v is not None]
            if valid_values:
                features[key] = values[-lookback:]

        # 计算价格变化
        price_changes = []
        for i in range(1, len(closes)):
            change = (closes[i] - closes[i - 1]) / closes[i - 1]
            price_changes.append(change)
        features["price_change"] = price_changes[-lookback:]

        # 计算波动率
        if len(price_changes) >= 5:
            volatility = self._calculate_volatility(price_changes[-lookback:])
            features["volatility"] = volatility

        return features

    def _calculate_volatility(
        self,
        returns: List[float],
        window: int = 5,
    ) -> List[Optional[float]]:
        """计算波动率"""
        result = []
        for i in range(len(returns)):
            if i < window - 1:
                result.append(None)
            else:
                window_returns = returns[i - window + 1:i + 1]
                mean = sum(window_returns) / window
                variance = sum((r - mean) ** 2 for r in window_returns) / window
                result.append(variance ** 0.5)
        return result

    def create_sequences(
        self,
        features: Dict[str, List[float]],
        sequence_length: int = 10,
        target_field: str = "close",
    ) -> tuple:
        """
        创建训练序列

        Args:
            features: 特征数据
            sequence_length: 序列长度
            target_field: 目标字段

        Returns:
            (X, y) 元组
        """
        target = features.get(target_field, [])
        if not target:
            return np.array([]), np.array([])

        # 准备特征矩阵
        feature_keys = [k for k in features.keys() if k != target_field]
        feature_matrix = []

        for i in range(len(target)):
            row = []
            for key in feature_keys:
                values = features[key]
                if i < len(values) and values[i] is not None:
                    row.append(values[i])
                else:
                    row.append(0)
            feature_matrix.append(row)

        X = []
        y = []

        for i in range(sequence_length, len(target)):
            X.append(feature_matrix[i - sequence_length:i])
            y.append(target[i])

        return np.array(X), np.array(y)
