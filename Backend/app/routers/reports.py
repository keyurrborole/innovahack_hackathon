"""
Reports Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ReportListResponse,
    ReportListItem
)
from app.schemas.common import MessageResponse
from app.services.report_service import report_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate a report"""
    user_id = current_user["sub"]
    
    try:
        result = await report_service.generate_report(
            user_id=user_id,
            upload_id=request.uploadId,
            report_type=request.type,
            report_format=request.format
        )
        
        return ReportResponse(
            id=result["reportId"],
            uploadId=request.uploadId,
            type=request.type,
            status=result["status"],
            createdAt=result.get("createdAt") or __import__("datetime").datetime.utcnow(),
            fileSize=result.get("fileSize"),
            downloadUrl=result.get("downloadUrl")
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    upload_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user)
):
    """List user's reports"""
    user_id = current_user["sub"]
    
    reports, total = await report_service.get_reports(
        user_id=user_id,
        upload_id=upload_id,
        page=page,
        limit=limit
    )
    
    return ReportListResponse(
        reports=[
            ReportListItem(
                id=r["id"],
                name=r.get("name", f"Report {r['id'][:8]}"),
                uploadId=r["upload_id"],
                type=r["type"],
                format=r["format"],
                status=r["status"],
                createdAt=r["created_at"],
                fileSize=r.get("size")
            )
            for r in reports
        ],
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0
        }
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get report details"""
    user_id = current_user["sub"]
    
    report = await report_service.get_report_by_id(report_id, user_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return ReportResponse(
        id=report["id"],
        uploadId=report["upload_id"],
        type=report["type"],
        status=report["status"],
        createdAt=report["created_at"],
        fileSize=report.get("size"),
        downloadUrl=f"/api/v1/reports/download/{report_id}" if report["status"] == "completed" else None
    )


@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download a report"""
    user_id = current_user["sub"]
    
    report_file = await report_service.get_report_file(report_id, user_id)
    
    if not report_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    content = report_file["content"]
    filename = report_file["filename"]
    media_type = report_file["media_type"]
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content))
        }
    )


@router.delete("/{report_id}", response_model=MessageResponse)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a report"""
    user_id = current_user["sub"]
    
    success = await report_service.delete_report(report_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return MessageResponse(message="Report deleted successfully")
