from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Text, ForeignKey, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class ReviewStatus(str, enum.Enum):
    VISIBLE = "visible"    # Normal, publicly shown
    HIDDEN  = "hidden"     # Hidden by admin (policy violation, spam, etc.)
    FLAGGED = "flagged"    # Reported by users, pending admin review


class Review(Base):
    """
    A customer's review of a product.

    Any authenticated user can review any product — purchase is not
    required, but is_verified_purchase is set automatically if the
    reviewer has a completed order containing this product, and is
    surfaced prominently in the UI so buyers can weight reviews
    accordingly.

    One review per (user, product) — re-reviewing updates the existing
    row rather than creating duplicates.
    """
    __tablename__ = "reviews"

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
    )

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    # Denormalized for fast "all reviews for this seller" queries without a join
    seller_id  = Column(Integer, ForeignKey("seller_profiles.id", ondelete="SET NULL"), nullable=True, index=True)

    rating  = Column(Integer, nullable=False)   # 1-5, enforced in schema + DB check
    title   = Column(String(150), nullable=True)
    body    = Column(Text, nullable=True)

    is_verified_purchase = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(ReviewStatus, native_enum=False), default=ReviewStatus.VISIBLE, nullable=False)

    # Moderation audit trail
    flagged_count    = Column(Integer, default=0)
    moderated_by     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    moderation_reason = Column(String(255), nullable=True)
    moderated_at      = Column(DateTime(timezone=True), nullable=True)

    # Helpful votes — lightweight counter, not a full vote-tracking table
    helpful_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user    = relationship("User",          foreign_keys=[user_id])
    product = relationship("Product",       foreign_keys=[product_id])
    seller  = relationship("SellerProfile", foreign_keys=[seller_id])
    moderator = relationship("User",        foreign_keys=[moderated_by])
    reply   = relationship(
        "ReviewReply", back_populates="review",
        uselist=False, cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Review user={self.user_id} product={self.product_id} rating={self.rating}>"


class ReviewReply(Base):
    """
    A single public reply from the seller to a review on their product.
    One reply per review — re-replying updates the existing row.
    """
    __tablename__ = "review_replies"

    id        = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False)

    body = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    review = relationship("Review", back_populates="reply")
    seller = relationship("SellerProfile", foreign_keys=[seller_id])

    def __repr__(self):
        return f"<ReviewReply review={self.review_id} seller={self.seller_id}>"