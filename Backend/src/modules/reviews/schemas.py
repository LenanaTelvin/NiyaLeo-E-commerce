from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List
from datetime import datetime

from .models import ReviewStatus


# ============================================
# REVIEW REPLY SCHEMAS
# ============================================

class ReviewReplyCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class ReviewReplyUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class ReviewReplyResponse(BaseModel):
    id:         int
    review_id:  int
    seller_id:  int
    body:       str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# REVIEW SCHEMAS
# ============================================

class ReviewCreate(BaseModel):
    product_id: int
    rating:     int = Field(..., ge=1, le=5)
    title:      Optional[str] = Field(None, max_length=150)
    body:       Optional[str] = Field(None, max_length=5000)


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title:  Optional[str] = Field(None, max_length=150)
    body:   Optional[str] = Field(None, max_length=5000)


class ReviewUserSummary(BaseModel):
    """Lightweight reviewer identity — no email/sensitive fields exposed."""
    id:       int
    username: str
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewProductSummary(BaseModel):
    id:   int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    id:                   int
    user_id:              int
    product_id:           int
    seller_id:            Optional[int] = None
    rating:                int
    title:                 Optional[str] = None
    body:                  Optional[str] = None
    is_verified_purchase:  bool
    status:                ReviewStatus
    helpful_count:         int
    created_at:            datetime
    updated_at:            Optional[datetime] = None

    user:    Optional[ReviewUserSummary]    = None
    product: Optional[ReviewProductSummary] = None
    reply:   Optional[ReviewReplyResponse]  = None

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    items:       List[ReviewResponse]
    total:       int
    page:        int
    per_page:    int
    total_pages: int
    # Aggregate stats for the product/seller being viewed
    average_rating:  float
    rating_breakdown: dict   # {"5": 12, "4": 3, "3": 1, "2": 0, "1": 0}


# ============================================
# MODERATION SCHEMAS  (admin)
# ============================================

class ReviewModerationUpdate(BaseModel):
    status: ReviewStatus
    moderation_reason: Optional[str] = Field(None, max_length=255)


class ReviewFlagRequest(BaseModel):
    """A user reporting a review as inappropriate/spam."""
    reason: Optional[str] = Field(None, max_length=255)


# ============================================
# FILTER SCHEMAS
# ============================================

class ReviewFilterParams(BaseModel):
    product_id: Optional[int] = None
    seller_id:  Optional[int] = None
    user_id:    Optional[int] = None
    rating:     Optional[int] = Field(None, ge=1, le=5)
    status:     Optional[ReviewStatus] = None
    verified_only: bool = False
    page:     int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    sort_by:  str = Field("created_at", pattern="^(created_at|rating|helpful_count)$")
    sort_dir: str = Field("desc", pattern="^(asc|desc)$")