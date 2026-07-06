from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from modules.Auth.models import UserRole
from modules.sellers.models import StoreStatus


# ============================================
# PLATFORM STATS
# ============================================

class UserStats(BaseModel):
    total: int
    active: int
    inactive: int
    verified: int
    new_today: int
    new_this_week: int
    new_this_month: int
    by_role: Dict[str, int]   # {"admin": 1, "seller": 12, "customer": 340}


class SellerStats(BaseModel):
    total: int
    pending: int              # awaiting admin approval ← the gap you flagged
    approved: int
    suspended: int
    rejected: int
    closed: int
    new_this_week: int


class ProductStats(BaseModel):
    total: int
    active: int
    draft: int
    out_of_stock: int
    archived: int
    low_stock: int            # stock_quantity <= low_stock_threshold


class OrderStats(BaseModel):
    """Placeholder — populated with zeros until Orders module is built."""
    total: int = 0
    pending: int = 0
    processing: int = 0
    completed: int = 0
    cancelled: int = 0
    total_revenue: float = 0.0
    revenue_this_month: float = 0.0
    average_order_value: float = 0.0


class CommissionStats(BaseModel):
    """Placeholder — populated with zeros until Payments module is built."""
    total_collected: float = 0.0
    this_month: float = 0.0
    pending_payout: float = 0.0
    platform_rate: float = 0.0


class PlatformStats(BaseModel):
    """Top-level dashboard stats block."""
    users:       UserStats
    sellers:     SellerStats
    products:    ProductStats
    orders:      OrderStats
    commissions: CommissionStats
    generated_at: datetime


# ============================================
# SELLER APPROVAL QUEUE
# ============================================

class PendingSellerItem(BaseModel):
    id: int
    user_id: int
    business_name: str
    business_type: str
    store_name: str
    store_slug: str
    phone_number: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_verified: bool
    kyb_status: Optional[str] = None
    created_at: datetime

    # User info joined in
    user_email: Optional[str] = None
    user_username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PendingSellerListResponse(BaseModel):
    items: List[PendingSellerItem]
    total: int
    page: int
    per_page: int
    total_pages: int


class SellerApprovalAction(BaseModel):
    action: StoreStatus          # APPROVED, REJECTED, SUSPENDED
    reason: Optional[str] = None # required when rejecting or suspending


# ============================================
# USER MANAGEMENT
# ============================================

class AdminUserItem(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    has_seller_profile: bool = False
    seller_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    items: List[AdminUserItem]
    total: int
    page: int
    per_page: int
    total_pages: int


# ============================================
# RECENT ACTIVITY
# ============================================

class ActivityItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    activity_type: str
    activity_category: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecentActivityResponse(BaseModel):
    items: List[ActivityItem]
    total: int


# ============================================
# FULL DASHBOARD RESPONSE
# ============================================

class AdminDashboardResponse(BaseModel):
    stats:           PlatformStats
    pending_sellers: PendingSellerListResponse
    recent_activity: RecentActivityResponse
    generated_at:    datetime