"""
AI 预测模块

提供股价预测和趋势分析功能。
"""

from .feature_engineering import FeatureEngineering
from .prediction_service import PredictionService

__all__ = [
    "FeatureEngineering",
    "PredictionService",
]
