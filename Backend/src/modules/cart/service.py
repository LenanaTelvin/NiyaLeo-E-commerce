from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime

from .models import Cart, CartItem, CartStatus
from .schemas import (
    CartItemAdd, CartItemUpdate, CartUpdate,
    CartSummary, CartResponse, CartValidationResult, StockIssue,
)
from modules.products.models import Product, ProductVariant, ProductStatus
from modules.Auth.models import User
from core.exceptions import CommerceException, NotFoundException
from fastapi import status as http_status


# ============================================
# INTERNAL HELPERS
# ============================================

async def _load_cart(db: AsyncSession, cart_id: int) -> Cart:
    """Load a cart with all relations eager-loaded."""
    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(
            selectinload(Cart.items).selectinload(CartItem.product),
            selectinload(Cart.items).selectinload(CartItem.variant),
            selectinload(Cart.items).selectinload(CartItem.seller),
            selectinload(Cart.shipping_address),
        )
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise NotFoundException("Cart not found")
    return cart


def _compute_summary(cart: Cart) -> CartSummary:
    """Compute totals from the cart's active (not saved-for-later) items."""
    active_items = [i for i in cart.items if not i.saved_for_later]
    saved_items  = [i for i in cart.items if i.saved_for_later]

    item_count     = len(active_items)
    total_quantity = sum(i.quantity for i in active_items)
    subtotal       = sum(
        Decimal(str(i.unit_price)) * i.quantity for i in active_items
    )
    savings = sum(
        (Decimal(str(i.original_price)) - Decimal(str(i.unit_price))) * i.quantity
        for i in active_items
        if i.original_price and i.original_price > i.unit_price
    )
    discount_amount = Decimal(str(cart.discount_amount or 0))
    total           = max(subtotal - discount_amount, Decimal("0.00"))
    seller_ids      = {i.seller_id for i in active_items if i.seller_id}

    return CartSummary(
        item_count=item_count,
        total_quantity=total_quantity,
        subtotal=subtotal,
        discount_amount=discount_amount,
        total=total,
        savings=savings,
        seller_count=len(seller_ids),
    )


async def _get_or_create_active_cart(db: AsyncSession, user_id: int) -> Cart:
    """Return the user's single active cart, creating one if none exists."""
    result = await db.execute(
        select(Cart).where(
            and_(
                Cart.user_id == user_id,
                Cart.status == CartStatus.ACTIVE,
            )
        )
    )
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id, status=CartStatus.ACTIVE)
        db.add(cart)
        await db.flush()

    return cart


async def _assert_product_purchasable(
    db: AsyncSession,
    product_id: int,
    variant_id: Optional[int],
    requested_qty: int,
) -> tuple[Product, Optional[ProductVariant]]:
    """
    Verify the product (and variant) exists, is active/published, and
    has sufficient stock. Returns (product, variant).
    """
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundException("Product not found")

    if not product.is_published or product.status not in (
        ProductStatus.ACTIVE,
    ):
        raise CommerceException(
            "This product is not available for purchase",
            http_status.HTTP_400_BAD_REQUEST,
        )

    variant: Optional[ProductVariant] = None

    if variant_id:
        variant = next(
            (v for v in product.variants if v.id == variant_id), None
        )
        if not variant or not variant.is_active:
            raise NotFoundException("Product variant not found or inactive")

        if product.track_inventory and not product.allow_backorder:
            if variant.stock_quantity < requested_qty:
                raise CommerceException(
                    f"Only {variant.stock_quantity} units available",
                    http_status.HTTP_400_BAD_REQUEST,
                )
    else:
        if product.track_inventory and not product.allow_backorder:
            if product.stock_quantity < requested_qty:
                raise CommerceException(
                    f"Only {product.stock_quantity} units available",
                    http_status.HTTP_400_BAD_REQUEST,
                )

    return product, variant


# ============================================
# GET CART
# ============================================

