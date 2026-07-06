from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status, Request
from .models import User
from .schemas import UserCreate, UserLogin, TokenResponse
from core.security import get_password_hash, create_access_token, create_refresh_token
from core.exceptions import CommerceException, ValidationException
from . import utils
from .models import UserRole

async def register_user(
    db: AsyncSession, 
    user_data: UserCreate,
    request: Request = None
) -> TokenResponse:
    """Register a new user with validation"""
    
    # Validate email
    utils.validate_email_address(user_data.email)
    normalized_email = utils.normalize_email(user_data.email)
    
    # Validate username
    utils.validate_username(user_data.username)
    normalized_username = utils.normalize_username(user_data.username)
    
    # Validate password strength
    utils.validate_password_strength(user_data.password)
    
    # Check if user exists
    existing_user = await db.execute(
        select(User).where(
            (User.email == normalized_email) | 
            (User.username == normalized_username)
        )
    )
    if existing_user.scalar_one_or_none():
        raise CommerceException("Email or username already registered", status.HTTP_409_CONFLICT)
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    new_user = User(
        email=normalized_email,
        username=normalized_username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=UserRole.CUSTOMER,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate tokens
    access_token = create_access_token({"sub": str(new_user.id), "role": new_user.role})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    # Store refresh token
    new_user.refresh_token = refresh_token
    await db.commit()
    
    # Log registration attempt
    if request:
        ip_address = utils.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        log_entry = utils.log_auth_attempt(
            email=normalized_email,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="Registration successful"
        )
        # In production, send this to a logging service
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "role": new_user.role
        }
    )

async def authenticate_user(
    db: AsyncSession, 
    credentials: UserLogin,
    request: Request = None
) -> TokenResponse:
    """Authenticate user with credentials"""
    
    # Normalize email
    normalized_email = utils.normalize_email(credentials.email)
    
    # Find user
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    
    ip_address = utils.get_client_ip(request) if request else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown") if request else "Unknown"
    
    if not user or not utils.verify_password(credentials.password, user.hashed_password):
        # Log failed attempt
        log_entry = utils.log_auth_attempt(
            email=normalized_email,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="Invalid credentials"
        )
        raise CommerceException("Invalid credentials", status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        log_entry = utils.log_auth_attempt(
            email=normalized_email,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="Account deactivated"
        )
        raise CommerceException("Account is deactivated", status.HTTP_403_FORBIDDEN)
    
    # Log successful login
    log_entry = utils.log_auth_attempt(
        email=normalized_email,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
        reason="Login successful"
    )
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # Store refresh token
    user.refresh_token = refresh_token
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role
        }
    )

async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
    """Refresh access token using refresh token"""
    
    # Validate refresh token
    try:
        payload = utils.decode_token_with_validation(refresh_token, token_type="refresh")
    except ValidationException as e:
        raise CommerceException(str(e), status.HTTP_401_UNAUTHORIZED)
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or user.refresh_token != refresh_token:
        raise CommerceException("Invalid refresh token", status.HTTP_401_UNAUTHORIZED)
    
    # Generate new access token
    new_access_token = create_access_token({"sub": str(user.id), "role": user.role})
    
    return {"access_token": new_access_token, "token_type": "bearer"}

async def logout_user(db: AsyncSession, user: User) -> dict:
    """Logout user by clearing refresh token"""
    user.refresh_token = None
    await db.commit()
    return {"message": "Logged out successfully"}

async def change_password(
    db: AsyncSession, 
    user: User, 
    current_password: str, 
    new_password: str
) -> dict:
    """Change user password"""
    
    # Verify current password
    if not utils.verify_password(current_password, user.hashed_password):
        raise CommerceException("Current password is incorrect", status.HTTP_401_UNAUTHORIZED)
    
    # Validate new password strength
    utils.validate_password_strength(new_password)
    
    # Hash and update new password
    user.hashed_password = get_password_hash(new_password)
    # Invalidate refresh token
    user.refresh_token = None
    await db.commit()
    
    return {"message": "Password changed successfully"}