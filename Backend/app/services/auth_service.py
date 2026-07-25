"""
Authentication Service - OAuth and user management
"""
import httpx
from typing import Optional, Dict
from datetime import datetime

from app.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.core.supabase import supabase_service


class AuthService:
    """
    Service for authentication operations
    """
    
    async def oauth_login(self, code: str, provider: str) -> Dict:
        """
        Handle OAuth login flow
        """
        if provider == "google":
            user_info = await self._google_oauth(code)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Use Google ID as user ID (from user_info)
        google_id = user_info["id"]
        
        # Check if user exists by Google ID first, then by email
        existing_user = await supabase_service.get_user_by_id(google_id)
        
        if not existing_user:
            # Also check by email for backwards compatibility
            existing_user = await supabase_service.get_user_by_email(user_info["email"])
        
        if existing_user:
            user = existing_user
            # Update user info in case name changed
            await supabase_service.update_user(user["id"], {
                "name": user_info["name"]
            })
        else:
            # Create new user with Google ID as the primary key
            user = await supabase_service.create_user({
                "id": google_id,
                "email": user_info["email"],
                "name": user_info["name"],
                "provider": "Google",
                "created_at": datetime.utcnow().isoformat()
            })
        
        if not user:
            raise ValueError("Failed to create or retrieve user")
        
        # Generate tokens
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "name": user.get("name", "")
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Return with field names matching frontend expectations
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "name": user.get("name", ""),
                "email": user["email"],
                "avatar": user.get("avatar")
            }
        }
    
    async def _google_oauth(self, code: str) -> Dict:
        """
        Exchange Google OAuth code for user info
        """
        # The redirect_uri MUST match exactly what was used in the authorization request
        redirect_uri = f"{settings.FRONTEND_URL}/cryptoflow/auth/callback"
        
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                error_detail = token_response.json() if token_response.text else {}
                print(f"Google token exchange failed: {token_response.status_code} - {error_detail}")
                raise ValueError(f"Failed to exchange OAuth code: {error_detail.get('error_description', 'Unknown error')}")
            
            token_data = token_response.json()
            access_token = token_data["access_token"]
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                print(f"Google userinfo failed: {user_response.status_code} - {user_response.text}")
                raise ValueError("Failed to get user info")
            
            user_data = user_response.json()
            
            return {
                "id": user_data["id"],  # Google's unique user ID
                "email": user_data["email"],
                "name": user_data.get("name", user_data["email"].split("@")[0]),
                "avatar": user_data.get("picture")
            }
    
    
    async def get_current_user(self, user_id: str) -> Optional[Dict]:
        """
        Get current user details
        """
        return await supabase_service.get_user_by_id(user_id)
    
    async def logout(self, user_id: str) -> bool:
        """
        Handle user logout (invalidate tokens if needed)
        """
        # Could implement token blacklisting here
        return True


# Global service instance
auth_service = AuthService()
