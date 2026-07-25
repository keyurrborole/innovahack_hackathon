"""
Dashboard Router
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.dashboard import (
    DashboardResponse,
    DashboardStats,
    DashboardChanges,
    RecentUploadsResponse,
    RecentUpload
)
from app.core.supabase import supabase_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    user_id = current_user["sub"]
    
    stats_data = await supabase_service.get_dashboard_stats(user_id)
    
    # Calculate risk score improvement (mock for now - could be computed from historical data)
    risk_score = int(min(100, max(0, 100 - (stats_data.get("max_risk_score", 0) * 100))))
    
    return DashboardResponse(
        stats=DashboardStats(
            totalTransactions=stats_data.get("total_transactions", 0),
            suspiciousCount=stats_data.get("suspicious_count", 0),
            activeCases=stats_data.get("total_uploads", 0),
            riskScore=stats_data.get("max_risk_score", 0.0),
            patternsCount=stats_data.get("patterns_count", 0),
            addressesMonitored=stats_data.get("addresses_monitored", 0)
        ),
        changes=DashboardChanges(
            transactions="+12.5%",
            suspicious="+4.2%",
            cases="+8.1%",
            risk="+18.3%"
        )
    )


@router.get("/recent-uploads", response_model=RecentUploadsResponse)
async def get_recent_uploads(current_user: dict = Depends(get_current_user)):
    """Get recent uploads"""
    user_id = current_user["sub"]
    
    uploads, _ = await supabase_service.get_uploads_by_user(user_id, page=1, limit=5)
    
    return RecentUploadsResponse(
        uploads=[
            RecentUpload(
                id=u["id"],
                name=u.get("filename", "Unnamed"),
                date=u.get("uploaded_at", ""),
                status=u.get("status", "unknown"),
                records=u.get("row_count", 0)
            )
            for u in uploads
        ]
    )
