from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from modules.Auth.models import User, UserRole
from modules.sellers.models import SellerProfile, StoreStatus
from modules.products.models import Product, ProductStatus
from modules.users.models import UserActivityLog
from core.exceptions import NotFoundException, CommerceException
from fastapi import status as http_status

from .schemas import (
    UserStats, SellerStats, ProductStats,
    OrderStats, CommissionStats, PlatformStats,
    PendingSellerItem, PendingSellerListResponse,
    AdminUserItem, AdminUserListResponse,
    ActivityItem, RecentActivityResponse,
    AdminDashboardResponse,
)


# ============================================
# HELPERS
# ============================================

def _now() -> datetime:
    return datetime.utcnow()

def _start_of_day() -> datetime:
    n = _now()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)

def _start_of_week() -> datetime:
    n = _now()
    return (n - timedelta(days=n.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

def _start_of_month() -> datetime:
    n = _now()
    return n.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# ============================================
# STATS QUERIES
# ============================================

async def _get_user_stats(db: AsyncSession) -> UserStats:
    # Total counts
    total_result  = await db.execute(select(func.count()).select_from(User))
    total         = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count()).where(User.is_active == True)
    )
    active = active_result.scalar() or 0

    verified_result = await db.execute(
        select(func.count()).where(User.is_verified == True)
    )
    verified = verified_result.scalar() or 0

    # New users time-window counts
    today_result = await db.execute(
        select(func.count()).where(User.created_at >= _start_of_day())
    )
    new_today = today_result.scalar() or 0

    week_result = await db.execute(
        select(func.count()).where(User.created_at >= _start_of_week())
    )
    new_this_week = week_result.scalar() or 0

    month_result = await db.execute(
        select(func.count()).where(User.created_at >= _start_of_month())
    )
    new_this_month = month_result.scalar() or 0

    # By role breakdown
    role_result = await db.execute(
        select(User.role, func.count().label("cnt"))
        .group_by(User.role)
    )
    by_role = {row.role.value: row.cnt for row in role_result.all()}

    return UserStats(
        total=total,
        active=active,
        inactive=total - active,
        verified=verified,
        new_today=new_today,
        new_this_week=new_this_week,
        new_this_month=new_this_month,
        by_role=by_role,
    )


async def _get_seller_stats(db: AsyncSession) -> SellerStats:
    total_result = await db.execute(
        select(func.count()).select_from(SellerProfile)
    )
    total = total_result.scalar() or 0

    # Count by status in one query
    status_result = await db.execute(
        select(SellerProfile.status, func.count().label("cnt"))
        .group_by(SellerProfile.status)
    )
    by_status = {row.status.value: row.cnt for row in status_result.all()}

    week_result = await db.execute(
        select(func.count()).where(
            SellerProfile.created_at >= _start_of_week()
        )
    )
    new_this_week = week_result.scalar() or 0

    return SellerStats(
        total=total,
        pending=by_status.get("pending", 0),
        approved=by_status.get("approved", 0),
        suspended=by_status.get("suspended", 0),
        rejected=by_status.get("rejected", 0),
        closed=by_status.get("closed", 0),
        new_this_week=new_this_week,
    )


async def _get_product_stats(db: AsyncSession) -> ProductStats:
    total_result = await db.execute(
        select(func.count()).select_from(Product)
    )
    total = total_result.scalar() or 0

    status_result = await db.execute(
        select(Product.status, func.count().label("cnt"))
        .group_by(Product.status)
    )
    by_status = {row.status.value: row.cnt for row in status_result.all()}

    # Low stock: track_inventory=True and stock <= threshold
    low_stock_result = await db.execute(
        select(func.count()).where(
            and_(
                Product.track_inventory == True,
                Product.stock_quantity <= Product.low_stock_threshold,
                Product.status == ProductStatus.ACTIVE,
            )
        )
    )
    low_stock = low_stock_result.scalar() or 0

    return ProductStats(
        total=total,
        active=by_status.get("active", 0),
        draft=by_status.get("draft", 0),
        out_of_stock=by_status.get("out_of_stock", 0),
        archived=by_status.get("archived", 0),
        low_stock=low_stock,
    )


# ============================================
# PENDING SELLER QUEUE  (the gap you flagged)
# ============================================

async def get_pending_sellers(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
) -> PendingSellerListResponse:
    """
    Returns all seller profiles with status=PENDING, joined with
    their user's email and username so the admin can see who applied.
    This is what was missing — admins had no way to see the queue.
    """
    query = (
        select(SellerProfile)
        .where(SellerProfile.status == StoreStatus.PENDING)
        .options(selectinload(SellerProfile.user))
        .order_by(SellerProfile.created_at.asc())   # oldest first — FIFO queue
    )

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                SellerProfile.business_name.ilike(term),
                SellerProfile.store_name.ilike(term),
                SellerProfile.store_slug.ilike(term),
            )
        )

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    sellers = result.scalars().all()

    items = [
        PendingSellerItem(
            id=s.id,
            user_id=s.user_id,
            business_name=s.business_name,
            business_type=s.business_type.value,
            store_name=s.store_name,
            store_slug=s.store_slug,
            phone_number=s.phone_number,
            city=s.city,
            country=s.country,
            is_verified=s.is_verified,
            kyb_status=s.kyb_status,
            created_at=s.created_at,
            user_email=s.user.email if s.user else None,
            user_username=s.user.username if s.user else None,
        )
        for s in sellers
    ]

    return PendingSellerListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


