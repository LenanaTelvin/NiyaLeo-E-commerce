from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from core.database import get_db
from core.security import verify_password, get_password_hash
from core.exceptions import NotFoundException
from modules.Auth.dependencies import get_current_user, get_current_admin
from modules.Auth.models import User, UserRole

from . import service
from . import schemas

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ============================================
# PROFILE
# ============================================

@router.get("/me", response_model=schemas.CompleteUserResponse)
async def get_my_complete_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.get_complete_user_data(db, current_user.id)
    return {
        "id":         data["user"].id,
        "email":      data["user"].email,
        "username":   data["user"].username,
        "full_name":  data["user"].full_name,
        "role":       data["user"].role,
        "is_active":  data["user"].is_active,
        "is_verified": data["user"].is_verified,
        "created_at": data["user"].created_at,
        "profile":     data["profile"],
        "preferences": data["preferences"],
        "addresses":   data["addresses"],
    }


@router.get("/me/profile", response_model=schemas.UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_user_profile(db, current_user.id)


@router.put("/me/profile", response_model=schemas.UserProfileResponse)
async def update_my_profile(
    update_data: schemas.UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_user_profile(db, current_user.id, update_data)


@router.post("/me/avatar")
async def upload_my_avatar(
    avatar_url: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await service.upload_avatar(db, current_user.id, avatar_url)
    return {"message": "Avatar updated", "avatar_url": profile.avatar_url}


# ============================================
# ADDRESSES
# FIX: user_id resolved from auth — never accepted from body
# ============================================

@router.get("/me/addresses", response_model=List[schemas.UserAddressResponse])
async def get_my_addresses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_user_addresses(db, current_user.id)


@router.post("/me/addresses", response_model=schemas.UserAddressResponse, status_code=status.HTTP_201_CREATED)
async def add_my_address(
    address_data: schemas.UserAddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # FIX: user_id passed explicitly — not mutated onto the schema
    return await service.add_user_address(db, current_user.id, address_data)


@router.put("/me/addresses/{address_id}", response_model=schemas.UserAddressResponse)
async def update_my_address(
    address_id: int,
    update_data: schemas.UserAddressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_user_address(db, address_id, current_user.id, update_data)


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_user_address(db, address_id, current_user.id)


# ============================================
# PREFERENCES
# ============================================

@router.get("/me/preferences", response_model=schemas.UserPreferenceResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_user_preferences(db, current_user.id)


@router.put("/me/preferences", response_model=schemas.UserPreferenceResponse)
async def update_my_preferences(
    update_data: schemas.UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_user_preferences(db, current_user.id, update_data)


# ============================================
# DEVICES
# FIX: user_id resolved from auth — never accepted from body
# ============================================

@router.get("/me/devices", response_model=List[schemas.UserDeviceResponse])
async def get_my_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_user_devices(db, current_user.id)


@router.post("/me/devices/register", response_model=schemas.UserDeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_my_device(
    device_data: schemas.UserDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # FIX: user_id passed explicitly — not mutated onto the schema
    return await service.register_device(db, current_user.id, device_data)


@router.put("/me/devices/{device_id}/trust")
async def trust_device(
    device_id: str,
    is_trusted: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.update_device_trust(db, device_id, current_user.id, is_trusted)
    return {"message": f"Device trust updated to {is_trusted}"}


@router.delete("/me/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_my_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.revoke_device(db, device_id, current_user.id)


# ============================================
# ACTIVITY
# FIX: user_id resolved from auth — never accepted from body
# ============================================

@router.get("/me/activity", response_model=List[schemas.UserActivityLogResponse])
async def get_my_activity(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    activity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_user_activity(
        db, current_user.id, limit, offset, activity_type
    )


@router.post("/me/activity/log", status_code=status.HTTP_201_CREATED)
async def log_my_activity(
    activity_data: schemas.UserActivityLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # FIX: user_id passed explicitly — not mutated onto the schema
    await service.log_user_activity(db, current_user.id, activity_data)
    return {"message": "Activity logged"}


# ============================================
# PASSWORD MANAGEMENT
# ============================================

@router.post("/password/request-reset")
async def request_password_reset(
    request_data: schemas.PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(
        select(User).where(User.email == request_data.email)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        # Always return the same message — don't leak whether email exists
        return {"message": "If your email is registered, you will receive a reset link"}

    await service.create_password_reset_token(db, user)
    # TODO: await email_service.send_password_reset_email(user.email, token)
    return {"message": "Password reset link sent to your email"}


@router.post("/password/reset")
async def reset_password(
    request_data: schemas.PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    await service.reset_password(db, request_data.token, request_data.new_password)
    return {"message": "Password reset successfully"}


@router.post("/password/change")
async def change_password(
    request_data: schemas.ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(request_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = get_password_hash(request_data.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


# ============================================
# EMAIL VERIFICATION
# ============================================

@router.post("/email/verify-request")
async def request_email_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.is_verified:
        return {"message": "Email is already verified"}
    await service.create_email_verification_token(db, current_user)
    # TODO: await email_service.send_verification_email(current_user.email, token)
    return {"message": "Verification email sent"}


@router.post("/email/verify")
async def verify_email(
    request_data: schemas.EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    await service.verify_email(db, request_data.token)
    return {"message": "Email verified successfully"}


@router.post("/email/update")
async def update_email(
    request_data: schemas.UserEmailUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(request_data.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect",
        )

    existing = await db.execute(
        select(User).where(User.email == request_data.new_email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already taken",
        )

    current_user.email = request_data.new_email
    current_user.is_verified = False
    await db.commit()

    await service.create_email_verification_token(db, current_user)
    # TODO: await email_service.send_verification_email(current_user.email, token)
    return {"message": "Email updated. Please verify your new email."}


# ============================================
# ADMIN — ROLE MANAGEMENT
# ============================================

@router.patch("/admin/{user_id}/role", tags=["Admin - Users"])
async def update_user_role(
    user_id: int,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Admin-only — elevate or demote a user's role."""
    user = await service.update_user_role(db, user_id, role)
    return {"message": f"User {user_id} role updated to {role.value}"}