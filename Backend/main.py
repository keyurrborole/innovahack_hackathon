"""
FundFlow Trace Backend - FastAPI Application
PS3: Internal bank fund-flow tracking for fraud detection (prototype)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.routers import (
    auth_router,
    dashboard_router,
    upload_router,
    analysis_router,
    graph_router,
    reports_router,
    settings_router,
    ws_router
)
from app.services.ml_service import ml_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting FundFlow Trace Backend...")
    
    # Load ML model
    try:
        ml_service.load_model()
        logger.info("ML model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FundFlow Trace Backend...")


# Create FastAPI application
app = FastAPI(
    title="FundFlow Trace API",
    description="Internal fund-flow graph analytics and ML for fraud detection (PS3 prototype)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Exception Handlers ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )



# API v1 prefix
API_V1_PREFIX = "/api/v1"

# Authentication
app.include_router(auth_router, prefix=API_V1_PREFIX)

# Dashboard
app.include_router(dashboard_router, prefix=API_V1_PREFIX)

# Upload
app.include_router(upload_router, prefix=API_V1_PREFIX)

# Analysis
app.include_router(analysis_router, prefix=API_V1_PREFIX)

# Graph
app.include_router(graph_router, prefix=API_V1_PREFIX)

# Reports
app.include_router(reports_router, prefix=API_V1_PREFIX)

# Settings
app.include_router(settings_router, prefix=API_V1_PREFIX)

# WebSocket (no prefix)
app.include_router(ws_router)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fundflow-trace-api",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to FundFlow Trace API",
        "docs": "/docs",
        "health": "/health"
    }


# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
