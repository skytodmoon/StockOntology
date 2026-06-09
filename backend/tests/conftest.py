"""
测试配置

提供测试 fixtures 和配置。
"""

import pytest
import os
from unittest.mock import MagicMock, patch

# 设置测试环境
os.environ["APP_ENV"] = "testing"


@pytest.fixture(scope="session")
def mock_neo4j():
    """Mock Neo4j 客户端"""
    with patch("backend.app.core.database.neo4j_client.GraphDatabase") as mock:
        driver = MagicMock()
        mock.driver.return_value = driver
        yield driver


@pytest.fixture(scope="session")
def mock_redis():
    """Mock Redis 客户端"""
    with patch("backend.app.core.database.redis_client.Redis") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_company_data():
    """示例公司数据"""
    return {
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "market": "SH",
        "industry": "白酒",
        "list_date": "2001-08-27",
        "market_cap": 2100000000000,
    }


@pytest.fixture
def sample_industry_data():
    """示例行业数据"""
    return {
        "code": "C1511",
        "name": "白酒制造",
        "level": 3,
        "parent_code": "C15",
    }


@pytest.fixture
def sample_financial_data():
    """示例财务数据"""
    return {
        "stock_code": "600519",
        "report_date": "2024-03-31",
        "report_type": "Q1",
        "revenue": 46700000000,
        "net_profit": 24000000000,
        "roe": 0.085,
    }


@pytest.fixture
def sample_event_data():
    """示例事件数据"""
    return {
        "event_id": "EVT001",
        "title": "央行降准0.5个百分点",
        "event_type": "PolicyEvent",
        "event_date": "2024-02-05",
        "impact_level": "High",
    }


@pytest.fixture
def sample_investor_data():
    """示例投资者数据"""
    return {
        "investor_id": "INV001",
        "name": "易方达蓝筹精选",
        "investor_type": "Fund",
    }
