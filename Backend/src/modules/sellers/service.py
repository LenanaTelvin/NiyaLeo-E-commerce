from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import status as http_status
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import (
    SellerProfile, SellerBankAccount,
    StoreStatus, BusinessType
)
from .schemas import (
    SellerProfileCreate, SellerProfileUpdate,
    SellerBankAccountCreate, SellerBankAccountUpdate,
    SellerDashboardStats
)
from modules.Auth.models import User, UserRole
from core.exceptions import CommerceException, NotFoundException


# ============================================
# SELLER PROFILE SERVICE
# ============================================

async def create_seller_profile(
    db: AsyncSession,
    user_id: int,
    profile_data: SellerProfileCreate
) -> SellerProfile:
    """
    Create a new seller profile.

    NOTE: this no longer creates a StoreSetting row (removed — see models.py).
    StoreCustomization is provisioned later, in update_seller_status, once the
    seller is actually APPROVED — not here at signup. A pending/unreviewed
    seller has no need for a live, publicly-renderable storefront yet.
    """
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    
    existing_profile = await db.execute(
        select(SellerProfile).where(SellerProfile.user_id == user_id)
    )
    if existing_profile.scalar_one_or_none():
        raise CommerceException("User already has a seller profile", http_status.HTTP_409_CONFLICT)
    
    slug_exists = await db.execute(
        select(SellerProfile).where(SellerProfile.store_slug == profile_data.store_slug)
    )
    if slug_exists.scalar_one_or_none():
        raise CommerceException("Store slug is already taken", http_status.HTTP_409_CONFLICT)
    
    # FIX: model_dump(mode="json") so HttpUrl fields (store_logo_url,
    # store_banner_url) serialize to plain str before hitting SQLAlchemy's
    # String columns — passing the HttpUrl object directly is the same
    # latent bug we fixed in modules/stores/service.py.
    seller_profile = SellerProfile(
        user_id=user_id,
        **profile_data.model_dump(mode="json")
    )
    
    db.add(seller_profile)
    
    
    await db.commit()
    await db.refresh(seller_profile)
    
    return seller_profile


async def get_seller_profile_by_id(
    db: AsyncSession,
    seller_id: int,
    load_relations: bool = False
) -> SellerProfile:
    """Get seller profile by ID"""
    query = select(SellerProfile).where(SellerProfile.id == seller_id)
    
    if load_relations:
        query = query.options(
            selectinload(SellerProfile.user),
            selectinload(SellerProfile.store_customization),
            selectinload(SellerProfile.bank_accounts)
        )
    
    result = await db.execute(query)
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise NotFoundException("Seller profile not found")
    
    return seller


