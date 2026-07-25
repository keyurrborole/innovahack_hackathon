"""
Authentication Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    LogoutResponse,
    UserResponse
)
from app.services.auth_service import auth_service
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google")
async def google_oauth_redirect():
    """
    Redirect to Google OAuth authorization URL
    """
    client_id = settings.GOOGLE_CLIENT_ID
    # Redirect back to frontend callback page which will handle the code
    redirect_uri = f"{settings.FRONTEND_URL}/cryptoflow/auth/callback"
    
    if not client_id or client_id == "your-google-client-id":
        # Return a mock URL for development
        return {
            "authorization_url": f"{settings.FRONTEND_URL}/cryptoflow/dashboard?code=mock_auth_code"
        }
    
    authorization_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"authorization_url": authorization_url}


@router.get("/google/callback")
async def google_oauth_callback(code: str):
    """
    Handle Google OAuth callback
    
    Exchange authorization code for tokens
    """
    try:
        result = await auth_service.oauth_login(
            code=code,
            provider="google"
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    OAuth login endpoint
    
    Exchange OAuth authorization code for JWT token
    """
    try:
        result = await auth_service.oauth_login(
            code=request.code,
            provider=request.provider
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint
    
    Invalidate the current user's session
    """
    await auth_service.logout(current_user["sub"])
    return LogoutResponse()


@router.options("/logout")
async def logout_options():
    """
    Handle CORS preflight for logout
    """
    return Response(status_code=200)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information (alias for /user)
    """
    user = await auth_service.get_current_user(current_user["sub"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        avatar=user.get("avatar"),
        createdAt=user.get("created_at")
    )


@router.get("/user", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    user = await auth_service.get_current_user(current_user["sub"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        avatar=user.get("avatar"),
        createdAt=user.get("created_at")
    )
