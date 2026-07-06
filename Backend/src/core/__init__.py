"""
Core module - Shared configuration and utilities
"""

from .config import settings
from .database import engine, Base, get_db, AsyncSessionLocal
from .security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from .exceptions import (
    CommerceException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ValidationException
)

__all__ = [
    # Config
    "settings",
    
    # Database
    "engine",
    "Base",
    "get_db",
    "AsyncSessionLocal",
    
    # Security
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    
    # Exceptions
    "CommerceException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "ValidationException",
]