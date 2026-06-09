"""
本体管理 API

提供本体的查询、验证和管理接口。
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.core.ontology import (
    get_ontology_manager,
    get_ontology_validator,
    STOCK_ONTOLOGY_SCHEMA,
    RDFLIB_AVAILABLE,
)

router = APIRouter()


class OntologyResponse(BaseModel):
    """本体响应模型"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


class ValidationResultResponse(BaseModel):
    """验证结果响应模型"""
    success: bool = True
    is_valid: bool = True
    errors: int = 0
    warnings: int = 0
    issues: List[Dict[str, Any]] = []


def _get_manager():
    """获取本体管理器实例"""
    manager = get_ontology_manager()
    manager.load_all_modules()
    return manager


@router.get("/status")
async def get_ontology_status():
    """获取本体系统状态"""
    return {
        "success": True,
        "data": {
            "rdflib_available": RDFLIB_AVAILABLE,
            "schema_loaded": True,
            "schema_name": STOCK_ONTOLOGY_SCHEMA.name,
            "schema_namespace": STOCK_ONTOLOGY_SCHEMA.namespace,
        },
    }


@router.get("/classes", response_model=OntologyResponse)
async def get_classes():
    """获取所有类定义"""
    try:
        manager = _get_manager()
        classes = manager.get_classes()
        return OntologyResponse(data=classes)
    except Exception as e:
        logger.error(f"Failed to get classes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classes/{class_name}", response_model=OntologyResponse)
async def get_class(class_name: str):
    """获取指定类定义"""
    try:
        manager = _get_manager()
        cls = manager.get_class(class_name)
        if cls is None:
            raise HTTPException(status_code=404, detail=f"Class '{class_name}' not found")
        return OntologyResponse(data=cls)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get class {class_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/properties", response_model=OntologyResponse)
async def get_properties():
    """获取所有属性定义"""
    try:
        manager = _get_manager()
        properties = manager.get_properties()
        return OntologyResponse(data=properties)
    except Exception as e:
        logger.error(f"Failed to get properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{class_name}", response_model=OntologyResponse)
async def get_instances(class_name: str):
    """获取指定类的所有实例"""
    try:
        manager = _get_manager()
        instances = manager.get_instances(class_name)
        return OntologyResponse(data=instances)
    except Exception as e:
        logger.error(f"Failed to get instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hierarchy", response_model=OntologyResponse)
async def get_class_hierarchy():
    """获取类层次结构"""
    try:
        manager = _get_manager()
        hierarchy = manager.get_class_hierarchy()
        return OntologyResponse(data=hierarchy)
    except Exception as e:
        logger.error(f"Failed to get hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=OntologyResponse)
async def get_statistics():
    """获取本体统计信息"""
    try:
        manager = _get_manager()
        stats = manager.get_statistics()
        return OntologyResponse(data=stats)
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate", response_model=ValidationResultResponse)
async def validate_ontology():
    """验证本体"""
    try:
        manager = _get_manager()
        validator = get_ontology_validator(manager)
        result = validator.validate_all()
        return ValidationResultResponse(
            is_valid=result.is_valid,
            errors=len(result.errors),
            warnings=len(result.warnings),
            issues=[i.to_dict() for i in result.issues],
        )
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate/report")
async def get_validation_report():
    """获取验证报告"""
    try:
        manager = _get_manager()
        validator = get_ontology_validator(manager)
        report = validator.generate_report()
        return {"report": report}
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema", response_model=OntologyResponse)
async def get_schema():
    """获取本体 Schema"""
    try:
        return OntologyResponse(data=STOCK_ONTOLOGY_SCHEMA.dict())
    except Exception as e:
        logger.error(f"Failed to get schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=OntologyResponse)
async def sparql_query(query: str):
    """执行 SPARQL 查询"""
    try:
        manager = _get_manager()
        results = manager.query_sparql(query)
        return OntologyResponse(data=results)
    except Exception as e:
        logger.error(f"SPARQL query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
