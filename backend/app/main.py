"""
StockOntology 后端应用入口

基于 FastAPI 构建的股票分析预测系统 API。
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
import time

from app.config import settings
from app.core.database import get_neo4j_client, get_redis_client


# 配置日志
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)
logger.add(settings.LOG_FILE, rotation="10 MB", retention="7 days")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    在应用启动和关闭时执行初始化和清理操作。
    """
    # 启动时执行
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Environment: {settings.APP_ENV}")

    # 初始化数据库连接
    try:
        neo4j = get_neo4j_client()
        neo4j.init_database()
        logger.info("Neo4j database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {e}")

    try:
        redis = get_redis_client()
        if redis.ping():
            logger.info("Redis connection established")
        else:
            logger.warning("Redis connection failed")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

    yield

    # 关闭时执行
    logger.info("Shutting down...")

    try:
        neo4j = get_neo4j_client()
        neo4j.close()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j: {e}")

    try:
        redis = get_redis_client()
        redis.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用

    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="基于本体论的股票分析预测系统 API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 配置 CORS
    # 解析 CORS_ORIGINS 字符串为列表
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册中间件
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """添加请求处理时间头"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # 注册异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器"""
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "detail": str(exc) if settings.APP_DEBUG else None,
            },
        )

    # 注册路由
    register_routes(app)

    return app


def register_routes(app: FastAPI):
    """
    注册 API 路由

    Args:
        app: FastAPI 应用实例
    """
    # 健康检查
    @app.get("/health", tags=["System"])
    async def health_check() -> Dict[str, Any]:
        """健康检查接口"""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": "0.1.0",
        }

    # 系统信息
    @app.get("/api/v1/system/info", tags=["System"])
    async def system_info() -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "0.1.0",
            "debug": settings.APP_DEBUG,
        }

    # 数据库状态
    @app.get("/api/v1/system/database", tags=["System"])
    async def database_status() -> Dict[str, Any]:
        """获取数据库状态"""
        status = {}

        # Neo4j 状态
        try:
            neo4j = get_neo4j_client()
            neo4j_stats = neo4j.get_database_stats()
            status["neo4j"] = {
                "status": "connected",
                "stats": neo4j_stats,
            }
        except Exception as e:
            status["neo4j"] = {
                "status": "error",
                "error": str(e),
            }

        # Redis 状态
        try:
            redis = get_redis_client()
            if redis.ping():
                redis_info = redis.get_memory_usage()
                status["redis"] = {
                    "status": "connected",
                    "memory": redis_info,
                }
            else:
                status["redis"] = {"status": "disconnected"}
        except Exception as e:
            status["redis"] = {
                "status": "error",
                "error": str(e),
            }

        return status

    # 注册 API 路由模块
    from app.api import ontology, graph, companies, industries, events, investors, financial, collectors, llm, prediction

    app.include_router(ontology.router, prefix="/api/v1/ontology", tags=["Ontology"])
    app.include_router(graph.router, prefix="/api/v1/graph", tags=["Knowledge Graph"])
    app.include_router(companies.router, prefix="/api/v1/companies", tags=["Companies"])
    app.include_router(industries.router, prefix="/api/v1/industries", tags=["Industries"])
    app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
    app.include_router(investors.router, prefix="/api/v1/investors", tags=["Investors"])
    app.include_router(financial.router, prefix="/api/v1/financial", tags=["Financial"])
    app.include_router(collectors.router, prefix="/api/v1/collectors", tags=["Data Collectors"])
    app.include_router(llm.router, prefix="/api/v1/llm", tags=["LLM Analysis"])
    app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["Prediction"])


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
