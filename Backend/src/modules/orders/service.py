from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from fastapi import status as http_status

from .models import (
    Order, SellerOrder, SellerOrderItem,
    OrderStatusHistory, OrderStatus, SellerOrderStatus
)
from .schemas import OrderCreate, OrderFilterParams, SellerOrderStatusUpdate, AdminOrderStatusUpdate
from modules.cart.models import Cart, CartItem, CartStatus
from modules.products.models import Product, ProductVariant, InventoryLog, StockAdjustmentReason
from modules.sellers.models import SellerProfile
from core.config import settings
from core.exceptions import CommerceException, NotFoundException


# ============================================
# VALID STATUS TRANSITIONS
# ============================================

# Sellers can only move forward, never skip states, never back.
SELLER_STATUS_TRANSITIONS: Dict[SellerOrderStatus, List[SellerOrderStatus]] = {
    SellerOrderStatus.PENDING:    [SellerOrderStatus.CONFIRMED, SellerOrderStatus.CANCELLED],
    SellerOrderStatus.CONFIRMED:  [SellerOrderStatus.PROCESSING, SellerOrderStatus.CANCELLED],
    SellerOrderStatus.PROCESSING: [SellerOrderStatus.SHIPPED],
    SellerOrderStatus.SHIPPED:    [SellerOrderStatus.DELIVERED],
    SellerOrderStatus.DELIVERED:  [],
    SellerOrderStatus.CANCELLED:  [],
}


# ============================================
# INTERNAL HELPERS
# ============================================

async def _load_order(
    db: AsyncSession,
    order_id: int,
    user_id: Optional[int] = None,
) -> Order:
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.seller_orders).options(
                selectinload(SellerOrder.items),
                selectinload(SellerOrder.status_history),
            ),
            selectinload(Order.status_history),
        )
    )
    if user_id is not None:
        query = query.where(Order.user_id == user_id)

    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    return order


async def _record_status_change(
    db: AsyncSession,
    order_id: Optional[int],
    seller_order_id: Optional[int],
    from_status: Optional[str],
    to_status: str,
    changed_by: Optional[int],
    note: Optional[str] = None,
) -> None:
    history = OrderStatusHistory(
        order_id=order_id,
        seller_order_id=seller_order_id,
        changed_by=changed_by,
        from_status=from_status,
        to_status=to_status,
        note=note,
    )
    db.add(history)


async def _deduct_stock(
    db: AsyncSession,
    product: Product,
    variant: Optional[ProductVariant],
    quantity: int,
    order_reference: str,
    user_id: Optional[int],
) -> None:
    """
    Deducts stock immediately on order placement using InventoryLog,
    matching the pattern in modules/products/service.py adjust_inventory.
    """
    if variant:
        qty_before = variant.stock_quantity
        new_qty = max(qty_before - quantity, 0)
        variant.stock_quantity = new_qty
        qty_after = new_qty
    else:
        qty_before = product.stock_quantity
        new_qty = max(qty_before - quantity, 0)
        product.stock_quantity = new_qty
        qty_after = new_qty

        if product.track_inventory:
            if product.stock_quantity == 0:
                from modules.products.models import ProductStatus
                product.status = ProductStatus.OUT_OF_STOCK

    log = InventoryLog(
        product_id=product.id,
        variant_id=variant.id if variant else None,
        quantity_before=qty_before,
        quantity_change=-quantity,
        quantity_after=qty_after,
        reason=StockAdjustmentReason.SALE,
        reference_id=order_reference,
        notes=f"Deducted on order placement",
        created_by=user_id,
    )
    db.add(log)


async def _restore_stock(
    db: AsyncSession,
    product: Product,
    variant: Optional[ProductVariant],
    quantity: int,
    order_reference: str,
    user_id: Optional[int],
) -> None:
    """Restores stock on order cancellation."""
    if variant:
        qty_before = variant.stock_quantity
        variant.stock_quantity = qty_before + quantity
        qty_after = variant.stock_quantity
    else:
        qty_before = product.stock_quantity
        product.stock_quantity = qty_before + quantity
        qty_after = product.stock_quantity

        if product.track_inventory:
            from modules.products.models import ProductStatus
            if product.status == ProductStatus.OUT_OF_STOCK and product.stock_quantity > 0:
                product.status = ProductStatus.ACTIVE

    log = InventoryLog(
        product_id=product.id,
        variant_id=variant.id if variant else None,
        quantity_before=qty_before,
        quantity_change=quantity,
        quantity_after=qty_after,
        reason=StockAdjustmentReason.RETURN,
        reference_id=order_reference,
        notes="Restored on order cancellation",
        created_by=user_id,
    )
    db.add(log)


