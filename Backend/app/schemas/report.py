"""
Report Schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
from datetime import datetime


class ReportGenerateRequest(BaseModel):
    uploadId: str
    type: Literal["compliance", "investigation", "summary"]
    format: Literal["pdf", "excel", "json"] = "pdf"
    includeGraph: bool = True
    includePatterns: bool = True
    includeAddresses: bool = True


class ReportResponse(BaseModel):
    id: str
    uploadId: str
    type: str
    status: str
    createdAt: datetime
    fileSize: Optional[int] = None
    downloadUrl: Optional[str] = None


class ReportListItem(BaseModel):
    id: str
    name: str
    uploadId: str
    type: str
    format: str
    status: str
    createdAt: datetime
    fileSize: Optional[int] = None


class ReportListResponse(BaseModel):
    reports: List[ReportListItem]
    pagination: Dict[str, int]
