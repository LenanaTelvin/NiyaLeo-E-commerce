from pydantic import BaseModel, Field, HttpUrl, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .models import Gender


# ============================================
# USER PROFILE SCHEMAS
# ============================================

class UserProfileBase(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None

    phone_number: Optional[str] = Field(None, max_length=20)
    alternate_email: Optional[EmailStr] = None

    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    date_of_birth: Optional[date] = None
    gender: Gender = Gender.PREFER_NOT_TO_SAY

    language: str = "en"
    timezone: str = "UTC"
    currency: str = "USD"

    avatar_url: Optional[HttpUrl] = None

    social_links: Dict[str, Optional[str]] = Field(default_factory=lambda: {
        "twitter": None, "linkedin": None, "github": None,
        "website": None, "instagram": None, "facebook": None,
    })
    email_notifications: Dict[str, bool] = Field(default_factory=lambda: {
        "order_updates": True, "promotions": True, "newsletter": False,
        "security_alerts": True, "seller_updates": True,
    })


class UserProfileCreate(UserProfileBase):
    # FIX: user_id removed — resolved server-side from auth token
    pass


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    alternate_email: Optional[EmailStr] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    social_links: Optional[Dict[str, Optional[str]]] = None
    email_notifications: Optional[Dict[str, bool]] = None


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# USER ADDRESS SCHEMAS
# ============================================

class UserAddressBase(BaseModel):
    address_type: str = "shipping"
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(..., max_length=100)
    recipient_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_default: bool = False
    label: Optional[str] = Field(None, max_length=50)


class UserAddressCreate(UserAddressBase):
    # FIX: user_id removed — resolved server-side from auth token
    pass


class UserAddressUpdate(BaseModel):
    address_type: Optional[str] = None
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    recipient_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_default: Optional[bool] = None
    label: Optional[str] = Field(None, max_length=50)


class UserAddressResponse(UserAddressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# USER PREFERENCES SCHEMAS
# ============================================

class UserPreferenceBase(BaseModel):
    theme: str = "light"
    font_size: str = "medium"
    email_frequency: str = "daily"
    push_enabled: bool = True
    sms_enabled: bool = False
    profile_visibility: str = "public"
    show_email: bool = False
    show_phone: bool = False
    preferred_language: str = "en"
    preferred_currency: str = "USD"
    seller_dashboard_layout: Dict[str, Any] = Field(default_factory=dict)
    product_views: str = "grid"
    custom_preferences: Dict[str, Any] = Field(default_factory=dict)


class UserPreferenceCreate(UserPreferenceBase):
    # FIX: user_id removed — resolved server-side
    pass


class UserPreferenceUpdate(BaseModel):
    theme: Optional[str] = None
    font_size: Optional[str] = None
    email_frequency: Optional[str] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    profile_visibility: Optional[str] = None
    show_email: Optional[bool] = None
    show_phone: Optional[bool] = None
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None
    seller_dashboard_layout: Optional[Dict[str, Any]] = None
    product_views: Optional[str] = None
    custom_preferences: Optional[Dict[str, Any]] = None


class UserPreferenceResponse(UserPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# USER DEVICE SCHEMAS
# ============================================

class UserDeviceBase(BaseModel):
    device_id: str = Field(..., max_length=255)
    device_name: Optional[str] = Field(None, max_length=255)
    device_type: Optional[str] = Field(None, max_length=50)
    os: Optional[str] = Field(None, max_length=50)
    browser: Optional[str] = Field(None, max_length=50)
    is_trusted: bool = False
    push_token: Optional[str] = Field(None, max_length=500)
    push_provider: Optional[str] = Field(None, max_length=50)


class UserDeviceCreate(UserDeviceBase):
    # FIX: user_id removed — resolved server-side from auth token
    ip_address: Optional[str] = None


class UserDeviceUpdate(BaseModel):
    device_name: Optional[str] = Field(None, max_length=255)
    is_trusted: Optional[bool] = None
    push_token: Optional[str] = Field(None, max_length=500)
    push_provider: Optional[str] = Field(None, max_length=50)


class UserDeviceResponse(UserDeviceBase):
    id: int
    user_id: int
    last_login: Optional[datetime] = None
    last_ip: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# USER ACTIVITY LOG SCHEMAS
# ============================================

class UserActivityLogCreate(BaseModel):
    # user_id intentionally absent from request body — passed explicitly
    # by the service layer so anonymous activity can pass None safely.
    activity_type: str = Field(..., max_length=50)
    activity_category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class UserActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    activity_type: str
    activity_category: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# COMPLETE USER RESPONSE
# ============================================

class CompleteUserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    profile: Optional[UserProfileResponse] = None
    preferences: Optional[UserPreferenceResponse] = None
    addresses: Optional[List[UserAddressResponse]] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PASSWORD & EMAIL SCHEMAS
# ============================================

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class EmailVerificationRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserEmailUpdate(BaseModel):
    new_email: EmailStr
    password: str