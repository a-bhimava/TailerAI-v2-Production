"""
Authentication Service for TailerAI v2.0.
Handles JWT tokens, password hashing, email verification, and security.
Following project blueprint best practices for security and error handling.
"""

import logging
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import get_settings
from app.models.database import User, UserProfile
from app.services.database_service import db_service, DatabaseError

logger = logging.getLogger(__name__)
settings = get_settings()

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT configuration
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720  # 12 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Account lockout configuration
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Email verification configuration
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_HOURS = 1


class AuthenticationError(Exception):
    """Custom exception for authentication operations."""
    pass


class AuthService:
    """
    Service for handling authentication operations.
    Implements secure user registration, login, and token management.
    """
    
    def __init__(self):
        self.logger = logger
        self.pwd_context = pwd_context
    
    # Password Security
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, error_message).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Check for character variety
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password must contain uppercase, lowercase, digit, and special character"
        
        return True, ""
    
    # JWT Token Management
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify JWT token and return payload.
        Raises AuthenticationError if invalid.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                raise AuthenticationError("Invalid token type")
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise AuthenticationError("Token has expired")
            
            return payload
            
        except JWTError as e:
            self.logger.warning(f"JWT verification failed: {str(e)}")
            raise AuthenticationError("Invalid token")
    
    # User Registration
    
    async def register_user(
        self, 
        email: str, 
        username: str, 
        password: str,
        full_name: str
    ) -> User:
        """
        Register new user with email verification.
        Returns User object (unverified).
        """
        try:
            # Validate password strength
            is_valid, error_msg = self.validate_password_strength(password)
            if not is_valid:
                raise AuthenticationError(error_msg)
            
            with db_service.get_session() as session:
                # Check if email already exists
                existing_email = session.query(User).filter_by(email=email.lower()).first()
                if existing_email:
                    raise AuthenticationError("Email already registered")
                
                # Check if username already exists
                existing_username = session.query(User).filter_by(username=username.lower()).first()
                if existing_username:
                    raise AuthenticationError("Username already taken")
                
                # Create user
                hashed_password = self.hash_password(password)
                verification_token = secrets.token_urlsafe(32)
                verification_expires = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
                
                user = User(
                    email=email.lower(),
                    username=username.lower(),
                    hashed_password=hashed_password,
                    email_verification_token=verification_token,
                    email_verification_expires=verification_expires,
                    is_active=False,  # Will be activated after email verification
                    is_verified=False
                )
                
                session.add(user)
                session.flush()  # Get user ID
                
                # Create user profile
                user_profile = UserProfile(
                    user_id=user.id,
                    full_name=full_name,
                    email=email.lower()
                )
                
                session.add(user_profile)
                session.commit()
                session.refresh(user)
                
                # Send verification email (skip in development)
                if settings.environment == "production":
                    await self._send_verification_email(email, verification_token)
                else:
                    # Auto-verify in development
                    user.is_verified = True
                    user.is_active = True
                    user.email_verified_at = datetime.utcnow()
                    user.email_verification_token = None
                    user.email_verification_expires = None
                    session.commit()
                
                # Create a detached copy of the user object with all needed attributes
                user_dict = {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
                    "created_at": user.created_at
                }
                
                self.logger.info(f"User registered: {email}")
                
                # Return a new User object with copied attributes
                detached_user = User()
                for key, value in user_dict.items():
                    setattr(detached_user, key, value)
                
                return detached_user
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during registration: {str(e)}")
            raise AuthenticationError("Registration failed due to database error")
        except Exception as e:
            self.logger.error(f"Unexpected error during registration: {str(e)}")
            raise AuthenticationError("Registration failed")
    
    # User Login
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Authenticate user and return tokens.
        Returns (user, access_token, refresh_token).
        """
        try:
            with db_service.get_session() as session:
                user = session.query(User).filter_by(email=email.lower()).first()
                
                if not user:
                    raise AuthenticationError("Invalid email or password")
                
                # Check if account is locked
                if user.is_locked:
                    raise AuthenticationError(f"Account locked until {user.locked_until}")
                
                # Verify password
                if not self.verify_password(password, user.hashed_password):
                    # Increment failed attempts
                    user.failed_login_attempts += 1
                    
                    # Lock account if too many attempts
                    if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                        self.logger.warning(f"Account locked for user: {email}")
                    
                    session.commit()
                    raise AuthenticationError("Invalid email or password")
                
                # Check if user can login
                if not user.can_login:
                    raise AuthenticationError("Account not verified or inactive")
                
                # Reset failed attempts and update last login
                user.failed_login_attempts = 0
                user.locked_until = None
                user.last_login = datetime.utcnow()
                session.commit()
                
                # Generate tokens
                token_data = {"sub": str(user.id), "email": user.email}
                access_token = self.create_access_token(token_data)
                refresh_token = self.create_refresh_token(token_data)
                
                self.logger.info(f"User authenticated: {email}")
                return user, access_token, refresh_token
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during authentication: {str(e)}")
            raise AuthenticationError("Authentication failed due to database error")
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    # Email Verification
    
    async def verify_email(self, token: str) -> User:
        """Verify email with verification token."""
        try:
            with db_service.get_session() as session:
                user = session.query(User).filter_by(
                    email_verification_token=token
                ).first()
                
                if not user:
                    raise AuthenticationError("Invalid verification token")
                
                # Check if token expired
                if user.email_verification_expires < datetime.utcnow():
                    raise AuthenticationError("Verification token expired")
                
                # Verify email
                user.is_verified = True
                user.is_active = True
                user.email_verified_at = datetime.utcnow()
                user.email_verification_token = None
                user.email_verification_expires = None
                
                session.commit()
                session.refresh(user)
                
                self.logger.info(f"Email verified for user: {user.email}")
                return user
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during email verification: {str(e)}")
            raise AuthenticationError("Email verification failed")
    
    # Password Reset
    
    async def request_password_reset(self, email: str) -> bool:
        """Send password reset email."""
        try:
            with db_service.get_session() as session:
                user = session.query(User).filter_by(email=email.lower()).first()
                
                if not user:
                    # Don't reveal if email exists
                    self.logger.info(f"Password reset requested for non-existent email: {email}")
                    return True
                
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                reset_expires = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
                
                user.password_reset_token = reset_token
                user.password_reset_expires = reset_expires
                
                session.commit()
                
                # Send reset email
                await self._send_password_reset_email(email, reset_token)
                
                self.logger.info(f"Password reset requested for: {email}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error during password reset request: {str(e)}")
            return False
    
    async def reset_password(self, token: str, new_password: str) -> User:
        """Reset password with reset token."""
        try:
            # Validate password strength
            is_valid, error_msg = self.validate_password_strength(new_password)
            if not is_valid:
                raise AuthenticationError(error_msg)
            
            with db_service.get_session() as session:
                user = session.query(User).filter_by(
                    password_reset_token=token
                ).first()
                
                if not user:
                    raise AuthenticationError("Invalid reset token")
                
                # Check if token expired
                if user.password_reset_expires < datetime.utcnow():
                    raise AuthenticationError("Reset token expired")
                
                # Reset password
                user.hashed_password = self.hash_password(new_password)
                user.password_changed_at = datetime.utcnow()
                user.password_reset_token = None
                user.password_reset_expires = None
                user.failed_login_attempts = 0
                user.locked_until = None
                
                session.commit()
                session.refresh(user)
                
                self.logger.info(f"Password reset for user: {user.email}")
                return user
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during password reset: {str(e)}")
            raise AuthenticationError("Password reset failed")
    
    # Token Management
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Generate new access token from refresh token."""
        try:
            payload = self.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            # Verify user still exists and is active
            with db_service.get_session() as session:
                user = session.query(User).filter_by(id=UUID(user_id)).first()
                
                if not user or not user.can_login:
                    raise AuthenticationError("User not found or inactive")
                
                # Generate new access token
                token_data = {"sub": str(user.id), "email": user.email}
                access_token = self.create_access_token(token_data)
                
                return access_token
                
        except Exception as e:
            self.logger.error(f"Error refreshing token: {str(e)}")
            raise AuthenticationError("Token refresh failed")
    
    # User Retrieval
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        try:
            payload = self.verify_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            with db_service.get_session() as session:
                user = session.query(User).filter_by(id=UUID(user_id)).first()
                
                if not user:
                    raise AuthenticationError("User not found")
                
                if not user.can_login:
                    raise AuthenticationError("User account inactive")
                
                # Force load all user attributes and relationships before session closes to avoid DetachedInstanceError
                _ = user.is_active
                _ = user.is_verified
                _ = user.email
                _ = user.username
                _ = user.id
                _ = user.created_at
                _ = user.updated_at
                _ = user.profile  # Load the profile relationship
                
                # Expunge from session to make it independent
                session.expunge(user)
                
                return user
                
        except Exception as e:
            self.logger.error(f"Error getting current user: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    # Email Utilities
    
    async def _send_verification_email(self, email: str, token: str) -> None:
        """Send email verification email."""
        try:
            verification_url = f"{settings.frontend_url}/verify-email?token={token}"
            
            subject = "TailerAI - Verify Your Email Address"
            body = f"""
            Welcome to TailerAI!
            
            Please click the link below to verify your email address:
            {verification_url}
            
            This link will expire in 24 hours.
            
            If you didn't create an account, please ignore this email.
            """
            
            await self._send_email(email, subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send verification email: {str(e)}")
            # Don't raise exception - registration should still succeed
    
    async def _send_password_reset_email(self, email: str, token: str) -> None:
        """Send password reset email."""
        try:
            reset_url = f"{settings.frontend_url}/reset-password?token={token}"
            
            subject = "TailerAI - Password Reset Request"
            body = f"""
            A password reset was requested for your TailerAI account.
            
            Click the link below to reset your password:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you didn't request this reset, please ignore this email.
            """
            
            await self._send_email(email, subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send password reset email: {str(e)}")
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> None:
        """Send email using SMTP."""
        try:
            # Skip email sending in development if not configured
            if settings.environment == "development" and not settings.smtp_host:
                self.logger.info(f"Email would be sent to {to_email}: {subject}")
                return
            
            msg = MIMEMultipart()
            msg['From'] = settings.smtp_from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_tls:
                    server.starttls()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent to {to_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise


# Global service instance
auth_service = AuthService()