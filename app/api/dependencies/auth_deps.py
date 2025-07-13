"""
Authentication dependencies for FastAPI.
Provides dependency injection for user authentication and authorization.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from app.models.database import User, UserProfile
from app.services.auth_service import auth_service, AuthenticationError
from app.services.database_service import db_service

logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current authenticated user.
    Raises HTTPException if authentication fails.
    """
    try:
        if not credentials:
            logger.error("No credentials provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        logger.info(f"Auth dependency: Got token {token[:20]}...")
        user = await auth_service.get_current_user(token)
        logger.info(f"Auth dependency: Got user {user.id}")
        
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    Ensures user is active and verified.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    
    return current_user


async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserProfile:
    """
    Dependency to get current user's profile.
    Returns the UserProfile associated with the authenticated user.
    """
    try:
        with db_service.get_session() as session:
            user_profile = session.query(UserProfile).filter_by(
                user_id=current_user.id
            ).first()
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            
            return user_profile
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Optional dependency to get current user.
    Returns None if no valid authentication provided.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        return user
    except AuthenticationError:
        return None
    except Exception as e:
        logger.error(f"Error in optional authentication: {str(e)}")
        return None


def require_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to require superuser permissions.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return current_user


def verify_user_access(user_id: UUID, current_user: User) -> bool:
    """
    Verify that current user can access resources for given user_id.
    Users can only access their own data unless they're superuser.
    """
    if current_user.is_superuser:
        return True
    
    # Get user's profile to compare user_id
    try:
        with db_service.get_session() as session:
            user_profile = session.query(UserProfile).filter_by(
                user_id=current_user.id
            ).first()
            
            if user_profile and str(user_profile.user_id) == str(user_id):
                return True
            
            return False
            
    except Exception as e:
        logger.error(f"Error verifying user access: {str(e)}")
        return False


async def get_user_by_id_or_current(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> UUID:
    """
    Get user ID - either from parameter or current user.
    Validates access permissions.
    """
    if user_id:
        try:
            target_user_id = UUID(user_id)
            
            # Verify access
            if not verify_user_access(target_user_id, current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to user data"
                )
            
            return target_user_id
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
    else:
        # Use current user's ID
        return current_user.id