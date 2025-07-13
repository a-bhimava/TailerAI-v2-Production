"""
Google OAuth service for TailerAI v2.0
Handles Google Sign-In authentication
"""

import logging
from typing import Optional, Dict, Any
import httpx
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError

from app.config.settings import get_settings
from app.models.database import User
from app.services.database_service import db_service
from app.services.auth_service import auth_service, AuthenticationError

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    """Google OAuth authentication service."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client_id = self.settings.google_client_id
        self.client_secret = self.settings.google_client_secret
        
    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Google ID token and return user info.
        """
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            # Check issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise GoogleAuthError('Wrong issuer.')
            
            # Validate required fields
            if not idinfo.get('email') or not idinfo.get('sub'):
                raise GoogleAuthError('Missing required user information')
            
            logger.info(f"Successfully verified Google token for user: {idinfo.get('email')}")
            return idinfo
            
        except GoogleAuthError as e:
            logger.error(f"Google token verification failed: {str(e)}")
            raise AuthenticationError(f"Invalid Google token: {str(e)}")
        except ValueError as e:
            logger.error(f"Google token format error: {str(e)}")
            raise AuthenticationError("Invalid token format")
        except Exception as e:
            logger.error(f"Unexpected error during Google token verification: {str(e)}")
            raise AuthenticationError("Google authentication failed")
    
    async def authenticate_with_google(self, google_token: str) -> tuple[User, str, str]:
        """
        Authenticate user with Google token.
        Creates user if doesn't exist, then returns (user, access_token, refresh_token).
        """
        try:
            # Verify Google token and get user info
            google_user_info = await self.verify_google_token(google_token)
            
            email = google_user_info.get('email')
            name = google_user_info.get('name', '')
            google_id = google_user_info.get('sub')
            
            if not email or not google_id:
                raise AuthenticationError("Invalid Google user information")
            
            # Check if user exists
            with db_service.get_session() as session:
                user = session.query(User).filter_by(email=email.lower()).first()
                
                if not user:
                    # Create new user from Google info
                    user_id, user_email = await self._create_user_from_google(
                        email=email,
                        name=name,
                        google_id=google_id,
                        session=session
                    )
                    logger.info(f"Created new user from Google OAuth: {email}")
                else:
                    # Update existing user's Google ID if not set
                    if not hasattr(user, 'google_id') or not user.google_id:
                        user.google_id = google_id
                        logger.info(f"Added Google ID to existing user: {email}")
                    
                    # Update last login and profile name if needed
                    from datetime import datetime
                    user.last_login = datetime.utcnow()
                    
                    # Update user profile with Google name if available and not set
                    from app.models.database import UserProfile
                    profile = session.query(UserProfile).filter_by(user_id=user.id).first()
                    if profile and name and (not profile.full_name or profile.full_name.strip() == ''):
                        profile.full_name = name
                        logger.info(f"Updated profile name for user: {email}")
                    
                    session.commit()
                    
                    # Capture data before closing session
                    user_id = str(user.id)
                    user_email = user.email
                    
                    # Refresh user object to ensure all relationships are loaded
                    session.refresh(user)
                    logger.info(f"Existing user authenticated via Google: {email}")
                
            # Generate tokens with captured data outside session context
            token_data = {"sub": user_id, "email": user_email}
            access_token = auth_service.create_access_token(token_data)
            refresh_token = auth_service.create_refresh_token(token_data)
            
            logger.info(f"User authenticated via Google: {email}")
            
            # Create a simple user object with essential data (not bound to session)
            class SimpleUser:
                def __init__(self, user_id, email):
                    self.id = user_id
                    self.email = email
            
            simple_user = SimpleUser(user_id, user_email)
            return simple_user, access_token, refresh_token
                
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Google authentication: {str(e)}")
            raise AuthenticationError("Google authentication failed")
    
    async def _create_user_from_google(self, email: str, name: str, google_id: str, session) -> User:
        """Create a new user from Google OAuth information."""
        try:
            # Generate username from email - sanitize for validation requirements
            base_username = email.split('@')[0].lower()
            # Replace invalid characters with underscores
            import re
            username = re.sub(r'[^a-z0-9_-]', '_', base_username)
            
            # Ensure username is within length limits (3-30 chars)
            if len(username) < 3:
                username = f"user_{google_id[:8]}"
            elif len(username) > 30:
                username = username[:22] + "_" + google_id[:7]
            
            # Check if username already exists, add suffix if needed
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                # Create unique username with Google ID suffix
                suffix = google_id[:8]
                base_len = 30 - len(suffix) - 1  # Reserve space for underscore and suffix
                username = username[:base_len] + "_" + suffix
            
            # Create user (no password needed for OAuth)
            user = User(
                email=email.lower(),
                username=username,
                hashed_password="",  # Empty for OAuth users
                is_active=True,
                is_verified=True,  # Google accounts are pre-verified
                google_id=google_id
            )
            
            session.add(user)
            session.flush()  # Get the user ID
            
            # Create user profile
            from app.models.database import UserProfile
            profile = UserProfile(
                user_id=user.id,
                full_name=name,
                email=email.lower(),
                is_active=True
            )
            
            session.add(profile)
            session.commit()
            
            # Capture essential data and refresh user
            user_id = str(user.id)
            user_email = user.email
            
            # Refresh user object to ensure all data is loaded
            session.refresh(user)
            
            logger.info(f"Created new user from Google OAuth: {email}")
            return user_id, user_email
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create user from Google OAuth: {str(e)}")
            raise AuthenticationError("Failed to create user account")

# Global service instance
google_oauth_service = GoogleOAuthService()