def _commission_rate_for(seller: Optional[SellerProfile]) -> Decimal:
    if seller and seller.custom_commission_rate is not None:
        return Decimal(str(seller.custom_commission_rate))
    return Decimal(str(settings.DEFAULT_COMMISSION_PERCENTAGE))


# ============================================
# CREATE ORDER (main checkout function)
# ============================================

async def create_order(
    db: AsyncSession,
    user_id: int,
    cart_id: int,
    notes: Optional[str] = None,
) -> Order:
    """
    Full checkout:
    1. Validate cart (active, belongs to user, has items, each item is still
       purchasable and has sufficient stock).
    2. Group items by seller_id.
    3. Create parent Order.
    4. For each seller group: create SellerOrder + SellerOrderItems,
       calculate commission, deduct stock.
    5. Mark cart as CONVERTED.
    6. Generate human-readable order_number after flush.

    Does NOT handle payment, email, or commission disbursement —
    those are triggered downstream by the Payments module.
    """
    cart_result = await db.execute(
        select(Cart)
        .where(and_(Cart.id == cart_id, Cart.user_id == user_id))
        .options(selectinload(Cart.items))
    )
    cart = cart_result.scalar_one_or_none()

    if not cart:
        raise NotFoundException("Cart not found")
    if cart.status != CartStatus.ACTIVE:
        raise CommerceException("Cart is no longer active", http_status.HTTP_409_CONFLICT)
    if not cart.items:
        raise CommerceException("Cart is empty", http_status.HTTP_400_BAD_REQUEST)

    # Load shipping address snapshot
    shipping_address_snapshot: Optional[dict] = None
    if cart.shipping_address_id:
        from modules.users.models import UserAddress
        addr_result = await db.execute(
            select(UserAddress).where(
                and_(UserAddress.id == cart.shipping_address_id, UserAddress.user_id == user_id)
            )
        )
        addr = addr_result.scalar_one_or_none()
        if addr:
            shipping_address_snapshot = {
                "address_line1": addr.address_line1,
                "address_line2": addr.address_line2,
                "city": addr.city,
                "state": addr.state,
                "postal_code": addr.postal_code,
                "country": addr.country,
                "recipient_name": addr.recipient_name,
                "phone_number": addr.phone_number,
            }

    # Validate every line item before writing anything
    from modules.products.models import ProductStatus as PS
    items_by_seller: Dict[int, List[CartItem]] = {}

    for item in cart.items:
        prod_result = await db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = prod_result.scalar_one_or_none()
        if not product or product.status != PS.ACTIVE or not product.is_published:
            raise CommerceException(
                f"Product '{product.name if product else item.product_id}' is no longer available",
                http_status.HTTP_400_BAD_REQUEST,
            )

        variant = None
        if item.variant_id:
            var_result = await db.execute(
                select(ProductVariant).where(
                    and_(ProductVariant.id == item.variant_id, ProductVariant.product_id == product.id)
                )
            )
            variant = var_result.scalar_one_or_none()
            if not variant or not variant.is_active:
                raise CommerceException(
                    f"Variant for '{product.name}' is no longer available",
                    http_status.HTTP_400_BAD_REQUEST,
                )

        available = (variant.stock_quantity if variant else product.stock_quantity) \
            if product.track_inventory else None

        if available is not None and item.quantity > available and not product.allow_backorder:
            raise CommerceException(
                f"Insufficient stock for '{product.name}': requested {item.quantity}, available {available}",
                http_status.HTTP_409_CONFLICT,
            )

        seller_id = item.seller_id
        items_by_seller.setdefault(seller_id, []).append(item)

    # Calculate parent order totals from cart
    subtotal = sum(
        item.unit_price * item.quantity for item in cart.items
    )
    discount_amount = cart.discount_amount or Decimal("0")
    shipping_amount = Decimal("0")  # Shipping module will set this when built
    total = subtotal - discount_amount + shipping_amount

    # Create parent Order
    order = Order(
        user_id=user_id,
        cart_id=cart_id,
        subtotal=subtotal,
        discount_amount=discount_amount,
        shipping_amount=shipping_amount,
        total=total,
        currency="USD",
        shipping_address=shipping_address_snapshot,
        notes=notes,
        coupon_code=cart.coupon_code,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    await db.flush()  # get order.id for order_number and seller_order FKs

    # Set human-readable order number using the generated ID
    order.order_number = f"FC-{datetime.utcnow().year}-{order.id:06d}"

    await _record_status_change(
        db, order_id=order.id, seller_order_id=None,
        from_status=None, to_status=OrderStatus.PENDING,
        changed_by=user_id, note="Order placed"
    )

    # Create one SellerOrder per seller, with stock deduction
    for seller_id, seller_items in items_by_seller.items():
        seller_result = await db.execute(
            select(SellerProfile).where(SellerProfile.id == seller_id)
        )
        seller = seller_result.scalar_one_or_none()

        commission_rate = _commission_rate_for(seller)
        seller_subtotal = sum(item.unit_price * item.quantity for item in seller_items)
        commission_amount = (seller_subtotal * commission_rate / Decimal("100")).quantize(Decimal("0.01"))
        seller_earnings = seller_subtotal - commission_amount

        seller_order = SellerOrder(
            order_id=order.id,
            seller_id=seller_id,
            subtotal=seller_subtotal,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            seller_earnings=seller_earnings,
            status=SellerOrderStatus.PENDING,
        )
        db.add(seller_order)
        await db.flush()  # get seller_order.id for items and history

        await _record_status_change(
            db, order_id=None, seller_order_id=seller_order.id,
            from_status=None, to_status=SellerOrderStatus.PENDING,
            changed_by=user_id, note="Seller order created"
        )

        for item in seller_items:
            prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = prod_result.scalar_one_or_none()

            variant = None
            if item.variant_id:
                var_result = await db.execute(
                    select(ProductVariant).where(ProductVariant.id == item.variant_id)
                )
                variant = var_result.scalar_one_or_none()

            order_item = SellerOrderItem(
                seller_order_id=seller_order.id,
                product_id=product.id,
                variant_id=item.variant_id,
                product_name=product.name,
                product_sku=variant.sku if variant else product.sku,
                variant_name=variant.name if variant else None,
                unit_price=item.unit_price,
                quantity=item.quantity,
                subtotal=item.unit_price * item.quantity,
            )
            db.add(order_item)

            # Deduct stock immediately
            await _deduct_stock(
                db, product, variant,
                quantity=item.quantity,
                order_reference=order.order_number,
                user_id=user_id,
            )

    # Mark cart as converted
    cart.status = CartStatus.CONVERTED

    await db.commit()

    # TODO: trigger Notifications module — send order confirmation email
    # await notifications_service.send_order_confirmation(db, order.id)

    # TODO: trigger Payments module — initiate payment intent
    # await payments_service.create_payment_intent(db, order.id)

    return await _load_order(db, order.id)


# ============================================
# READ
# ============================================

async def get_order(
    db: AsyncSession,
    order_id: int,
    user_id: Optional[int] = None,
) -> Order:
    return await _load_order(db, order_id, user_id=user_id)


async def list_orders(
    db: AsyncSession,
    user_id: int,
    filters: OrderFilterParams,
) -> Dict[str, Any]:
    query = select(Order).where(Order.user_id == user_id)

    if filters.status:
        query = query.where(Order.status == filters.status)
    if filters.date_from:
        query = query.where(Order.created_at >= filters.date_from)
    if filters.date_to:
        query = query.where(Order.created_at <= filters.date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.order_by(desc(Order.created_at))
    query = query.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)

    result = await db.execute(
        query.options(selectinload(Order.seller_orders).options(selectinload(SellerOrder.items)))
    )
    orders = result.scalars().all()

    items = []
    for o in orders:
        item_count = sum(i.quantity for so in o.seller_orders for i in so.items)
        items.append({
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "total": o.total,
            "currency": o.currency,
            "item_count": item_count,
            "seller_count": len(o.seller_orders),
            "created_at": o.created_at,
        })

    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "total_pages": (total + filters.per_page - 1) // filters.per_page,
    }


async def list_seller_orders(
    db: AsyncSession,
    seller_id: int,
    filters: OrderFilterParams,
) -> Dict[str, Any]:
    query = select(SellerOrder).where(SellerOrder.seller_id == seller_id)

    if filters.status:
        query = query.where(SellerOrder.status == filters.status.value
                            if hasattr(filters.status, 'value') else filters.status)
    if filters.date_from:
        query = query.where(SellerOrder.created_at >= filters.date_from)
    if filters.date_to:
        query = query.where(SellerOrder.created_at <= filters.date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.order_by(desc(SellerOrder.created_at))
    query = query.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)

    result = await db.execute(
        query.options(
            selectinload(SellerOrder.items),
            selectinload(SellerOrder.status_history),
        )
    )
    seller_orders = result.scalars().all()

    return {
        "items": seller_orders,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "total_pages": (total + filters.per_page - 1) // filters.per_page,
    }


# ============================================
# SELLER STATUS UPDATE (state machine)
# ============================================

async def update_seller_order_status(
    db: AsyncSession,
    seller_order_id: int,
    seller_id: int,
    update_data: SellerOrderStatusUpdate,
    user_id: int,
) -> SellerOrder:
    result = await db.execute(
        select(SellerOrder)
        .where(and_(SellerOrder.id == seller_order_id, SellerOrder.seller_id == seller_id))
        .options(selectinload(SellerOrder.items), selectinload(SellerOrder.status_history))
    )
    seller_order = result.scalar_one_or_none()
    if not seller_order:
        raise NotFoundException("Seller order not found")

    allowed = SELLER_STATUS_TRANSITIONS.get(seller_order.status, [])
    if update_data.status not in allowed:
        raise CommerceException(
            f"Cannot transition from '{seller_order.status}' to '{update_data.status}'. "
            f"Allowed transitions: {[s.value for s in allowed]}",
            http_status.HTTP_400_BAD_REQUEST,
        )

    old_status = seller_order.status
    seller_order.status = update_data.status

    if update_data.status == SellerOrderStatus.SHIPPED:
        seller_order.shipped_at = datetime.utcnow()
        if update_data.tracking_number:
            seller_order.tracking_number = update_data.tracking_number
    elif update_data.status == SellerOrderStatus.DELIVERED:
        seller_order.delivered_at = datetime.utcnow()

    await _record_status_change(
        db, order_id=None, seller_order_id=seller_order.id,
        from_status=old_status.value, to_status=update_data.status.value,
        changed_by=user_id, note=update_data.note,
    )

    # If all seller orders are now delivered, roll up the parent order status
    parent_result = await db.execute(
        select(Order).where(Order.id == seller_order.order_id)
        .options(selectinload(Order.seller_orders))
    )
    parent = parent_result.scalar_one_or_none()
    if parent:
        all_statuses = {so.status for so in parent.seller_orders}
        if all_statuses == {SellerOrderStatus.DELIVERED}:
            old_parent = parent.status
            parent.status = OrderStatus.DELIVERED
            await _record_status_change(
                db, order_id=parent.id, seller_order_id=None,
                from_status=old_parent.value, to_status=OrderStatus.DELIVERED.value,
                changed_by=user_id, note="All seller orders delivered",
            )
        elif SellerOrderStatus.SHIPPED in all_statuses:
            if parent.status == OrderStatus.CONFIRMED:
                old_parent = parent.status
                parent.status = OrderStatus.SHIPPED
                await _record_status_change(
                    db, order_id=parent.id, seller_order_id=None,
                    from_status=old_parent.value, to_status=OrderStatus.SHIPPED.value,
                    changed_by=user_id, note="At least one seller order shipped",
                )

    seller_order.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(seller_order)

    # TODO: trigger Notifications module
    # await notifications_service.send_order_status_update(db, seller_order_id)

    return seller_order