async def process_seller_approval(
    db: AsyncSession,
    seller_id: int,
    action: StoreStatus,
    reason: Optional[str],
    admin_id: int,
) -> Dict[str, Any]:
    """
    Approve, reject, or suspend a pending seller from the dashboard queue.
    Wires into the existing sellers/service.update_seller_status so
    StoreCustomization provisioning fires on APPROVED — no duplication.
    """
    from modules.sellers import service as sellers_service

    if action == StoreStatus.APPROVED:
        # Also elevate the user's role to SELLER
        seller_result = await db.execute(
            select(SellerProfile).where(SellerProfile.id == seller_id)
        )
        seller = seller_result.scalar_one_or_none()
        if not seller:
            raise NotFoundException("Seller profile not found")

        await sellers_service.update_seller_status(db, seller_id, action, reason)

        user_result = await db.execute(
            select(User).where(User.id == seller.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.role = UserRole.SELLER
            await db.commit()

        return {
            "message": f"Seller {seller_id} approved and role elevated to SELLER",
            "seller_id": seller_id,
            "status": action.value,
        }
    else:
        await sellers_service.update_seller_status(db, seller_id, action, reason)
        return {
            "message": f"Seller {seller_id} status updated to {action.value}",
            "seller_id": seller_id,
            "status": action.value,
            "reason": reason,
        }


# ============================================
# USER MANAGEMENT
# ============================================

async def get_admin_user_list(
    db: AsyncSession,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> AdminUserListResponse:
    """
    User list enriched with seller profile status so admin can see
    which customers have pending seller applications at a glance.
    """
    query = select(User).options(selectinload(User.seller_profile))
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
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    items = [
        AdminUserItem(
            id=u.id,
            email=u.email,
            username=u.username,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            is_verified=u.is_verified,
            created_at=u.created_at,
            has_seller_profile=u.seller_profile is not None,
            seller_status=(
                u.seller_profile.status.value
                if u.seller_profile else None
            ),
        )
        for u in users
    ]

    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


# ============================================
# RECENT ACTIVITY
# ============================================

async def get_recent_activity(
    db: AsyncSession,
    limit: int = 20,
    category: Optional[str] = None,
) -> RecentActivityResponse:
    """
    Platform-wide activity feed — all user actions across all modules,
    joined with username for display.
    """
    query = (
        select(UserActivityLog)
        .options(selectinload(UserActivityLog.user))
        .order_by(UserActivityLog.created_at.desc())
        .limit(limit)
    )
    if category:
        query = query.where(UserActivityLog.activity_category == category)

    result = await db.execute(query)
    logs   = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).select_from(UserActivityLog)
    )
    total = count_result.scalar() or 0

    items = [
        ActivityItem(
            id=log.id,
            user_id=log.user_id,
            username=log.user.username if log.user else None,
            activity_type=log.activity_type,
            activity_category=log.activity_category,
            description=log.description,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return RecentActivityResponse(items=items, total=total)


# ============================================
# FULL DASHBOARD
# ============================================

async def get_admin_dashboard(db: AsyncSession) -> AdminDashboardResponse:
    """
    Single call that assembles the full admin dashboard:
    - Platform stats (users, sellers, products, orders*, commissions*)
    - Pending seller approval queue
    - Recent platform activity

    * Orders and Commissions return real zeros until those modules
      are built — the schema fields are there, they just won't grow
      until Phase 3 is wired in.
    """
    # Run stat queries
    user_stats    = await _get_user_stats(db)
    seller_stats  = await _get_seller_stats(db)
    product_stats = await _get_product_stats(db)
    order_stats   = OrderStats()       # zeros — Orders not built yet
    commission_stats = CommissionStats(
        platform_rate=10.0             # default from settings
    )

    stats = PlatformStats(
        users=user_stats,
        sellers=seller_stats,
        products=product_stats,
        orders=order_stats,
        commissions=commission_stats,
        generated_at=_now(),
    )

    # Pending seller queue (first page, 10 most urgent)
    pending_sellers = await get_pending_sellers(db, page=1, per_page=10)

    # Recent activity (last 20 events)
    recent_activity = await get_recent_activity(db, limit=20)

    return AdminDashboardResponse(
        stats=stats,
        pending_sellers=pending_sellers,
        recent_activity=recent_activity,
        generated_at=_now(),
    )