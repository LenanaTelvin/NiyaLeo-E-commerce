from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib

from .models import (
    UserProfile, UserAddress, UserPreference,
    UserDevice, UserActivityLog, PasswordResetToken,
    EmailVerificationToken,
)
from .schemas import (
    UserProfileCreate, UserProfileUpdate,
    UserAddressCreate, UserAddressUpdate,
    UserPreferenceCreate, UserPreferenceUpdate,
    UserDeviceCreate, UserDeviceUpdate,
    UserActivityLogCreate,
)
from modules.Auth.models import User, UserRole
from core.exceptions import CommerceException, NotFoundException, ValidationException
from core.security import get_password_hash
from fastapi import status


# ============================================
# USER PROFILE SERVICE
# ============================================

async def get_user_profile(db: AsyncSession, user_id: int) -> UserProfile:
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # Auto-provision on first access — no separate create step needed
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile


async def update_user_profile(
    db: AsyncSession,
    user_id: int,
    update_data: UserProfileUpdate,
) -> UserProfile:
    profile = await get_user_profile(db, user_id)

    for field, value in update_data.model_dump(exclude_unset=True, mode="json").items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(profile)
    return profile


async def upload_avatar(
    db: AsyncSession,
    user_id: int,
    avatar_url: str,
    public_id: Optional[str] = None,
) -> UserProfile:
    profile = await get_user_profile(db, user_id)
    profile.avatar_url = avatar_url
    profile.avatar_public_id = public_id
    profile.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(profile)
    return profile


# ============================================
# USER ADDRESS SERVICE
# FIX: user_id now an explicit arg — not from schema body
# ============================================

async def add_user_address(
    db: AsyncSession,
    user_id: int,                   # FIX: explicit, not from schema
    address_data: UserAddressCreate,
) -> UserAddress:
    if address_data.is_default:
        await db.execute(
            UserAddress.__table__.update()
            .where(and_(
                UserAddress.user_id == user_id,
                UserAddress.is_default == True,
            ))
            .values(is_default=False)
        )

    address = UserAddress(user_id=user_id, **address_data.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


async def get_user_addresses(db: AsyncSession, user_id: int) -> List[UserAddress]:
    result = await db.execute(
        select(UserAddress)
        .where(UserAddress.user_id == user_id)
        .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
    )
    return list(result.scalars().all())


async def get_user_address(
    db: AsyncSession, address_id: int, user_id: int
) -> UserAddress:
    result = await db.execute(
        select(UserAddress).where(and_(
            UserAddress.id == address_id,
            UserAddress.user_id == user_id,
        ))
    )
    address = result.scalar_one_or_none()
    if not address:
        raise NotFoundException("Address not found")
    return address


async def update_user_address(
    db: AsyncSession,
    address_id: int,
    user_id: int,
    update_data: UserAddressUpdate,
) -> UserAddress:
    address = await get_user_address(db, address_id, user_id)

    if update_data.is_default:
        await db.execute(
            UserAddress.__table__.update()
            .where(and_(
                UserAddress.user_id == user_id,
                UserAddress.is_default == True,
            ))
            .values(is_default=False)
        )

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(address, field, value)

    address.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(address)
    return address


async def delete_user_address(
    db: AsyncSession, address_id: int, user_id: int
) -> bool:
    address = await get_user_address(db, address_id, user_id)
    await db.delete(address)
    await db.commit()
    return True


async def get_default_address(
    db: AsyncSession, user_id: int
) -> Optional[UserAddress]:
    result = await db.execute(
        select(UserAddress).where(and_(
            UserAddress.user_id == user_id,
            UserAddress.is_default == True,
        ))
    )
    return result.scalar_one_or_none()


# ============================================
# USER PREFERENCES SERVICE
# ============================================

async def get_user_preferences(db: AsyncSession, user_id: int) -> UserPreference:
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    preferences = result.scalar_one_or_none()

    if not preferences:
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)

    return preferences


async def update_user_preferences(
    db: AsyncSession,
    user_id: int,
    update_data: UserPreferenceUpdate,
) -> UserPreference:
    preferences = await get_user_preferences(db, user_id)

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(preferences, field, value)

    preferences.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(preferences)
    return preferences


# ============================================
# USER DEVICE SERVICE
# FIX: user_id now an explicit arg — not from schema body
# ============================================

async def register_device(
    db: AsyncSession,
    user_id: int,                   # FIX: explicit, not from schema
    device_data: UserDeviceCreate,
) -> UserDevice:
    existing = await db.execute(
        select(UserDevice).where(and_(
            UserDevice.user_id == user_id,
            UserDevice.device_id == device_data.device_id,
        ))
    )
    device = existing.scalar_one_or_none()

    if device:
        device.last_login = datetime.utcnow()
        device.last_ip = device_data.ip_address
        device.device_name = device_data.device_name or device.device_name
        await db.commit()
        await db.refresh(device)
        return device

    new_device = UserDevice(
        user_id=user_id,
        **device_data.model_dump(exclude={"ip_address"}),
    )
    new_device.last_login = datetime.utcnow()
    new_device.last_ip = device_data.ip_address
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    return new_device


