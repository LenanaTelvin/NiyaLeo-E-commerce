from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import Optional

from core.database import get_db
from modules.Auth.dependencies import get_current_admin
from modules.Auth.models import User, UserRole
from modules.sellers.models import SellerProfile, StoreStatus
from core.exceptions import NotFoundException, CommerceException

from . import service
from . import schemas

router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin - Users"])


# ── internal helper ────────────────────────────────────────────────────

async def _get_user_or_404(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    return user


# ══════════════════════════════════════════════════════════════════════
# USER LISTING & DETAIL
# ══════════════════════════════════════════════════════════════════════

@router.get("/")
async def list_all_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List all users with filters."""
    query = select(User)
    conditions = []

    if role is not None:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if is_verified is not None:
        conditions.append(User.is_verified == is_verified)
    if search:
        term = f"%{search}%"
        conditions.append(
            or_(
                User.email.ilike(term),
                User.username.ilike(term),
                User.full_name.ilike(term),
            )
        )

    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    users = result.scalars().all()

    return {
        "items": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/{user_id}/complete")
async def get_user_complete_data(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Get complete user data including profile, addresses, preferences."""
    return await service.get_complete_user_data(db, user_id)


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Get activity logs for any user."""
    return await service.get_user_activity(db, user_id, limit, offset)


# ══════════════════════════════════════════════════════════════════════
# ROLE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Update a user's role directly.
 
    """
    if role == UserRole.SELLER:
        raise CommerceException(
            "Cannot set role=seller directly. Use "
            "POST /api/v1/admin/users/{user_id}/promote-to-seller — "
            "it validates the user has a seller profile before "
            "elevating their role.",
            status.HTTP_400_BAD_REQUEST,
        )
 
    if role == UserRole.CUSTOMER:
        seller_result = await db.execute(
            select(SellerProfile).where(SellerProfile.user_id == user_id)
        )
        seller = seller_result.scalar_one_or_none()
 
        if seller and seller.status == StoreStatus.APPROVED:
            raise CommerceException(
                "Cannot set role=customer directly while the user has an "
                "approved, live store. Use POST /api/v1/admin/users/"
                "{user_id}/demote-to-customer — it suspends the store as "
                "part of the same action, keeping role and store status "
                "in sync.",
                status.HTTP_400_BAD_REQUEST,
            )
 
    updated_user = await service.update_user_role(db, user_id, role)
    await service.log_user_activity(
        db, user_id,
        schemas.UserActivityLogCreate(
            activity_type="role_updated",
            activity_category="admin_action",
            description=f"Role changed to {role.value} by admin {current_admin.id}",
        ),
    )
    return {
        "message": f"User role updated to {role.value}",
        "user_id": user_id,
        "role": role.value,
    }
 

# ══════════════════════════════════════════════════════════════════════
# SELLER PROMOTION  ←  THE MISSING PIECE
# ══════════════════════════════════════════════════════════════════════

@router.post("/{user_id}/promote-to-seller")
async def promote_to_seller(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Promote a customer to seller role.

    This endpoint:
    1. Validates the user exists and is a CUSTOMER
    2. Checks they have an existing seller profile (created during
       registration / KYB) — if not, returns a clear error so the
       admin knows to ask the user to complete seller registration first
    3. Approves the seller profile (triggers StoreCustomization provisioning
       via sellers/service.py update_seller_status)
    4. Elevates the user role to SELLER

    If you want to create the seller profile here too (admin-initiated
    onboarding), wire in sellers/service.create_seller_profile instead.
    """
    user = await _get_user_or_404(db, user_id)

    if user.role == UserRole.ADMIN:
        raise CommerceException(
            "Cannot change role of an admin account",
            status.HTTP_400_BAD_REQUEST,
        )

    if user.role == UserRole.SELLER:
        raise CommerceException(
            "User is already a seller",
            status.HTTP_409_CONFLICT,
        )

    # Check seller profile exists
    seller_result = await db.execute(
        select(SellerProfile).where(SellerProfile.user_id == user_id)
    )
    seller = seller_result.scalar_one_or_none()

    if not seller:
        raise CommerceException(
            "User has no seller profile. Ask them to complete seller "
            "registration at /api/v1/sellers/register before promoting.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Approve the seller profile — this also provisions StoreCustomization
    from modules.sellers import service as sellers_service
    await sellers_service.update_seller_status(
        db, seller.id, StoreStatus.APPROVED
    )

    # Elevate role
    user.role = UserRole.SELLER
    await db.commit()

    # Audit log
    await service.log_user_activity(
        db, user_id,
        schemas.UserActivityLogCreate(
            activity_type="promoted_to_seller",
            activity_category="admin_action",
            description=(
                f"Promoted to seller by admin {current_admin.id}. "
                f"Seller profile {seller.id} approved."
            ),
        ),
    )

    return {
        "message": f"User {user_id} promoted to seller",
        "user_id": user_id,
        "seller_profile_id": seller.id,
        "store_slug": seller.store_slug,
        "status": StoreStatus.APPROVED.value,
    }


@router.post("/{user_id}/demote-to-customer")
async def demote_to_customer(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Demote a seller back to customer and suspend their store.
    Does NOT delete the seller profile or store data.
    """
    user = await _get_user_or_404(db, user_id)

    if user.role != UserRole.SELLER:
        raise CommerceException(
            "User is not a seller",
            status.HTTP_400_BAD_REQUEST,
        )

    seller_result = await db.execute(
        select(SellerProfile).where(SellerProfile.user_id == user_id)
    )
    seller = seller_result.scalar_one_or_none()

    if seller:
        from modules.sellers import service as sellers_service
        await sellers_service.update_seller_status(
            db, seller.id, StoreStatus.SUSPENDED,
            reason=f"Demoted to customer by admin {current_admin.id}"
        )

    user.role = UserRole.CUSTOMER
    await db.commit()

    await service.log_user_activity(
        db, user_id,
        schemas.UserActivityLogCreate(
            activity_type="demoted_to_customer",
            activity_category="admin_action",
            description=f"Demoted to customer by admin {current_admin.id}",
        ),
    )

    return {
        "message": f"User {user_id} demoted to customer and store suspended",
        "user_id": user_id,
    }


# ══════════════════════════════════════════════════════════════════════
# ACCOUNT ACTIVATION / DEACTIVATION
# ══════════════════════════════════════════════════════════════════════

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Activate a deactivated user account."""
    user = await _get_user_or_404(db, user_id)
    user.is_active = True
    await db.commit()

    await service.log_user_activity(
        db, user_id,
        schemas.UserActivityLogCreate(
            activity_type="account_activated",
            activity_category="admin_action",
            description=f"Activated by admin {current_admin.id}",
        ),
    )
    return {"message": f"User {user_id} activated"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Deactivate a user account (soft — preserves all data)."""
    user = await _get_user_or_404(db, user_id)

    if user.id == current_admin.id:
        raise CommerceException(
            "You cannot deactivate your own account",
            status.HTTP_400_BAD_REQUEST,
        )

    user.is_active = False
    await db.commit()

    await service.log_user_activity(
        db, user_id,
        schemas.UserActivityLogCreate(
            activity_type="account_deactivated",
            activity_category="admin_action",
            description=f"Deactivated by admin {current_admin.id}",
        ),
    )
    return {"message": f"User {user_id} deactivated"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Soft-delete a user (deactivate). Hard deletes are not exposed here
    to prevent accidental cascade-deletion of seller stores, products,
    orders, and all related data. For GDPR erasure requests, implement
    a separate explicit endpoint with additional confirmation.
    """
    user = await _get_user_or_404(db, user_id)

    if user.id == current_admin.id:
        raise CommerceException(
            "You cannot delete your own account",
            status.HTTP_400_BAD_REQUEST,
        )

    user.is_active = False
    await db.commit()

    await service.log_user_activity(
        db, user_id,
        schemas.UserActivityLogCreate(
            activity_type="account_deactivated",
            activity_category="admin_action",
            description=f"Soft-deleted by admin {current_admin.id}",
        ),
    )
    return {"message": f"User {user_id} has been deactivated"}