# ============================================
# CANCEL ORDER
# ============================================

async def cancel_order(
    db: AsyncSession,
    order_id: int,
    user_id: int,
) -> Order:
    order = await _load_order(db, order_id, user_id=user_id)

    if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
        raise CommerceException(
            f"Order cannot be cancelled in '{order.status}' status. "
            "Only PENDING or CONFIRMED orders can be cancelled.",
            http_status.HTTP_400_BAD_REQUEST,
        )

    old_status = order.status
    order.status = OrderStatus.CANCELLED

    await _record_status_change(
        db, order_id=order.id, seller_order_id=None,
        from_status=old_status.value, to_status=OrderStatus.CANCELLED.value,
        changed_by=user_id, note="Cancelled by customer",
    )

    # Cancel all seller sub-orders and restore stock
    for seller_order in order.seller_orders:
        if seller_order.status not in (SellerOrderStatus.DELIVERED, SellerOrderStatus.CANCELLED):
            old_so_status = seller_order.status
            seller_order.status = SellerOrderStatus.CANCELLED
            seller_order.updated_at = datetime.utcnow()

            await _record_status_change(
                db, order_id=None, seller_order_id=seller_order.id,
                from_status=old_so_status.value, to_status=SellerOrderStatus.CANCELLED.value,
                changed_by=user_id, note="Order cancelled by customer",
            )

            for item in seller_order.items:
                prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
                product = prod_result.scalar_one_or_none()
                if not product:
                    continue

                variant = None
                if item.variant_id:
                    var_result = await db.execute(
                        select(ProductVariant).where(ProductVariant.id == item.variant_id)
                    )
                    variant = var_result.scalar_one_or_none()

                await _restore_stock(
                    db, product, variant,
                    quantity=item.quantity,
                    order_reference=order.order_number,
                    user_id=user_id,
                )

    await db.commit()

    # TODO: trigger Notifications module
    # await notifications_service.send_cancellation_confirmation(db, order.id)

    # TODO: trigger Payments module — initiate refund if already paid
    # await payments_service.refund_order(db, order.id)

    return await _load_order(db, order.id)