async def get_seller_profile_by_user_id(
    db: AsyncSession,
    user_id: int
) -> SellerProfile:
    """Get seller profile by user ID"""
    result = await db.execute(
        select(SellerProfile)
        .where(SellerProfile.user_id == user_id)
        .options(
            selectinload(SellerProfile.store_customization),
            selectinload(SellerProfile.bank_accounts)
        )
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise NotFoundException("Seller profile not found for this user")
    
    return seller


async def get_seller_profile_by_slug(
    db: AsyncSession,
    slug: str
) -> SellerProfile:
    """Get seller profile by store slug (public facing)"""
    result = await db.execute(
        select(SellerProfile)
        .where(
            and_(
                SellerProfile.store_slug == slug,
                SellerProfile.status == StoreStatus.APPROVED,
                SellerProfile.is_active == True
            )
        )
        .options(
            selectinload(SellerProfile.store_customization),
            selectinload(SellerProfile.user)
        )
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise NotFoundException("Store not found")
    
    return seller


async def update_seller_profile(
    db: AsyncSession,
    seller_id: int,
    update_data: SellerProfileUpdate
) -> SellerProfile:
    """Update seller profile"""
    seller = await get_seller_profile_by_id(db, seller_id)
    
    update_dict = update_data.model_dump(exclude_unset=True, mode="json")

    if "store_slug" in update_dict and update_dict["store_slug"] != seller.store_slug:
        slug_exists = await db.execute(
            select(SellerProfile).where(
                and_(
                    SellerProfile.store_slug == update_dict["store_slug"],
                    SellerProfile.id != seller_id
                )
            )
        )
        if slug_exists.scalar_one_or_none():
            raise CommerceException("Store slug is already taken", http_status.HTTP_409_CONFLICT)
    
    for field, value in update_dict.items():
        setattr(seller, field, value)
    
    seller.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(seller)
    
    return seller


async def update_seller_status(
    db: AsyncSession,
    seller_id: int,
    status: StoreStatus,
    reason: Optional[str] = None
) -> SellerProfile:
    """
    Update seller status (admin only).

    FIX: this is now where StoreCustomization gets provisioned — the moment
    a seller transitions to APPROVED. Guarded against the double-fire /
    race-condition case (e.g. a retried approval call) by catching the
    409 CommerceException that create_store_customization raises if a
    customization row already exists, and treating it as a no-op rather
    than letting it bubble up and fail the approval itself.
    """
    seller = await get_seller_profile_by_id(db, seller_id)

    was_already_approved = seller.status == StoreStatus.APPROVED
    seller.status = status
    
    if status == StoreStatus.APPROVED:
        seller.approved_at = datetime.utcnow()
        seller.suspension_reason = None
    elif status in [StoreStatus.SUSPENDED, StoreStatus.REJECTED]:
        seller.suspension_reason = reason
        seller.suspended_at = datetime.utcnow()
    elif status == StoreStatus.CLOSED:
        seller.is_active = False
    
    seller.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(seller)

    if status == StoreStatus.APPROVED and not was_already_approved:
        # Local import to avoid a hard import-time coupling between the two
        # modules — only needed on this specific transition.
        from modules.stores import service as stores_service

        try:
            await stores_service.create_store_customization(
                db,
                # StoreCustomizationCreate only requires seller_id; every
                # themed field is Optional[None], so the default theme
                # template fills everything in (see stores/service.py).
                __import__("modules.stores.schemas", fromlist=["StoreCustomizationCreate"]).StoreCustomizationCreate(
                    seller_id=seller.id
                )
            )
        except CommerceException as exc:
            if exc.status_code != http_status.HTTP_409_CONFLICT:
                raise
            # Already provisioned (e.g. duplicate/retried approval call) — fine, no-op.
    
    return seller


async def delete_seller_profile(
    db: AsyncSession,
    seller_id: int
) -> bool:
    """Soft delete seller profile"""
    seller = await get_seller_profile_by_id(db, seller_id)
    seller.status = StoreStatus.CLOSED
    seller.is_active = False
    seller.updated_at = datetime.utcnow()
    
    await db.commit()
    return True


# ============================================
# BANK ACCOUNT SERVICE
# ============================================

async def add_bank_account(
    db: AsyncSession,
    seller_id: int,
    account_data: SellerBankAccountCreate
) -> SellerBankAccount:
    """Add a bank account for seller payouts"""
    await get_seller_profile_by_id(db, seller_id)
    
    if account_data.is_default:
        await db.execute(
            SellerBankAccount.__table__.update()
            .where(SellerBankAccount.seller_id == seller_id)
            .values(is_default=False)
        )
    
    bank_account = SellerBankAccount(
        seller_id=seller_id,
        **account_data.model_dump()
    )
    
    db.add(bank_account)
    await db.commit()
    await db.refresh(bank_account)
    
    return bank_account


async def get_bank_accounts(
    db: AsyncSession,
    seller_id: int
) -> List[SellerBankAccount]:
    """Get all bank accounts for a seller"""
    result = await db.execute(
        select(SellerBankAccount)
        .where(SellerBankAccount.seller_id == seller_id)
        .order_by(SellerBankAccount.is_default.desc())
    )
    return result.scalars().all()


async def get_default_bank_account(
    db: AsyncSession,
    seller_id: int
) -> Optional[SellerBankAccount]:
    """Get default bank account for a seller"""
    result = await db.execute(
        select(SellerBankAccount)
        .where(
            and_(
                SellerBankAccount.seller_id == seller_id,
                SellerBankAccount.is_default == True
            )
        )
    )
    return result.scalar_one_or_none()


async def update_bank_account(
    db: AsyncSession,
    account_id: int,
    seller_id: int,
    update_data: SellerBankAccountUpdate
) -> SellerBankAccount:
    """Update bank account"""
    result = await db.execute(
        select(SellerBankAccount)
        .where(
            and_(
                SellerBankAccount.id == account_id,
                SellerBankAccount.seller_id == seller_id
            )
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise NotFoundException("Bank account not found")
    
    if update_data.is_default:
        await db.execute(
            SellerBankAccount.__table__.update()
            .where(SellerBankAccount.seller_id == seller_id)
            .values(is_default=False)
        )
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    
    account.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(account)
    
    return account


async def delete_bank_account(
    db: AsyncSession,
    account_id: int,
    seller_id: int
) -> bool:
    """Delete bank account"""
    result = await db.execute(
        select(SellerBankAccount)
        .where(
            and_(
                SellerBankAccount.id == account_id,
                SellerBankAccount.seller_id == seller_id
            )
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise NotFoundException("Bank account not found")
    
    await db.delete(account)
    await db.commit()
    
    return True


# ============================================
# SELLER DASHBOARD STATS
# ============================================

async def get_seller_dashboard_stats(
    db: AsyncSession,
    seller_id: int
) -> SellerDashboardStats:
    """Get dashboard statistics for a seller"""
    from modules.products.models import Product
    
    product_count = await db.execute(
        select(func.count()).where(
            and_(
                Product.seller_id == seller_id,
                Product.is_active == True
            )
        )
    )
    total_products = product_count.scalar() or 0
    
    # Placeholder — to be wired up once the orders/payments module exists.
    total_orders = 0
    pending_orders = 0
    total_revenue = 0.0
    total_commission = 0.0
    total_earnings = 0.0
    average_rating = 0.0
    total_reviews = 0
    recent_orders = []
    sales_chart = {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "values": [0, 0, 0, 0, 0, 0, 0]
    }
    
    return SellerDashboardStats(
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_commission=total_commission,
        pending_orders=pending_orders,
        total_earnings=total_earnings,
        average_rating=average_rating,
        total_reviews=total_reviews,
        recent_orders=recent_orders,
        sales_chart=sales_chart
    )


# ============================================
# SELLER LISTING & SEARCH
# ============================================

async def list_sellers(
    db: AsyncSession,
    filters: Dict[str, Any],
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """List sellers with filters"""
    query = select(SellerProfile)
    count_query = select(func.count()).select_from(SellerProfile)
    
    conditions = []
    
    if filters.get('status'):
        conditions.append(SellerProfile.status == filters['status'])
    
    if filters.get('is_active') is not None:
        conditions.append(SellerProfile.is_active == filters['is_active'])
    
    if filters.get('is_verified') is not None:
        conditions.append(SellerProfile.is_verified == filters['is_verified'])
    
    if filters.get('search'):
        search_term = f"%{filters['search']}%"
        conditions.append(
            or_(
                SellerProfile.business_name.ilike(search_term),
                SellerProfile.store_name.ilike(search_term),
                SellerProfile.store_slug.ilike(search_term)
            )
        )
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }