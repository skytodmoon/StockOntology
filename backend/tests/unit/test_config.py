"""
配置模块测试
"""

import pytest
from unittest.mock import patch
import os

from app.config import Settings, get_settings


class TestSettings:
    """Settings 测试类"""

    def test_default_values(self):
        """测试默认值"""
        settings = Settings()
        assert settings.APP_NAME == "StockOntology"
        assert settings.APP_ENV == "development"
        assert settings.APP_DEBUG is True
        assert settings.APP_PORT == 8000

    def test_neo4j_config(self):
        """测试 Neo4j 配置"""
        settings = Settings()
        assert settings.NEO4J_URI == "bolt://localhost:7687"
        assert settings.NEO4J_USER == "neo4j"
        assert settings.NEO4J_DATABASE == "neo4j"

    def test_postgres_config(self):
        """测试 PostgreSQL 配置"""
        settings = Settings()
        assert settings.POSTGRES_HOST == "localhost"
        assert settings.POSTGRES_PORT == 5432
        assert settings.POSTGRES_DB == "stock_ontology"

    def test_postgres_url(self):
        """测试 PostgreSQL URL 构建"""
        settings = Settings()
        url = settings.POSTGRES_URL
        assert "postgresql://" in url
        assert "localhost" in url
        assert "5432" in url

    def test_redis_config(self):
        """测试 Redis 配置"""
        settings = Settings()
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379

    def test_redis_url(self):
        """测试 Redis URL 构建"""
        settings = Settings()
        url = settings.REDIS_URL
        assert "redis://" in url

    def test_openai_config(self):
        """测试 OpenAI 配置"""
        settings = Settings()
        assert settings.OPENAI_MODEL == "gpt-4-turbo-preview"
        assert settings.OPENAI_TEMPERATURE == 0.7

    @patch.dict(os.environ, {"APP_ENV": "testing"})
    def test_testing_environment(self):
        """测试测试环境配置"""
        # 清除缓存
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.APP_ENV == "testing"

    def test_cors_origins(self):
        """测试 CORS 配置"""
        settings = Settings()
        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) > 0