async def get_cart(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """
    Get (or auto-create) the user's active cart and return it
    with a computed summary.
    """
    cart = await _get_or_create_active_cart(db, user_id)
    await db.commit()

    # Reload with relations
    cart = await _load_cart(db, cart.id)

    active_items = [i for i in cart.items if not i.saved_for_later]
    saved_items  = [i for i in cart.items if i.saved_for_later]
    summary      = _compute_summary(cart)

    return {
        "cart":        cart,
        "active_items": active_items,
        "saved_items":  saved_items,
        "summary":      summary,
    }


# ============================================
# ADD ITEM
# ============================================

async def add_item(
    db: AsyncSession,
    user_id: int,
    data: CartItemAdd,
) -> Dict[str, Any]:
    """
    Add a product (+ optional variant) to the cart.

    If the exact (product, variant) combination already exists in the cart,
    the quantity is incremented rather than creating a duplicate row —
    enforced by the unique constraint on (cart_id, product_id, variant_id).
    """
    product, variant = await _assert_product_purchasable(
        db, data.product_id, data.variant_id, data.quantity
    )

    cart = await _get_or_create_active_cart(db, user_id)

    # Check for existing line
    existing_result = await db.execute(
        select(CartItem).where(
            and_(
                CartItem.cart_id   == cart.id,
                CartItem.product_id == data.product_id,
                CartItem.variant_id == data.variant_id,
            )
        )
    )
    existing_item = existing_result.scalar_one_or_none()

    # Snapshot the price at add-time
    if variant and variant.price_override is not None:
        unit_price = Decimal(str(variant.price_override))
    else:
        unit_price = Decimal(str(product.price))

    original_price = (
        Decimal(str(product.compare_price))
        if product.compare_price
        else None
    )

    if existing_item:
        new_qty = existing_item.quantity + data.quantity

        # Re-check stock for the combined quantity
        stock = variant.stock_quantity if variant else product.stock_quantity
        if (
            product.track_inventory
            and not product.allow_backorder
            and new_qty > stock
        ):
            raise CommerceException(
                f"Cannot add {data.quantity} more — only "
                f"{stock - existing_item.quantity} additional units available",
                http_status.HTTP_400_BAD_REQUEST,
            )

        existing_item.quantity       = new_qty
        existing_item.saved_for_later = False   # re-activate if it was saved
    else:
        new_item = CartItem(
            cart_id        = cart.id,
            product_id     = data.product_id,
            variant_id     = data.variant_id,
            quantity       = data.quantity,
            unit_price     = unit_price,
            original_price = original_price,
            seller_id      = product.seller_id,
        )
        db.add(new_item)

    cart.updated_at = datetime.utcnow()
    await db.commit()

    return await get_cart(db, user_id)


# ============================================
# UPDATE ITEM
# ============================================

async def update_item(
    db: AsyncSession,
    user_id: int,
    item_id: int,
    data: CartItemUpdate,
) -> Dict[str, Any]:
    """Update quantity or saved-for-later flag on a cart item."""
    cart = await _get_or_create_active_cart(db, user_id)

    result = await db.execute(
        select(CartItem).where(
            and_(
                CartItem.id      == item_id,
                CartItem.cart_id == cart.id,
            )
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Cart item not found")

    if data.quantity is not None:
        # Re-validate stock for the new quantity
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = product_result.scalar_one_or_none()

        if product and product.track_inventory and not product.allow_backorder:
            if item.variant_id:
                variant_result = await db.execute(
                    select(ProductVariant).where(
                        ProductVariant.id == item.variant_id
                    )
                )
                variant = variant_result.scalar_one_or_none()
                stock = variant.stock_quantity if variant else 0
            else:
                stock = product.stock_quantity

            if data.quantity > stock:
                raise CommerceException(
                    f"Only {stock} units available",
                    http_status.HTTP_400_BAD_REQUEST,
                )

        item.quantity = data.quantity

    if data.saved_for_later is not None:
        item.saved_for_later = data.saved_for_later

    item.updated_at   = datetime.utcnow()
    cart.updated_at   = datetime.utcnow()
    await db.commit()

    return await get_cart(db, user_id)


# ============================================
# REMOVE ITEM
# ============================================

async def remove_item(
    db: AsyncSession,
    user_id: int,
    item_id: int,
) -> Dict[str, Any]:
    """Remove a single item from the cart."""
    cart = await _get_or_create_active_cart(db, user_id)

    result = await db.execute(
        select(CartItem).where(
            and_(
                CartItem.id      == item_id,
                CartItem.cart_id == cart.id,
            )
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Cart item not found")

    await db.delete(item)
    cart.updated_at = datetime.utcnow()
    await db.commit()

    return await get_cart(db, user_id)


# ============================================
# CLEAR CART
# ============================================

async def clear_cart(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Remove all items from the cart (keeps the cart row itself)."""
    cart = await _get_or_create_active_cart(db, user_id)

    await db.execute(
        delete(CartItem).where(CartItem.cart_id == cart.id)
    )
    cart.coupon_code     = None
    cart.discount_amount = Decimal("0.00")
    cart.updated_at      = datetime.utcnow()
    await db.commit()

    return await get_cart(db, user_id)


# ============================================
# UPDATE CART (coupon, notes, shipping address)
# ============================================

async def update_cart(
    db: AsyncSession,
    user_id: int,
    data: CartUpdate,
) -> Dict[str, Any]:
    """Update top-level cart fields — coupon, notes, shipping address."""
    cart = await _get_or_create_active_cart(db, user_id)

    if data.coupon_code is not None:
        # Placeholder — real coupon validation wired in Phase 3
        cart.coupon_code     = data.coupon_code or None
        cart.discount_amount = Decimal("0.00")

    if data.notes is not None:
        cart.notes = data.notes

    if data.shipping_address_id is not None:
        # Verify the address belongs to this user
        from modules.users.models import UserAddress
        addr_result = await db.execute(
            select(UserAddress).where(
                and_(
                    UserAddress.id      == data.shipping_address_id,
                    UserAddress.user_id == user_id,
                )
            )
        )
        if not addr_result.scalar_one_or_none():
            raise NotFoundException("Shipping address not found")
        cart.shipping_address_id = data.shipping_address_id

    cart.updated_at = datetime.utcnow()
    await db.commit()

    return await get_cart(db, user_id)


# ============================================
# VALIDATE CART (pre-checkout check)
# ============================================

async def validate_cart(
    db: AsyncSession,
    user_id: int,
) -> CartValidationResult:
    """
    Run a pre-checkout validation pass:
    - Flag items whose product is no longer active/published
    - Flag items that exceed current stock
    - Auto-remove deactivated items and report their IDs

    Returns CartValidationResult so the frontend can show the buyer
    exactly what changed before they confirm the order.
    """
    cart_data    = await get_cart(db, user_id)
    cart         = cart_data["cart"]
    active_items = cart_data["active_items"]

    stock_issues:   List[StockIssue] = []
    removed_ids:    List[int]        = []

    for item in active_items:
        product = item.product

        # Product deactivated since it was added
        if not product or not product.is_published or product.status not in (
            ProductStatus.ACTIVE,
        ):
            removed_ids.append(item.id)
            await db.delete(item)
            continue

        # Stock check
        if product.track_inventory and not product.allow_backorder:
            if item.variant_id and item.variant:
                available = item.variant.stock_quantity
            else:
                available = product.stock_quantity

            if item.quantity > available:
                stock_issues.append(
                    StockIssue(
                        product_id         = product.id,
                        variant_id         = item.variant_id,
                        product_name       = product.name,
                        requested_quantity = item.quantity,
                        available_quantity = available,
                    )
                )

    if removed_ids:
        cart.updated_at = datetime.utcnow()
        await db.commit()

    return CartValidationResult(
        is_valid      = len(stock_issues) == 0 and len(removed_ids) == 0,
        stock_issues  = stock_issues,
        removed_items = removed_ids,
    )


# ============================================
# CONVERT CART → ORDER  (called by Orders module)
# ============================================

async def mark_cart_converted(db: AsyncSession, cart_id: int) -> Cart:
    """
    Mark a cart as CONVERTED once the Orders module has consumed it.
    Called internally — not exposed as an endpoint.
    """
    result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = result.scalar_one_or_none()
    if not cart:
        raise NotFoundException("Cart not found")

    cart.status     = CartStatus.CONVERTED
    cart.updated_at = datetime.utcnow()
    await db.commit()
    return cart