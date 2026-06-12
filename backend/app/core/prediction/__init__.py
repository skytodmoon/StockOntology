"""
AI 预测模块

提供股价预测和趋势分析功能。
增强功能：
- 本体特征提取（OntologyFeatureExtractor）
- 知识增强预测
- 预测结果本体校验
"""

from .feature_engineering import FeatureEngineering
from .prediction_service import PredictionService
from .ontology_features import OntologyFeatureExtractor

__all__ = [
    "FeatureEngineering",
    "PredictionService",
    "OntologyFeatureExtractor",
]
