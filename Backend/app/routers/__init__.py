"""
API Routers
"""
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.upload import router as upload_router
from app.routers.analysis import router as analysis_router
from app.routers.graph import router as graph_router
from app.routers.reports import router as reports_router
from app.routers.settings import router as settings_router
from app.routers.ws import router as ws_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "upload_router",
    "analysis_router",
    "graph_router",
    "reports_router",
    "settings_router",
    "ws_router"
]