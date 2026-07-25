"""
Upload Service - File handling and processing
"""
import os
import uuid
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import aiofiles
import json

from fastapi import UploadFile

from app.config import settings
from app.core.supabase import supabase_service
from app.core.websocket import ws_manager
from app.services.ml_service import ml_service


class UploadService:
    """
    Service for handling file uploads and processing
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_upload(
        self,
        file: UploadFile,
        user_id: str,
        description: Optional[str] = None
    ) -> Dict:
        """
        Process an uploaded file and automatically run ML analysis
        """
        # Generate upload ID
        upload_id = str(uuid.uuid4())
        
        # Validate file
        filename = file.filename or "unknown"
        file_ext = Path(filename).suffix.lower()
        
        # Normalize extension check - handle both ".csv" and "csv" formats
        allowed = settings.allowed_extensions_list
        ext_without_dot = file_ext.lstrip('.')
        ext_with_dot = f'.{ext_without_dot}'
        
        if ext_without_dot not in [e.lstrip('.') for e in allowed] and ext_with_dot not in allowed:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Save file
        file_path = self.upload_dir / f"{upload_id}{file_ext}"
        
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise ValueError(f"File too large. Max size: {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB")
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create upload record matching exact schema (columns: id, user_id, filename, uploaded_at, status, row_count)
        upload_record = await supabase_service.create_upload({
            "id": upload_id,
            "user_id": user_id,
            "filename": file.filename,
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "processing",
            "row_count": 0
        })
        
        # Notify via WebSocket
        await ws_manager.broadcast_upload_progress(
            user_id, upload_id, 10, "processing", "File uploaded, starting processing..."
        )
        
        # Process file in background (simplified - in production use Celery/background tasks)
        try:
            records = await self._process_file(file_path, file_ext, upload_id, user_id)
            
            # Update upload record
            await supabase_service.update_upload(upload_id, {
                "status": "completed",
                "row_count": records
            })
            
            await ws_manager.broadcast_upload_progress(
                user_id, upload_id, 70, "processing", "Running ML analysis..."
            )
            
            # AUTO-RUN ML ANALYSIS after file processing
            await self._run_auto_analysis(file_path, file_ext, upload_id, user_id)
            
            await ws_manager.broadcast_upload_progress(
                user_id, upload_id, 100, "completed", "Processing and analysis complete!"
            )
            
        except Exception as e:
            await supabase_service.update_upload(upload_id, {
                "status": "failed"
            })
            
            await ws_manager.broadcast_upload_progress(
                user_id, upload_id, 0, "failed", f"Processing failed: {str(e)}"
            )
            raise
        
        return {
            "id": upload_id,
            "name": file.filename,
            "status": "processing",
            "uploadedAt": datetime.utcnow().isoformat()
        }
    
    async def _process_file(
        self,
        file_path: Path,
        file_ext: str,
        upload_id: str,
        user_id: str
    ) -> int:
        """
        Process uploaded file and extract transactions
        """
        # Read file
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        await ws_manager.broadcast_upload_progress(
            user_id, upload_id, 30, "processing", f"Read {len(df)} records..."
        )
        
        row_count = len(df)
        
        await ws_manager.broadcast_upload_progress(
            user_id, upload_id, 50, "processing", "File parsed successfully..."
        )
        
        # Return the row count - the file is stored locally for later analysis
        return row_count
    
    async def _run_auto_analysis(
        self,
        file_path: Path,
        file_ext: str,
        upload_id: str,
        user_id: str
    ) -> None:
        """
        Automatically run ML analysis after file upload
        """
        try:
            # Read file
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            else:
                print(f"Cannot analyze file type: {file_ext}")
                return
            
            if df.empty:
                print(f"Empty dataframe for upload {upload_id}")
                return
            
            # Run ML analysis
            results = ml_service.analyze_transactions(df)
            
            # Extract metrics
            summary = results.get("summary", {})
            suspicious_addresses = results.get("suspicious_addresses", [])
            patterns = results.get("patterns", [])
            
            # Count suspicious nodes
            suspicious_node_count = len([
                addr for addr in suspicious_addresses 
                if addr.get("suspiciousScore", 0) > 0.5
            ])
            
            # Count smurfing patterns
            smurfing_patterns = len([
                p for p in patterns 
                if "smurf" in p.get("type", "").lower() or 
                   "structur" in p.get("type", "").lower() or
                   "fan" in p.get("type", "").lower()
            ])
            
            # Get max risk score
            max_risk_score = summary.get("maxSuspiciousScore", 0.0)
            if not max_risk_score and suspicious_addresses:
                max_risk_score = max(
                    (addr.get("suspiciousScore", 0) for addr in suspicious_addresses),
                    default=0.0
                )
            
            # Save to analysis_results table
            await supabase_service.save_analysis_results(
                upload_id=upload_id,
                suspicious_node_count=suspicious_node_count,
                smurfing_patterns_detected=smurfing_patterns,
                max_risk_score=max_risk_score
            )
            
            # Save patterns to database
            for pattern in patterns:
                await supabase_service.save_pattern(upload_id, pattern)
            
            # Save suspicious addresses to database
            for address in suspicious_addresses:
                await supabase_service.save_suspicious_address(upload_id, address)
            
            print(f"Auto-analysis complete for upload {upload_id}: {len(patterns)} patterns, {len(suspicious_addresses)} addresses")
            
        except Exception as e:
            print(f"Auto-analysis failed for upload {upload_id}: {e}")
            import traceback
            traceback.print_exc()
    
    async def get_upload_history(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 10,
        status: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get upload history for a user
        """
        uploads, total = await supabase_service.get_uploads_by_user(
            user_id, page, limit, status
        )
        
        return uploads, total
    
    async def get_upload_detail(
        self,
        upload_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Get upload details
        """
        upload = await supabase_service.get_upload_by_id(upload_id)
        
        if upload and upload.get("user_id") == user_id:
            return upload
        
        return None
    
    async def delete_upload(
        self,
        upload_id: str,
        user_id: str
    ) -> bool:
        """
        Delete an upload and its associated data
        """
        upload = await supabase_service.get_upload_by_id(upload_id)
        
        if not upload or upload.get("user_id") != user_id:
            return False
        
        # Delete file
        file_path = Path(upload.get("file_path", ""))
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        await supabase_service.delete_upload(upload_id)
        
        return True


# Global service instance
upload_service = UploadService()