async def get_user_devices(db: AsyncSession, user_id: int) -> List[UserDevice]:
    result = await db.execute(
        select(UserDevice)
        .where(UserDevice.user_id == user_id)
        .order_by(UserDevice.last_login.desc())
    )
    return list(result.scalars().all())


async def update_device_trust(
    db: AsyncSession, device_id: str, user_id: int, is_trusted: bool
) -> UserDevice:
    result = await db.execute(
        select(UserDevice).where(and_(
            UserDevice.device_id == device_id,
            UserDevice.user_id == user_id,
        ))
    )
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundException("Device not found")

    device.is_trusted = is_trusted
    device.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(device)
    return device


async def revoke_device(
    db: AsyncSession, device_id: str, user_id: int
) -> bool:
    result = await db.execute(
        select(UserDevice).where(and_(
            UserDevice.device_id == device_id,
            UserDevice.user_id == user_id,
        ))
    )
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundException("Device not found")

    await db.delete(device)
    await db.commit()
    return True


# ============================================
# USER ACTIVITY LOG SERVICE
# FIX: user_id now an explicit arg — not from schema body
# ============================================

async def log_user_activity(
    db: AsyncSession,
    user_id: Optional[int],         # FIX: explicit, None allowed for anonymous
    activity_data: UserActivityLogCreate,
) -> UserActivityLog:
    activity = UserActivityLog(
        user_id=user_id,
        **activity_data.model_dump(),
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


async def get_user_activity(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    activity_type: Optional[str] = None,
) -> List[UserActivityLog]:
    query = (
        select(UserActivityLog)
        .where(UserActivityLog.user_id == user_id)
        .order_by(UserActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if activity_type:
        query = query.where(UserActivityLog.activity_type == activity_type)

    result = await db.execute(query)
    return list(result.scalars().all())


# ============================================
# PASSWORD RESET SERVICE
# ============================================

async def create_password_reset_token(
    db: AsyncSession,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> str:
    await db.execute(
        PasswordResetToken.__table__.update()
        .where(and_(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ))
        .values(used_at=datetime.utcnow())
    )

    token = hashlib.sha256(
        f"{user.id}{user.email}{datetime.utcnow().timestamp()}".encode()
    ).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(reset_token)
    await db.commit()
    return token


async def reset_password(db: AsyncSession, token: str, new_password: str) -> bool:
    result = await db.execute(
        select(PasswordResetToken).where(and_(
            PasswordResetToken.token == token,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.utcnow(),
        ))
    )
    reset_token = result.scalar_one_or_none()
    if not reset_token:
        raise ValidationException("Invalid or expired reset token")

    user_result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    user.hashed_password = get_password_hash(new_password)
    reset_token.used_at = datetime.utcnow()
    await db.commit()
    return True


# ============================================
# EMAIL VERIFICATION SERVICE
# ============================================

async def create_email_verification_token(db: AsyncSession, user: User) -> str:
    await db.execute(
        EmailVerificationToken.__table__.update()
        .where(and_(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.verified_at.is_(None),
        ))
        .values(verified_at=datetime.utcnow())
    )

    token = hashlib.sha256(
        f"{user.id}{user.email}{datetime.utcnow().timestamp()}".encode()
    ).hexdigest()

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token=token,
        email=user.email,
        expires_at=datetime.utcnow() + timedelta(days=3),
    )
    db.add(verification_token)
    await db.commit()
    return token


async def verify_email(db: AsyncSession, token: str) -> bool:
    result = await db.execute(
        select(EmailVerificationToken).where(and_(
            EmailVerificationToken.token == token,
            EmailVerificationToken.verified_at.is_(None),
            EmailVerificationToken.expires_at > datetime.utcnow(),
        ))
    )
    verification_token = result.scalar_one_or_none()
    if not verification_token:
        raise ValidationException("Invalid or expired verification token")

    user_result = await db.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    user.is_verified = True
    verification_token.verified_at = datetime.utcnow()
    await db.commit()
    return True


# ============================================
# COMPLETE USER DATA
# ============================================

async def get_complete_user_data(
    db: AsyncSession, user_id: int
) -> Dict[str, Any]:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    profile     = await get_user_profile(db, user_id)
    preferences = await get_user_preferences(db, user_id)
    addresses   = await get_user_addresses(db, user_id)

    return {
        "user": user,
        "profile": profile,
        "preferences": preferences,
        "addresses": addresses,
    }


# ============================================
# ADMIN: ROLE MANAGEMENT
# ============================================

async def update_user_role(
    db: AsyncSession, user_id: int, role: UserRole
) -> User:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    user.role = role
    await db.commit()
    await db.refresh(user)
    return user