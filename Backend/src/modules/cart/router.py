from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from decimal import Decimal

from core.database import get_db
from modules.Auth.dependencies import get_current_user
from modules.Auth.models import User

from . import service
from .schemas import (
    CartItemAdd, CartItemUpdate, CartUpdate,
    CartResponse, CartItemResponse, CartSummary,
    CartValidationResult,
)
from .models import CartStatus

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])


# ── helpers ────────────────────────────────────────────────────────────

def _build_response(cart_data: dict) -> dict:
    """
    Shape the service dict into the CartResponse schema structure.
    Separates active items from saved-for-later and attaches summary.
    """
    cart    = cart_data["cart"]
    summary = cart_data["summary"]

    return {
        "id":                  cart.id,
        "user_id":             cart.user_id,
        "session_id":          cart.session_id,
        "status":              cart.status,
        "coupon_code":         cart.coupon_code,
        "discount_amount":     cart.discount_amount or Decimal("0.00"),
        "shipping_address_id": cart.shipping_address_id,
        "notes":               cart.notes,
        "expires_at":          cart.expires_at,
        "created_at":          cart.created_at,
        "updated_at":          cart.updated_at,
        "items":               cart_data["active_items"],
        "saved_for_later":     cart_data["saved_items"],
        "summary":             summary,
    }


# ══════════════════════════════════════════════════════════════════════
# CART ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@router.get("/", response_model=CartResponse)
async def get_my_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user's active cart.
    Auto-creates an empty cart if none exists — always returns 200.
    """
    cart_data = await service.get_cart(db, current_user.id)
    return _build_response(cart_data)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a product to the cart.
    If the same product+variant already exists, quantity is incremented.
    Validates stock availability before adding.
    """
    cart_data = await service.add_item(db, current_user.id, data)
    return _build_response(cart_data)


@router.patch("/items/{item_id}", response_model=CartResponse)
async def update_item(
    item_id: int,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update quantity or saved-for-later flag on a cart item.
    Validates stock when increasing quantity.
    """
    cart_data = await service.update_item(db, current_user.id, item_id, data)
    return _build_response(cart_data)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a single item from the cart."""
    cart_data = await service.remove_item(db, current_user.id, item_id)
    return _build_response(cart_data)


@router.delete("/", response_model=CartResponse)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove all items from the cart.
    Keeps the cart itself — resets coupon and discount too.
    """
    cart_data = await service.clear_cart(db, current_user.id)
    return _build_response(cart_data)


@router.patch("/", response_model=CartResponse)
async def update_cart(
    data: CartUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update cart-level fields:
    - coupon_code — apply or remove a discount code
    - notes       — buyer note to sellers
    - shipping_address_id — pre-select a saved address for checkout
    """
    cart_data = await service.update_cart(db, current_user.id, data)
    return _build_response(cart_data)


@router.post("/validate", response_model=CartValidationResult)
async def validate_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pre-checkout validation pass.
    Checks every active item for:
    - Product still active and published
    - Sufficient stock for requested quantity

    Automatically removes any items whose product was deactivated.
    Returns is_valid=false with details if anything needs buyer attention.
    Call this before showing the checkout summary page.
    """
    return await service.validate_cart(db, current_user.id)


@router.post("/items/{item_id}/save-for-later", response_model=CartResponse)
async def save_for_later(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Move an item from the active cart to the saved-for-later list."""
    data = CartItemUpdate(saved_for_later=True)
    cart_data = await service.update_item(db, current_user.id, item_id, data)
    return _build_response(cart_data)


@router.post("/items/{item_id}/move-to-cart", response_model=CartResponse)
async def move_to_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Move an item from saved-for-later back into the active cart."""
    data = CartItemUpdate(saved_for_later=False)
    cart_data = await service.update_item(db, current_user.id, item_id, data)
    return _build_response(cart_data)