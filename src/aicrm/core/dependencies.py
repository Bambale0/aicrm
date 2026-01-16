"""
Core dependencies for the application
Provides FastAPI dependency injection functions
"""

from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..models.user import User
from ..services.auth import AuthService
from .database import get_async_db, get_db

# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token"""
    return AuthService.create_access_token(data, expires_delta)


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract token from Authorization header"""
    return credentials.credentials


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(get_token_from_header)
) -> User:
    """Get current user from token"""
    user = AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not getattr(current_user, "is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user"""
    user_role = getattr(current_user, "role", None)
    if user_role not in ["admin", "su", "superuser"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current superuser"""
    if (
        not getattr(current_user, "is_superuser", False)
        or getattr(current_user, "role", None) != "superuser"
    ):
        raise HTTPException(status_code=403, detail="Superuser access required")
    return current_user
