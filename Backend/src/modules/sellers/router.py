from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from core.database import get_db
from modules.Auth.dependencies import get_current_admin, get_current_user
from modules.Auth.models import User

from . import service
from . import schemas
from .dependencies import get_seller_for_admin, get_current_seller_profile, get_seller_by_id_or_slug
from .models import StoreStatus, SellerProfile

# ════════════════════════════════════════════════════════════════════
# TWO ROUTERS — register both in main.py
#
# from modules.sellers.router import admin_router, self_router
# app.include_router(admin_router)   # /api/v1/admin/sellers/...
# app.include_router(self_router)    # /api/v1/sellers/...
# ════════════════════════════════════════════════════════════════════

admin_router = APIRouter(prefix="/api/v1/admin/sellers", tags=["Admin - Sellers"])
self_router  = APIRouter(prefix="/api/v1/sellers",       tags=["Sellers - Self Service"])


# ══════════════════════════════════════════════════════════════════════
# ADMIN ROUTER  (unchanged from original — confirmed working)
# ══════════════════════════════════════════════════════════════════════

@admin_router.get("/", response_model=schemas.SellerListResponse)
async def list_all_sellers(
    status: Optional[StoreStatus] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """List all sellers with filters"""
    filters = {
        "status": status,
        "is_active": is_active,
        "is_verified": is_verified,
        "search": search
    }
    return await service.list_sellers(db, filters, page, per_page)


@admin_router.get("/pending", response_model=schemas.SellerListResponse)
async def list_pending_sellers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """List pending seller approvals"""
    filters = {"status": StoreStatus.PENDING}
    return await service.list_sellers(db, filters, page, per_page)


@admin_router.get("/{seller_id}", response_model=schemas.SellerProfileResponse)
async def get_seller(
    seller = Depends(get_seller_for_admin),
    current_admin: User = Depends(get_current_admin)
):
    """Get a specific seller's profile"""
    return seller


@admin_router.put("/{seller_id}/status")
async def update_seller_status(
    seller_id: int,
    status_update: schemas.SellerStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update seller status"""
    updated_seller = await service.update_seller_status(
        db,
        seller_id,
        status_update.status,
        status_update.suspension_reason
    )

    return {
        "message": f"Seller status updated to {status_update.status.value}",
        "seller_id": seller_id,
        "status": status_update.status.value
    }


@admin_router.put("/{seller_id}/commission")
async def update_seller_commission(
    seller_id: int,
    commission_update: schemas.SellerCommissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update custom commission rate"""
    seller = await service.get_seller_profile_by_id(db, seller_id)
    seller.custom_commission_rate = commission_update.custom_commission_rate
    await db.commit()

    return {
        "message": "Commission rate updated",
        "seller_id": seller_id,
        "commission_rate": commission_update.custom_commission_rate
    }


@admin_router.delete("/{seller_id}")
async def delete_seller(
    seller_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Soft delete a seller"""
    await service.delete_seller_profile(db, seller_id)
    return {"message": f"Seller {seller_id} has been closed"}


# ══════════════════════════════════════════════════════════════════════
# SELF-SERVICE ROUTER  ←  this is what was missing
#
# Fixed-path routes (/register, /me, /me/...) are registered BEFORE
# the /{identifier} wildcard at the bottom, so they are never shadowed —
# same ordering rule we applied to stores and products.
# ══════════════════════════════════════════════════════════════════════

@self_router.post(
    "/register",
    response_model=schemas.SellerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_as_seller(
    profile_data: schemas.SellerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a seller application.

    Creates a SellerProfile tied to the current authenticated user with
    status=PENDING. Does NOT change the user's role — an admin must
    review and call POST /api/v1/admin/users/{user_id}/promote-to-seller
    to approve it and elevate the role to SELLER.

    Fails with 409 if this user already has a seller profile, or if the
    requested store_slug is already taken.
    """
    return await service.create_seller_profile(db, current_user.id, profile_data)


@self_router.get("/me", response_model=schemas.SellerProfileResponse)
async def get_my_seller_profile(
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Get the current user's own seller profile and approval status."""
    return seller


@self_router.put("/me", response_model=schemas.SellerProfileResponse)
async def update_my_seller_profile(
    update_data: schemas.SellerProfileUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update your own seller profile."""
    return await service.update_seller_profile(db, seller.id, update_data)


@self_router.get("/me/dashboard", response_model=schemas.SellerDashboardStats)
async def get_my_dashboard(
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard stats for the current seller."""
    return await service.get_seller_dashboard_stats(db, seller.id)


@self_router.get("/me/bank-accounts", response_model=List[schemas.SellerBankAccountResponse])
async def get_my_bank_accounts(
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_bank_accounts(db, seller.id)


@self_router.post(
    "/me/bank-accounts",
    response_model=schemas.SellerBankAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_my_bank_account(
    account_data: schemas.SellerBankAccountCreate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    return await service.add_bank_account(db, seller.id, account_data)


@self_router.put("/me/bank-accounts/{account_id}", response_model=schemas.SellerBankAccountResponse)
async def update_my_bank_account(
    account_id: int,
    update_data: schemas.SellerBankAccountUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_bank_account(db, account_id, seller.id, update_data)


@self_router.delete("/me/bank-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_bank_account(
    account_id: int,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_bank_account(db, account_id, seller.id)


@self_router.get("/{identifier}", response_model=schemas.SellerProfileResponse)
async def get_seller_public(
    identifier: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a seller's public profile by ID or store slug.
    Wildcard — must stay last in this router. Only returns APPROVED,
    active sellers; used for public storefront pages.
    """
    return await get_seller_by_id_or_slug(identifier, db)