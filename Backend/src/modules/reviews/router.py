from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from modules.Auth.dependencies import get_current_user, get_current_admin
from modules.Auth.models import User
from modules.sellers.dependencies import get_current_seller_profile
from modules.sellers.models import SellerProfile

from . import service
from .schemas import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewListResponse,
    ReviewModerationUpdate, ReviewReplyCreate, ReviewReplyUpdate,
    ReviewReplyResponse, ReviewFilterParams, ReviewFlagRequest,
)
from .models import ReviewStatus

# ════════════════════════════════════════════════════════════════════
# THREE ROUTERS
#
# from modules.reviews.router import public_router, seller_router, admin_router
# app.include_router(public_router)   # /api/v1/reviews/...
# app.include_router(seller_router)   # /api/v1/seller/reviews/...
# app.include_router(admin_router)    # /api/v1/admin/reviews/...
# ════════════════════════════════════════════════════════════════════

public_router = APIRouter(prefix="/api/v1/reviews",        tags=["Reviews"])
seller_router = APIRouter(prefix="/api/v1/seller/reviews",  tags=["Reviews - Seller"])
admin_router  = APIRouter(prefix="/api/v1/admin/reviews",   tags=["Admin - Reviews"])


# ══════════════════════════════════════════════════════════════════════
# PUBLIC / AUTHENTICATED — anyone can review, anyone can read
# ══════════════════════════════════════════════════════════════════════

@public_router.get("/", response_model=ReviewListResponse)
async def list_reviews(
    product_id: Optional[int] = None,
    seller_id:  Optional[int] = None,
    rating:     Optional[int] = Query(None, ge=1, le=5),
    verified_only: bool = False,
    page:     int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by:  str = Query("created_at", pattern="^(created_at|rating|helpful_count)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse reviews — filter by product or seller to show on a product
    page or seller storefront. Only VISIBLE reviews are returned.
    Includes aggregate average_rating and rating_breakdown for the
    full matching set (not just the current page).
    """
    filters = ReviewFilterParams(
        product_id=product_id,
        seller_id=seller_id,
        rating=rating,
        verified_only=verified_only,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return await service.list_reviews(db, filters)


@public_router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single review by ID."""
    return await service.get_review(db, review_id)


@public_router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a review for a product. Purchase is not required.
    One review per (user, product) — submitting again updates your
    existing review rather than creating a duplicate.
    is_verified_purchase is set automatically based on order history.
    """
    return await service.create_review(db, current_user.id, data)


@public_router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update your own review."""
    return await service.update_review(db, review_id, current_user.id, data)


@public_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete your own review."""
    await service.delete_review(db, review_id, current_user.id)


@public_router.post("/{review_id}/helpful", response_model=ReviewResponse)
async def mark_helpful(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Mark a review as helpful — increments the public helpful counter."""
    return await service.mark_helpful(db, review_id)


@public_router.post("/{review_id}/flag", response_model=ReviewResponse)
async def flag_review(
    review_id: int,
    data: ReviewFlagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Report a review as inappropriate or spam.
    After enough flags, the review auto-transitions to FLAGGED status
    and enters the admin moderation queue.
    """
    return await service.flag_review(db, review_id, current_user.id, data.reason)


# ══════════════════════════════════════════════════════════════════════
# SELLER — reply to reviews on their own products
# ══════════════════════════════════════════════════════════════════════

@seller_router.post(
    "/{review_id}/reply",
    response_model=ReviewReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reply_to_review(
    review_id: int,
    data: ReviewReplyCreate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Reply publicly to a review on your own product.
    One reply per review — calling again updates your existing reply.
    Returns 403 if the review is on a different seller's product.
    """
    return await service.add_reply(db, review_id, seller.id, data)


@seller_router.put("/{review_id}/reply", response_model=ReviewReplyResponse)
async def update_reply(
    review_id: int,
    data: ReviewReplyUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update your existing reply to a review."""
    return await service.update_reply(db, review_id, seller.id, data)


@seller_router.delete("/{review_id}/reply", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reply(
    review_id: int,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Delete your reply to a review."""
    await service.delete_reply(db, review_id, seller.id)


# ══════════════════════════════════════════════════════════════════════
# ADMIN — full moderation
# ══════════════════════════════════════════════════════════════════════

@admin_router.get("/flagged", response_model=ReviewListResponse)
async def list_flagged_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Moderation queue — all reviews currently flagged for review."""
    return await service.list_flagged_reviews(db, page, per_page)


@admin_router.get("/", response_model=ReviewListResponse)
async def admin_list_all_reviews(
    product_id: Optional[int] = None,
    seller_id:  Optional[int] = None,
    user_id:    Optional[int] = None,
    status: Optional[ReviewStatus] = None,
    page:     int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Admin view — see all reviews regardless of status (visible/hidden/flagged)."""
    filters = ReviewFilterParams(
        product_id=product_id,
        seller_id=seller_id,
        user_id=user_id,
        status=status,
        page=page,
        per_page=per_page,
    )
    return await service.list_reviews(db, filters, include_hidden=True)


@admin_router.patch("/{review_id}/moderate", response_model=ReviewResponse)
async def moderate_review(
    review_id: int,
    data: ReviewModerationUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Set a review's status — hide, restore to visible, etc.
    Records who moderated it and why for the audit trail.
    """
    return await service.moderate_review(db, review_id, current_admin.id, data)


@admin_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Admin hard-delete — for severe policy violations (illegal content, etc.)."""
    review = await service.get_review(db, review_id)
    await service.delete_review(db, review_id, review.user_id)