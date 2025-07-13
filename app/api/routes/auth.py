"""
Authentication API routes for TailerAI v2.0.
Handles user registration, login, email verification, and password reset.
Following project blueprint best practices for security and error handling.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.services.auth_service import auth_service, AuthenticationError
from app.services.google_oauth_service import google_oauth_service
from app.api.dependencies.auth_deps import get_current_user, get_current_active_user, limiter
from app.models.database import User

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models

class UserRegistration(BaseModel):
    """User registration request model."""
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=30, description="Username")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    
    @validator('email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError("Invalid email format")
        return v.lower()
    
    @validator('username')
    def validate_username(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")
        return v.lower()


class UserLogin(BaseModel):
    """User login request model."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    username: str
    full_name: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class StandardResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[list] = None


class PasswordReset(BaseModel):
    """Password reset request model."""
    email: str = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str = Field(..., description="Refresh token")


class GoogleAuthRequest(BaseModel):
    """Google OAuth request model."""
    google_token: str = Field(..., description="Google ID token", min_length=100, max_length=2000)
    
    @validator('google_token')
    def validate_google_token(cls, v):
        """Validate Google token format"""
        if not v or not isinstance(v, str):
            raise ValueError("Invalid token format")
        
        # Let Google's own verification handle token format validation
        # Just do basic sanity check for JWT-like format
        if '.' not in v or len(v) < 10:
            raise ValueError("Invalid JWT token format")
            
        return v.strip()


# Authentication Routes

@router.post("/register", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegistration):
    """
    Register a new user account.
    Sends email verification upon successful registration.
    """
    try:
        user = await auth_service.register_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return StandardResponse(
            success=True,
            message="Registration successful. Please check your email for verification.",
            data={
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "verification_required": True
            }
        )
        
    except AuthenticationError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, login_data: UserLogin):
    """
    Authenticate user and return JWT tokens.
    """
    try:
        user, access_token, refresh_token = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        logger.info(f"User logged in successfully: {login_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except AuthenticationError as e:
        logger.warning(f"Login failed for {login_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=dict)
@limiter.limit("20/minute")
async def refresh_token(request: Request, token_request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    try:
        access_token = await auth_service.refresh_access_token(
            refresh_token=token_request.refresh_token
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800
        }
        
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.profile.full_name if current_user.profile else "",
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/verify-email", response_model=StandardResponse)
@limiter.limit("10/minute")
async def verify_email(request: Request, token: str):
    """
    Verify user email with verification token.
    """
    try:
        user = await auth_service.verify_email(token)
        
        logger.info(f"Email verified successfully: {user.email}")
        
        return StandardResponse(
            success=True,
            message="Email verified successfully. You can now log in.",
            data={
                "user_id": str(user.id),
                "email": user.email,
                "verified_at": user.email_verified_at.isoformat()
            }
        )
        
    except AuthenticationError as e:
        logger.warning(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/request-password-reset", response_model=StandardResponse)
@limiter.limit("3/minute")
async def request_password_reset(request: Request, reset_request: PasswordReset):
    """
    Request password reset email.
    Always returns success for security (doesn't reveal if email exists).
    """
    try:
        await auth_service.request_password_reset(reset_request.email)
        
        return StandardResponse(
            success=True,
            message="If the email exists, a password reset link has been sent.",
            data={"email": reset_request.email}
        )
        
    except Exception as e:
        logger.error(f"Error during password reset request: {str(e)}")
        # Still return success for security
        return StandardResponse(
            success=True,
            message="If the email exists, a password reset link has been sent.",
            data={"email": reset_request.email}
        )


@router.post("/reset-password", response_model=StandardResponse)
@limiter.limit("5/minute")
async def reset_password(request: Request, reset_data: PasswordResetConfirm):
    """
    Reset password with reset token.
    """
    try:
        user = await auth_service.reset_password(
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        logger.info(f"Password reset successfully: {user.email}")
        
        return StandardResponse(
            success=True,
            message="Password reset successfully. You can now log in with your new password.",
            data={
                "user_id": str(user.id),
                "email": user.email
            }
        )
        
    except AuthenticationError as e:
        logger.warning(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/google", response_model=TokenResponse)
@limiter.limit("10/minute")
async def google_auth(request: Request, auth_data: GoogleAuthRequest):
    """
    Authenticate user with Google OAuth token.
    Creates user account if it doesn't exist.
    
    Security features:
    - Rate limiting (10 requests per minute)
    - JWT token format validation
    - Google token verification
    - Detailed logging for security monitoring
    """
    client_ip = get_remote_address(request)
    
    try:
        # Log authentication attempt for security monitoring
        logger.info(f"Google authentication attempt from IP: {client_ip}")
        
        user, access_token, refresh_token = await google_oauth_service.authenticate_with_google(
            auth_data.google_token
        )
        
        logger.info(f"User authenticated via Google: {user.email} from IP: {client_ip}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except AuthenticationError as e:
        logger.warning(f"Google authentication failed from IP {client_ip}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError as e:
        logger.warning(f"Invalid Google token format from IP {client_ip}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Unexpected error during Google authentication from IP {client_ip}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )


@router.post("/logout", response_model=StandardResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client should discard tokens).
    """
    logger.info(f"User logged out: {current_user.email}")
    
    return StandardResponse(
        success=True,
        message="Logged out successfully",
        data={"user_id": str(current_user.id)}
    )