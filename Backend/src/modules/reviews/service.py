from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import status as http_status

from .models import Review, ReviewReply, ReviewStatus
from .schemas import (
    ReviewCreate, ReviewUpdate, ReviewModerationUpdate,
    ReviewReplyCreate, ReviewReplyUpdate, ReviewFilterParams,
)
from modules.products.models import Product
from modules.sellers.models import SellerProfile
from core.exceptions import CommerceException, NotFoundException


# ============================================
# HELPERS
# ============================================

async def _check_verified_purchase(
    db: AsyncSession, user_id: int, product_id: int
) -> bool:
    """
    Check if the user has a completed order containing this product.

    Placeholder until Orders module exists — returns False for now.
    Once Orders is built, replace with a real query against
    OrderItem joined to Order where status=DELIVERED (or similar)
    and order.user_id == user_id and order_item.product_id == product_id.
    """
    # TODO: wire to Orders module once built
    return False


async def _get_review_or_404(
    db: AsyncSession,
    review_id: int,
    load_relations: bool = True,
) -> Review:
    query = select(Review).where(Review.id == review_id)
    if load_relations:
        query = query.options(
            selectinload(Review.user),
            selectinload(Review.product),
            selectinload(Review.reply),
        )
    result = await db.execute(query)
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundException("Review not found")
    return review


def _compute_rating_stats(reviews: list[Review]) -> tuple[float, dict]:
    """Compute average rating and breakdown from a list of visible reviews."""
    if not reviews:
        return 0.0, {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}

    breakdown = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    total = 0
    for r in reviews:
        breakdown[str(r.rating)] += 1
        total += r.rating

    average = round(total / len(reviews), 2)
    return average, breakdown


# ============================================
# REVIEW CRUD
# ============================================