# ============================================
# ADMIN
# ============================================

async def admin_list_orders(
    db: AsyncSession,
    filters: OrderFilterParams,
    seller_id: Optional[int] = None,
) -> Dict[str, Any]:
    query = select(Order)

    if filters.status:
        query = query.where(Order.status == filters.status)
    if filters.date_from:
        query = query.where(Order.created_at >= filters.date_from)
    if filters.date_to:
        query = query.where(Order.created_at <= filters.date_to)
    if seller_id:
        query = query.where(
            Order.id.in_(select(SellerOrder.order_id).where(SellerOrder.seller_id == seller_id))
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.order_by(desc(Order.created_at))
    query = query.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)

    result = await db.execute(
        query.options(selectinload(Order.seller_orders).options(selectinload(SellerOrder.items)))
    )
    orders = result.scalars().all()

    items = []
    for o in orders:
        item_count = sum(i.quantity for so in o.seller_orders for i in so.items)
        items.append({
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "total": o.total,
            "currency": o.currency,
            "item_count": item_count,
            "seller_count": len(o.seller_orders),
            "created_at": o.created_at,
        })

    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "total_pages": (total + filters.per_page - 1) // filters.per_page,
    }


async def admin_update_order_status(
    db: AsyncSession,
    order_id: int,
    update_data: AdminOrderStatusUpdate,
    admin_id: int,
) -> Order:
    order = await _load_order(db, order_id)

    old_status = order.status
    order.status = update_data.status

    await _record_status_change(
        db, order_id=order.id, seller_order_id=None,
        from_status=old_status.value, to_status=update_data.status.value,
        changed_by=admin_id, note=update_data.note,
    )

    order.updated_at = datetime.utcnow()
    await db.commit()

    # TODO: trigger Notifications module
    # await notifications_service.send_admin_status_update(db, order.id)

    return await _load_order(db, order.id)