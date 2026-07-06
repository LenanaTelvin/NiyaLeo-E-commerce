# Router for authentication-related endpoints (registration, login, token refresh)
from fastapi import APIRouter, Depends, HTTPException, status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from . import service
from .schemas import UserCreate, UserLogin, TokenResponse
from modules.Auth.dependencies import get_current_admin
from modules.Auth.dependencies import get_current_user
from modules.Auth.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user (customer/seller)"""
    return await service.register_user(db, user_data, request)

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Login and get access/refresh tokens"""
    return await service.authenticate_user(db, credentials, request)

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_token(
    request_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get new access token using refresh token"""
    return await service.refresh_access_token(db, request_data.refresh_token)

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout — invalidates the refresh token server-side."""
    return await service.logout_user(db, current_user)