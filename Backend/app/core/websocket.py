"""
WebSocket Manager for real-time updates
"""
from fastapi import WebSocket
from typing import Dict, List, Set, Optional, Any
import json
import asyncio


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        # user_id -> list of connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # connection -> subscribed channels
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept a new WebSocket connection
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.subscriptions[websocket] = set()
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove a WebSocket connection
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
    
    def subscribe(self, websocket: WebSocket, channels: List[str]):
        """
        Subscribe a connection to specific channels
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(channels)
    
    def unsubscribe(self, websocket: WebSocket, channels: List[str]):
        """
        Unsubscribe a connection from specific channels
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket] -= set(channels)
    
    async def send_personal_message(self, message: dict, user_id: str):
        """
        Send a message to all connections of a specific user
        """
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
    
    async def send_to_channel(self, channel: str, message: dict, user_id: str):
        """
        Send a message to subscribed connections of a user on a specific channel
        """
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                if channel in self.subscriptions.get(connection, set()):
                    try:
                        await connection.send_json({
                            "channel": channel,
                            "data": message
                        })
                    except Exception:
                        pass
    
    async def broadcast_upload_progress(
        self, 
        user_id: str, 
        upload_id: str, 
        progress: int, 
        status: str,
        message: Optional[str] = None
    ):
        """Broadcast upload progress to user"""
        await self.send_to_channel(
            "upload-progress",
            {
                "uploadId": upload_id,
                "progress": progress,
                "status": status,
                "message": message
            },
            user_id
        )
    
    async def broadcast_analysis_update(
        self,
        user_id: str,
        upload_id: str,
        status: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Broadcast analysis status update to user"""
        await self.send_to_channel(
            "analysis-updates",
            {
                "uploadId": upload_id,
                "status": status,
                "data": data
            },
            user_id
        )
    
    async def broadcast_report_status(
        self,
        user_id: str,
        report_id: str,
        status: str,
        download_url: Optional[str] = None
    ):
        """Broadcast report status update to user"""
        await self.send_to_channel(
            "report-status",
            {
                "reportId": report_id,
                "status": status,
                "downloadUrl": download_url
            },
            user_id
        )


# Global connection manager instance
ws_manager = ConnectionManager()
