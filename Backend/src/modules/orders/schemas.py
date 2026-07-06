from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from .models import OrderStatus, SellerOrderStatus


# ============================================
# ORDER CREATE
# ============================================

class OrderCreate(BaseModel):
    cart_id: int
    notes: Optional[str] = None


# ============================================
# STATUS HISTORY
# ============================================

class OrderStatusHistoryResponse(BaseModel):
    id: int
    from_status: Optional[str]
    to_status: str
    note: Optional[str]
    changed_by: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SELLER ORDER ITEM
# ============================================

class SellerOrderItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    variant_id: Optional[int]
    product_name: str
    product_sku: Optional[str]
    variant_name: Optional[str]
    unit_price: Decimal
    quantity: int
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SELLER ORDER
# ============================================

class SellerOrderResponse(BaseModel):
    id: int
    order_id: int
    seller_id: Optional[int]
    subtotal: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    seller_earnings: Decimal
    status: SellerOrderStatus
    tracking_number: Optional[str]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[SellerOrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================
# ORDER RESPONSE (full nested)
# ============================================

class OrderResponse(BaseModel):
    id: int
    order_number: Optional[str]
    user_id: Optional[int]
    cart_id: Optional[int]
    subtotal: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    total: Decimal
    currency: str
    shipping_address: Optional[dict]
    notes: Optional[str]
    coupon_code: Optional[str]
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime]
    seller_orders: List[SellerOrderResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================
# ORDER LIST (lightweight)
# ============================================

class OrderListItem(BaseModel):
    id: int
    order_number: Optional[str]
    status: OrderStatus
    total: Decimal
    currency: str
    item_count: int
    seller_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: List[OrderListItem]
    total: int
    page: int
    per_page: int
    total_pages: int


# ============================================
# SELLER ORDER STATUS UPDATE
# ============================================

class SellerOrderStatusUpdate(BaseModel):
    status: SellerOrderStatus
    tracking_number: Optional[str] = None
    note: Optional[str] = None


# ============================================
# ADMIN ORDER STATUS UPDATE
# ============================================

class AdminOrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: Optional[str] = None


# ============================================
# FILTER PARAMS
# ============================================

class OrderFilterParams(BaseModel):
    status: Optional[OrderStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)