from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from core.database import get_db
from modules.Auth.dependencies import get_current_user, get_current_admin
from modules.Auth.models import User
from modules.sellers.dependencies import get_current_seller_profile
from modules.sellers.models import SellerProfile

from . import service
from .schemas import (
    OrderCreate, OrderResponse, OrderListResponse,
    SellerOrderResponse, SellerOrderStatusUpdate,
    AdminOrderStatusUpdate, OrderFilterParams, OrderStatus
)

# ============================================
# THREE NAMED ROUTERS
# ============================================

customer_router = APIRouter(prefix="/api/v1/orders", tags=["Orders - Customer"])
seller_router   = APIRouter(prefix="/api/v1/seller/orders", tags=["Orders - Seller"])
admin_router    = APIRouter(prefix="/api/v1/admin/orders", tags=["Admin - Orders"])


# ============================================
# CUSTOMER ENDPOINTS
# ============================================

@customer_router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def checkout(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Place an order from the given cart.
    Validates stock, creates parent + seller sub-orders, deducts inventory,
    marks cart as converted.
    """
    return await service.create_order(
        db,
        user_id=current_user.id,
        cart_id=data.cart_id,
        notes=data.notes,
    )


@customer_router.get("/", response_model=OrderListResponse)
async def list_my_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current customer's order history, paginated."""
    filters = OrderFilterParams(
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    return await service.list_orders(db, current_user.id, filters)


@customer_router.get("/{order_id}", response_model=OrderResponse)
async def get_my_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single order (must belong to the authenticated user)."""
    return await service.get_order(db, order_id, user_id=current_user.id)


@customer_router.delete("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_my_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a PENDING or CONFIRMED order.
    Restores stock and triggers a refund stub (Payments module).
    """
    return await service.cancel_order(db, order_id, current_user.id)


# ============================================
# SELLER ENDPOINTS
# ============================================

@seller_router.get("/", response_model=OrderListResponse)
async def list_incoming_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get all incoming orders for the current seller's store."""
    filters = OrderFilterParams(
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    return await service.list_seller_orders(db, seller.id, filters)


@seller_router.get("/{seller_order_id}", response_model=SellerOrderResponse)
async def get_seller_order(
    seller_order_id: int,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get a single seller sub-order (must belong to this seller)."""
    from sqlalchemy import select, and_
    from sqlalchemy.orm import selectinload
    from .models import SellerOrder

    result = await db.execute(
        select(SellerOrder)
        .where(and_(SellerOrder.id == seller_order_id, SellerOrder.seller_id == seller.id))
        .options(
            selectinload(SellerOrder.items),
            selectinload(SellerOrder.status_history),
        )
    )
    seller_order = result.scalar_one_or_none()
    if not seller_order:
        from core.exceptions import NotFoundException
        raise NotFoundException("Seller order not found")
    return seller_order


@seller_router.patch("/{seller_order_id}/status", response_model=SellerOrderResponse)
async def update_order_status(
    seller_order_id: int,
    update_data: SellerOrderStatusUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Advance this seller sub-order through its lifecycle.
    State machine enforced: PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED.
    Cancellation allowed from PENDING or CONFIRMED only.
    """
    return await service.update_seller_order_status(
        db,
        seller_order_id=seller_order_id,
        seller_id=seller.id,
        update_data=update_data,
        user_id=current_user.id,
    )


# ============================================
# ADMIN ENDPOINTS
# ============================================

@admin_router.get("/", response_model=OrderListResponse)
async def admin_list_all_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    seller_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all orders across all sellers, filterable by seller and status."""
    filters = OrderFilterParams(
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    return await service.admin_list_orders(db, filters, seller_id=seller_id)


@admin_router.get("/{order_id}", response_model=OrderResponse)
async def admin_get_order(
    order_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get any order regardless of owner (admin view)."""
    return await service.get_order(db, order_id)


@admin_router.patch("/{order_id}/status", response_model=OrderResponse)
async def admin_update_status(
    order_id: int,
    update_data: AdminOrderStatusUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin can force any order to any status with an optional note."""
    return await service.admin_update_order_status(
        db,
        order_id=order_id,
        update_data=update_data,
        admin_id=current_admin.id,
    )