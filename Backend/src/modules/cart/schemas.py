from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from .models import CartStatus


# ============================================
# CART ITEM SCHEMAS
# ============================================

class CartItemAdd(BaseModel):
    """Payload for adding an item to the cart."""
    product_id: int
    variant_id: Optional[int] = None
    quantity:   int = Field(1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    """Update quantity or saved-for-later flag."""
    quantity:        Optional[int]  = Field(None, ge=1, le=100)
    saved_for_later: Optional[bool] = None


class CartItemProductSummary(BaseModel):
    """Lightweight product snapshot embedded in CartItemResponse."""
    id:                int
    name:              str
    slug:              str
    primary_image_url: Optional[str] = None
    sku:               Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartItemVariantSummary(BaseModel):
    """Lightweight variant snapshot embedded in CartItemResponse."""
    id:         int
    name:       str
    sku:        Optional[str] = None
    attributes: Optional[dict] = None
    image_url:  Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartItemSellerSummary(BaseModel):
    id:         int
    store_name: str
    store_slug: str

    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    id:              int
    cart_id:         int
    product_id:      int
    variant_id:      Optional[int] = None
    quantity:        int
    unit_price:      Decimal
    original_price:  Optional[Decimal] = None
    subtotal:        Decimal
    saved_for_later: bool
    created_at:      datetime
    updated_at:      Optional[datetime] = None

    product: Optional[CartItemProductSummary] = None
    variant: Optional[CartItemVariantSummary] = None
    seller:  Optional[CartItemSellerSummary]  = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# CART SCHEMAS
# ============================================

class CartSummary(BaseModel):
    """Totals block returned with every cart response."""
    item_count:      int      # distinct active line items
    total_quantity:  int      # sum of all active quantities
    subtotal:        Decimal  # sum of (unit_price × quantity)
    discount_amount: Decimal
    total:           Decimal  # subtotal − discount_amount
    savings:         Decimal  # sum of (original_price − unit_price) × qty
    seller_count:    int      # distinct sellers in the active cart


class CartResponse(BaseModel):
    id:                  int
    user_id:             Optional[int] = None
    session_id:          Optional[str] = None
    status:              CartStatus
    coupon_code:         Optional[str] = None
    discount_amount:     Decimal
    shipping_address_id: Optional[int] = None
    notes:               Optional[str] = None
    expires_at:          Optional[datetime] = None
    created_at:          datetime
    updated_at:          Optional[datetime] = None

    items:           List[CartItemResponse] = []   # active items
    saved_for_later: List[CartItemResponse] = []   # saved items
    summary:         CartSummary

    model_config = ConfigDict(from_attributes=True)


class CartUpdate(BaseModel):
    """Update top-level cart fields."""
    coupon_code:         Optional[str] = Field(None, max_length=50)
    notes:               Optional[str] = None
    shipping_address_id: Optional[int] = None


# ============================================
# CHECKOUT VALIDATION SCHEMA
# ============================================

class StockIssue(BaseModel):
    product_id:         int
    variant_id:         Optional[int] = None
    product_name:       str
    requested_quantity: int
    available_quantity: int


class CartValidationResult(BaseModel):
    """
    Result of pre-checkout cart validation.
    is_valid=False if any item has stock issues or its product
    was deactivated since it was added to the cart.
    """
    is_valid:      bool
    stock_issues:  List[StockIssue] = []
    removed_items: List[int] = []    # item IDs removed (product no longer active)