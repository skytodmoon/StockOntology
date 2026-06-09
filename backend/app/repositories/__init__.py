"""
数据仓库模块

提供数据访问层的抽象实现。
"""

from .base_repository import BaseRepository
from .company_repository import CompanyRepository
from .industry_repository import IndustryRepository
from .financial_repository import FinancialRepository
from .event_repository import EventRepository
from .investor_repository import InvestorRepository

__all__ = [
    "BaseRepository",
    "CompanyRepository",
    "IndustryRepository",
    "FinancialRepository",
    "EventRepository",
    "InvestorRepository",
]
