from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from modules.Auth.dependencies import get_current_admin
from modules.Auth.models import User, UserRole
from modules.sellers.models import StoreStatus

from . import service
from .schemas import (
    AdminDashboardResponse,
    PendingSellerListResponse,
    SellerApprovalAction,
    AdminUserListResponse,
    RecentActivityResponse,
    PlatformStats,
)

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["Admin - Dashboard"])


# ══════════════════════════════════════════════════════════════════════
# FULL DASHBOARD  (single endpoint for frontend to load everything)
# ══════════════════════════════════════════════════════════════════════

@router.get("/", response_model=AdminDashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Full admin dashboard in one call.
    Returns platform stats, pending seller queue, and recent activity.
    Use this to hydrate the admin home page.
    """
    return await service.get_admin_dashboard(db)


# ══════════════════════════════════════════════════════════════════════
# STATS  (individual endpoints for refreshing specific sections)
# ══════════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=PlatformStats)
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Platform-wide statistics only.
    Useful for polling/refreshing the stats cards without reloading
    the full dashboard.
    """
    from .service import (
        _get_user_stats, _get_seller_stats,
        _get_product_stats, _now,
    )
    from .schemas import OrderStats, CommissionStats
    from datetime import datetime

    return PlatformStats(
        users=await _get_user_stats(db),
        sellers=await _get_seller_stats(db),
        products=await _get_product_stats(db),
        orders=OrderStats(),
        commissions=CommissionStats(platform_rate=10.0),
        generated_at=_now(),
    )


# ══════════════════════════════════════════════════════════════════════
# SELLER APPROVAL QUEUE  (the gap you flagged)
# ══════════════════════════════════════════════════════════════════════

@router.get("/sellers/pending", response_model=PendingSellerListResponse)
async def list_pending_sellers(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Paginated queue of sellers awaiting approval — oldest first (FIFO).
    Shows business name, store slug, user email, KYB status, and
    date applied so the admin has everything needed to make a decision.
    """
    return await service.get_pending_sellers(db, page, per_page, search)


@router.post("/sellers/{seller_id}/action")
async def process_seller_approval(
    seller_id: int,
    action_data: SellerApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Approve, reject, or suspend a seller from the dashboard queue.

    - APPROVED  → seller profile approved, StoreCustomization provisioned,
                  user role elevated to SELLER in one atomic action
    - REJECTED  → seller profile rejected, reason stored, user stays CUSTOMER
    - SUSPENDED → seller profile suspended, reason required

    Note: reason is required for REJECTED and SUSPENDED.
    """
    if action_data.action in (StoreStatus.REJECTED, StoreStatus.SUSPENDED):
        if not action_data.reason:
            from core.exceptions import CommerceException
            from fastapi import status as http_status
            raise CommerceException(
                f"A reason is required when {action_data.action.value} a seller.",
                http_status.HTTP_400_BAD_REQUEST,
            )

    return await service.process_seller_approval(
        db,
        seller_id=seller_id,
        action=action_data.action,
        reason=action_data.reason,
        admin_id=current_admin.id,
    )


# ══════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    User list with seller profile status enrichment.
    Customers with a PENDING seller application are clearly visible here
    alongside their seller_status field.
    """
    return await service.get_admin_user_list(
        db, role, is_active, is_verified, search, page, per_page
    )


# ══════════════════════════════════════════════════════════════════════
# RECENT ACTIVITY
# ══════════════════════════════════════════════════════════════════════

@router.get("/activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Real-time platform activity feed.
    Filter by category: admin_action, auth, seller_action, etc.
    """
    return await service.get_recent_activity(db, limit, category)


# ══════════════════════════════════════════════════════════════════════
# COMMISSION SUMMARY  (placeholder until Payments is built)
# ══════════════════════════════════════════════════════════════════════

@router.get("/commissions")
async def get_commission_summary(
    _: User = Depends(get_current_admin),
):
    """
    Commission summary.
    Returns real zeros until the Payments/Commissions module is built
    in Phase 3. The endpoint is live now so the frontend can wire it up
    and it will automatically return real data once the module exists.
    """
    return {
        "total_collected": 0.0,
        "this_month": 0.0,
        "pending_payout": 0.0,
        "platform_rate": 10.0,
        "note": "Live data available after Payments module is built (Phase 3)",
    }