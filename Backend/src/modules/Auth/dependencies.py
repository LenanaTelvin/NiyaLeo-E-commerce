# Dependencies for authentication and authorization in FastAPI
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from .models import User
from core.database import get_db
from core.security import decode_token

security = HTTPBearer()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    try:
        token = credentials.credentials  # HTTPBearer strips "Bearer " for you
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        user_id = int(payload.get("sub"))
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

async def get_current_seller(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is a seller or admin"""
    if current_user.role not in ["admin", "seller"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return current_user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is admin"""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return current_user