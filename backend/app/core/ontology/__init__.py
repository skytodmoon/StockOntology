"""
本体引擎模块

提供本体加载、验证、查询和管理功能。
"""

from .ontology_manager import OntologyManager, RDFLIB_AVAILABLE
from .ontology_schema import OntologySchema, STOCK_ONTOLOGY_SCHEMA
from .ontology_validator import OntologyValidator, ValidationResult, ValidationIssue

__all__ = [
    "OntologyManager",
    "OntologySchema",
    "STOCK_ONTOLOGY_SCHEMA",
    "OntologyValidator",
    "ValidationResult",
    "ValidationIssue",
    "RDFLIB_AVAILABLE",
]


def get_ontology_manager(ontology_dir: str = None) -> OntologyManager:
    """
    获取本体管理器实例

    Args:
        ontology_dir: 本体文件目录

    Returns:
        OntologyManager 实例
    """
    return OntologyManager(ontology_dir)


def get_ontology_validator(ontology_manager: OntologyManager = None) -> OntologyValidator:
    """
    获取本体验证器实例

    Args:
        ontology_manager: 本体管理器实例

    Returns:
        OntologyValidator 实例
    """
    if ontology_manager is None:
        ontology_manager = get_ontology_manager()
    return OntologyValidator(ontology_manager)
