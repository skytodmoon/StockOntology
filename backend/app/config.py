"""
配置管理模块

支持从环境变量和 .env 文件加载配置，使用 pydantic-settings 进行验证。
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import os
import json


class Settings(BaseSettings):
    """应用配置"""

    # Application
    APP_NAME: str = "StockOntology"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_CONNECTION_POOL: int = 50
    NEO4J_CONNECTION_TIMEOUT: int = 30

    # PostgreSQL/TimescaleDB
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "stock_ontology"

    @property
    def POSTGRES_URL(self) -> str:
        """构建 PostgreSQL 连接 URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        """构建 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # TimescaleDB
    TIMESCALE_HOST: str = "localhost"
    TIMESCALE_PORT: int = 5433
    TIMESCALE_USER: str = "postgres"
    TIMESCALE_PASSWORD: str = "password"
    TIMESCALE_DB: str = "stock_ontology"

    @property
    def TIMESCALE_URL(self) -> str:
        """构建 TimescaleDB 连接 URL"""
        return f"postgresql://{self.TIMESCALE_USER}:{self.TIMESCALE_PASSWORD}@{self.TIMESCALE_HOST}:{self.TIMESCALE_PORT}/{self.TIMESCALE_DB}"

    # Milvus (Vector Database)
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "stock_embeddings"

    # ChromaDB (Alternative Vector Database)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "stock_docs"

    # OpenAI API
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_API_BASE_URL: Optional[str] = None

    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # openai, ollama, vllm, local, deepseek, qwen
    LLM_API_BASE_URL: str = "http://localhost:8001/v1"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "THUDM/chatglm3-6b"

    # Ollama Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # vLLM Configuration
    VLLM_HOST: str = "http://localhost:8000"
    VLLM_MODEL: str = "mistral-7b-instruct"

    # DeepSeek Configuration
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE_URL: str = "https://api.deepseek.com/v1"

    # Qwen Configuration
    QWEN_API_KEY: Optional[str] = None
    QWEN_API_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Xiaomi MiMo Configuration
    XIAOMI_API_KEY: Optional[str] = None
    XIAOMI_API_BASE_URL: str = "https://token-plan-cn.xiaomimimo.com/v1"
    XIAOMI_MODEL: str = "mimo-v2.5-pro"

    # Local LLM
    LOCAL_LLM_ENABLED: bool = False
    LOCAL_LLM_MODEL: str = "THUDM/chatglm3-6b"
    LOCAL_LLM_URL: str = "http://localhost:8001/v1"

    # Tushare
    TUSHARE_TOKEN: Optional[str] = None

    # AKShare
    AKSHARE_ENABLED: bool = True

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # Model Paths
    MODEL_DIR: str = "models/checkpoints"
    PRETRAINED_DIR: str = "models/pretrained"

    # Ontology
    ONTOLOGY_DIR: str = "ontology/core"
    ONTOLOGY_FORMAT: str = "owl"  # owl, rdf, json-ld

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 允许额外的字段


class DevelopmentSettings(Settings):
    """开发环境配置"""
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """生产环境配置"""
    APP_ENV: str = "production"
    APP_DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class TestingSettings(Settings):
    """测试环境配置"""
    APP_ENV: str = "testing"
    APP_DEBUG: bool = True
    NEO4J_DATABASE: str = "test"
    POSTGRES_DB: str = "stock_ontology_test"
    REDIS_DB: int = 15


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    根据 APP_ENV 环境变量返回对应的配置实例
    """
    env = os.getenv("APP_ENV", "development")

    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }

    settings_class = settings_map.get(env, Settings)
    return settings_class()


# 全局配置实例
settings = get_settings()