async def create_review(
    db: AsyncSession,
    user_id: int,
    data: ReviewCreate,
) -> Review:
    """
    Create a review. One per (user, product) — if the user already
    reviewed this product, update the existing review instead of
    erroring, since re-reviewing is a normal user action (e.g. updating
    opinion after using the product longer).
    """
    product_result = await db.execute(
        select(Product).where(Product.id == data.product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Product not found")

    existing_result = await db.execute(
        select(Review).where(
            and_(
                Review.user_id == user_id,
                Review.product_id == data.product_id,
            )
        )
    )
    existing = existing_result.scalar_one_or_none()

    is_verified = await _check_verified_purchase(db, user_id, data.product_id)

    if existing:
        existing.rating = data.rating
        existing.title  = data.title
        existing.body   = data.body
        existing.is_verified_purchase = is_verified
        existing.updated_at = datetime.utcnow()
        await db.commit()
        return await _get_review_or_404(db, existing.id)

    review = Review(
        user_id=user_id,
        product_id=data.product_id,
        seller_id=product.seller_id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        is_verified_purchase=is_verified,
        status=ReviewStatus.VISIBLE,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return await _get_review_or_404(db, review.id)


async def get_review(db: AsyncSession, review_id: int) -> Review:
    return await _get_review_or_404(db, review_id)


async def list_reviews(
    db: AsyncSession,
    filters: ReviewFilterParams,
    include_hidden: bool = False,
) -> Dict[str, Any]:
    """
    Paginated review listing with filters, plus aggregate rating stats
    computed over ALL matching visible reviews (not just the current page).
    """
    query = select(Review).options(
        selectinload(Review.user),
        selectinload(Review.product),
        selectinload(Review.reply),
    )

    conditions = []

    if not include_hidden:
        conditions.append(Review.status == ReviewStatus.VISIBLE)
    elif filters.status:
        conditions.append(Review.status == filters.status)

    if filters.product_id is not None:
        conditions.append(Review.product_id == filters.product_id)
    if filters.seller_id is not None:
        conditions.append(Review.seller_id == filters.seller_id)
    if filters.user_id is not None:
        conditions.append(Review.user_id == filters.user_id)
    if filters.rating is not None:
        conditions.append(Review.rating == filters.rating)
    if filters.verified_only:
        conditions.append(Review.is_verified_purchase == True)

    if conditions:
        query = query.where(and_(*conditions))

    # Aggregate stats over the full matching set (before pagination)
    stats_result = await db.execute(query)
    all_matching = list(stats_result.scalars().all())
    average_rating, rating_breakdown = _compute_rating_stats(all_matching)
    total = len(all_matching)

    # Sort + paginate
    sort_col = {
        "created_at":    Review.created_at,
        "rating":        Review.rating,
        "helpful_count": Review.helpful_count,
    }.get(filters.sort_by, Review.created_at)

    query = query.order_by(
        asc(sort_col) if filters.sort_dir == "asc" else desc(sort_col)
    )
    offset = (filters.page - 1) * filters.per_page
    query = query.offset(offset).limit(filters.per_page)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "total_pages": (total + filters.per_page - 1) // filters.per_page,
        "average_rating": average_rating,
        "rating_breakdown": rating_breakdown,
    }


async def update_review(
    db: AsyncSession,
    review_id: int,
    user_id: int,
    data: ReviewUpdate,
) -> Review:
    """Update your own review. Ownership enforced — 404 for non-owners."""
    result = await db.execute(
        select(Review).where(
            and_(Review.id == review_id, Review.user_id == user_id)
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundException("Review not found")

    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(review, field, value)

    review.updated_at = datetime.utcnow()
    await db.commit()

    return await _get_review_or_404(db, review_id)


async def delete_review(
    db: AsyncSession,
    review_id: int,
    user_id: int,
) -> bool:
    """Delete your own review."""
    result = await db.execute(
        select(Review).where(
            and_(Review.id == review_id, Review.user_id == user_id)
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundException("Review not found")

    await db.delete(review)
    await db.commit()
    return True


async def mark_helpful(db: AsyncSession, review_id: int) -> Review:
    """
    Increment the helpful counter.
    Simple counter, not per-user vote tracking — duplicate clicks from
    the same user are not prevented at this layer (acceptable for v1;
    a HelpfulVote table can be added later if abuse becomes an issue).
    """
    review = await _get_review_or_404(db, review_id, load_relations=False)
    review.helpful_count = (review.helpful_count or 0) + 1
    await db.commit()
    return await _get_review_or_404(db, review_id)


# ============================================
# REVIEW REPLIES (seller)
# ============================================

async def add_reply(
    db: AsyncSession,
    review_id: int,
    seller_id: int,
    data: ReviewReplyCreate,
) -> ReviewReply:
    """
    Seller replies to a review on their own product.
    Ownership enforced: the review's seller_id must match the caller's
    seller_id — a seller cannot reply to another seller's reviews.
    One reply per review — re-calling updates the existing reply.
    """
    review = await _get_review_or_404(db, review_id, load_relations=False)

    if review.seller_id != seller_id:
        raise CommerceException(
            "You can only reply to reviews on your own products",
            http_status.HTTP_403_FORBIDDEN,
        )

    existing_result = await db.execute(
        select(ReviewReply).where(ReviewReply.review_id == review_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.body = data.body
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    reply = ReviewReply(
        review_id=review_id,
        seller_id=seller_id,
        body=data.body,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return reply


async def update_reply(
    db: AsyncSession,
    review_id: int,
    seller_id: int,
    data: ReviewReplyUpdate,
) -> ReviewReply:
    result = await db.execute(
        select(ReviewReply).where(
            and_(
                ReviewReply.review_id == review_id,
                ReviewReply.seller_id == seller_id,
            )
        )
    )
    reply = result.scalar_one_or_none()
    if not reply:
        raise NotFoundException("Reply not found")

    reply.body = data.body
    reply.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(reply)
    return reply


async def delete_reply(
    db: AsyncSession,
    review_id: int,
    seller_id: int,
) -> bool:
    result = await db.execute(
        select(ReviewReply).where(
            and_(
                ReviewReply.review_id == review_id,
                ReviewReply.seller_id == seller_id,
            )
        )
    )
    reply = result.scalar_one_or_none()
    if not reply:
        raise NotFoundException("Reply not found")

    await db.delete(reply)
    await db.commit()
    return True


# ============================================
# MODERATION (admin)
# ============================================

async def flag_review(db: AsyncSession, review_id: int) -> Review:
    """
    A user reports a review. Increments flagged_count and auto-transitions
    to FLAGGED status once it crosses a threshold, surfacing it in the
    admin moderation queue without requiring manual patrol of every review.
    """
    review = await _get_review_or_404(db, review_id, load_relations=False)
    review.flagged_count = (review.flagged_count or 0) + 1

    FLAG_THRESHOLD = 3
    if review.flagged_count >= FLAG_THRESHOLD and review.status == ReviewStatus.VISIBLE:
        review.status = ReviewStatus.FLAGGED

    await db.commit()
    return await _get_review_or_404(db, review_id)


async def moderate_review(
    db: AsyncSession,
    review_id: int,
    admin_id: int,
    data: ReviewModerationUpdate,
) -> Review:
    """Admin sets review status (visible/hidden) with an audit trail."""
    review = await _get_review_or_404(db, review_id, load_relations=False)

    review.status = data.status
    review.moderation_reason = data.moderation_reason
    review.moderated_by = admin_id
    review.moderated_at = datetime.utcnow()

    await db.commit()
    return await _get_review_or_404(db, review_id)


async def list_flagged_reviews(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """Admin moderation queue — all reviews currently flagged for review."""
    filters = ReviewFilterParams(
        status=ReviewStatus.FLAGGED,
        page=page,
        per_page=per_page,
    )
    return await list_reviews(db, filters, include_hidden=True)