from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import StoreStatus, BusinessType


# ============================================
# SELLER PROFILE SCHEMAS
# ============================================

class SellerProfileBase(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    business_type: BusinessType = BusinessType.INDIVIDUAL
    business_registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    
    phone_number: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    store_name: str = Field(..., min_length=2, max_length=255)
    store_slug: str = Field(..., min_length=3, max_length=255, pattern="^[a-z0-9-]+$")
    store_description: Optional[str] = None
    store_logo_url: Optional[HttpUrl] = None
    store_banner_url: Optional[HttpUrl] = None
    
    @field_validator('store_slug')
    @classmethod
    def validate_slug(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Store slug must be at least 3 characters')
        return v.lower()


class SellerProfileCreate(SellerProfileBase):
    pass


class SellerProfileUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=2, max_length=255)
    business_type: Optional[BusinessType] = None
    business_registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    store_name: Optional[str] = Field(None, min_length=2, max_length=255)
    store_slug: Optional[str] = Field(None, min_length=3, max_length=255, pattern="^[a-z0-9-]+$")
    store_description: Optional[str] = None
    store_logo_url: Optional[HttpUrl] = None
    store_banner_url: Optional[HttpUrl] = None

    @field_validator('store_slug')
    @classmethod
    def validate_slug(cls, v):
        if v is None:
            return v
        return v.lower()


class SellerProfileResponse(SellerProfileBase):
    id: int
    user_id: int
    status: StoreStatus
    is_active: bool
    is_verified: bool
    custom_commission_rate: Optional[float]
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime]
    suspended_at: Optional[datetime]
    suspension_reason: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# NOTE: StoreSettingBase / Create / Update / Response have been removed.
# Theme/layout/page/media schemas now live exclusively in modules/stores/schemas.py
# (StoreCustomizationResponse, StorePageResponse, StoreSectionResponse, StoreMediaResponse).


# ============================================
# BANK ACCOUNT SCHEMAS
# ============================================

class SellerBankAccountBase(BaseModel):
    account_holder_name: str = Field(..., min_length=2, max_length=255)
    bank_name: str = Field(..., min_length=2, max_length=255)
    account_number: str = Field(..., min_length=4, max_length=50)
    routing_number: Optional[str] = Field(None, max_length=50)
    swift_code: Optional[str] = Field(None, max_length=20)
    iban: Optional[str] = Field(None, max_length=50)
    payment_provider: str = "stripe"
    provider_account_id: Optional[str] = None
    provider_customer_id: Optional[str] = None
    is_default: bool = False


class SellerBankAccountCreate(SellerBankAccountBase):
    pass


class SellerBankAccountUpdate(BaseModel):
    account_holder_name: Optional[str] = Field(None, min_length=2, max_length=255)
    bank_name: Optional[str] = Field(None, min_length=2, max_length=255)
    account_number: Optional[str] = Field(None, min_length=4, max_length=50)
    routing_number: Optional[str] = Field(None, max_length=50)
    swift_code: Optional[str] = Field(None, max_length=20)
    iban: Optional[str] = Field(None, max_length=50)
    provider_account_id: Optional[str] = None
    provider_customer_id: Optional[str] = None
    is_default: Optional[bool] = None


class SellerBankAccountResponse(SellerBankAccountBase):
    id: int
    seller_id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SELLER LIST & SEARCH SCHEMAS
# ============================================

class SellerListFilter(BaseModel):
    status: Optional[StoreStatus] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class SellerListResponse(BaseModel):
    items: List[SellerProfileResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ============================================
# SELLER DASHBOARD STATS
# ============================================

class SellerDashboardStats(BaseModel):
    total_products: int
    total_orders: int
    total_revenue: float
    total_commission: float
    pending_orders: int
    total_earnings: float
    average_rating: float
    total_reviews: int
    recent_orders: List[Dict[str, Any]]
    sales_chart: Dict[str, Any]


# ============================================
# ADMIN SELLER MANAGEMENT SCHEMAS
# ============================================

class SellerStatusUpdate(BaseModel):
    status: StoreStatus
    suspension_reason: Optional[str] = Field(None, max_length=500)


class SellerCommissionUpdate(BaseModel):
    custom_commission_rate: float = Field(..., ge=0, le=100)


class SellerVerificationUpdate(BaseModel):
    is_verified: bool
    verification_notes: Optional[str] = None


# ============================================
# KYB SCHEMAS
# ============================================

class KYBInitiateResponse(BaseModel):
    message: str
    verification_url: str
    inquiry_id: str
    status: str


class KYBStatusResponse(BaseModel):
    status: str
    persona_status: Optional[str] = None
    business_verified: bool = False
    ubo_data: List[Dict[str, Any]] = []
    inquiry_id: Optional[str] = None
    verification_url: Optional[str] = None
    error: Optional[str] = None