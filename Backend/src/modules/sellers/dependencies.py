from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from modules.Auth.dependencies import get_current_seller, get_current_admin
from modules.Auth.models import User
from .models import SellerProfile, StoreStatus
from .service import (
    get_seller_profile_by_user_id,
    get_seller_profile_by_id,
    get_seller_profile_by_slug
)
from core.exceptions import NotFoundException


async def get_current_seller_profile(
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db)
) -> SellerProfile:
    """Get seller profile for the current authenticated seller"""
    try:
        seller = await get_seller_profile_by_user_id(db, current_user.id)
        return seller
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found. Please complete your seller registration."
        )


async def get_verified_seller_profile(
    current_seller: SellerProfile = Depends(get_current_seller_profile)
) -> SellerProfile:
    """Get seller profile only if verified and approved"""
    if not current_seller.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not verified. Please complete KYB verification."
        )
    
    if current_seller.status != StoreStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your store is not active. Current status: {current_seller.status.value}"
        )
    
    if not current_seller.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your store has been deactivated. Please contact support."
        )
    
    return current_seller


async def get_seller_by_id_or_slug(
    identifier: str,
    db: AsyncSession = Depends(get_db)
) -> SellerProfile:
    """Get seller by ID (numeric) or slug (string)"""
    try:
        if identifier.isdigit():
            return await get_seller_profile_by_id(db, int(identifier))
        else:
            return await get_seller_profile_by_slug(db, identifier)
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )


async def get_seller_for_admin(
    seller_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> SellerProfile:
    """Get any seller profile for admin operations"""
    try:
        return await get_seller_profile_by_id(db, seller_id, load_relations=True)
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found"
        )