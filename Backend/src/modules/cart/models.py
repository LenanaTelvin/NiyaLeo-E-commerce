from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Numeric, Text, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class CartStatus(str, enum.Enum):
    ACTIVE    = "active"      # Current working cart
    MERGED    = "merged"      # Guest cart merged into auth cart on login
    ABANDONED = "abandoned"   # Inactive past TTL (analytics / recovery)
    CONVERTED = "converted"   # Checked out — Order was created from this cart


class Cart(Base):
    """
    One active cart per user at a time.

    Guest carts (user_id=None) are identified by session_id.
    On login, any guest cart is merged into the user's active cart
    and the guest cart is marked MERGED.
    """
    __tablename__ = "carts"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)  # guest carts

    status = Column(Enum(CartStatus), default=CartStatus.ACTIVE, nullable=False)

    # Snapshot of applied coupon (resolved at checkout)
    coupon_code     = Column(String(50),     nullable=True)
    discount_amount = Column(Numeric(12, 2), default=0)

    # Shipping address pre-selected in cart (optional — confirmed at checkout)
    shipping_address_id = Column(
        Integer,
        ForeignKey("user_addresses.id", ondelete="SET NULL"),
        nullable=True,
    )

    notes = Column(Text, nullable=True)   # buyer note to sellers

    expires_at = Column(DateTime(timezone=True), nullable=True)  # guest carts
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user             = relationship("User",        foreign_keys=[user_id])
    shipping_address = relationship("UserAddress", foreign_keys=[shipping_address_id])
    items            = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        order_by="CartItem.created_at",
    )

    def __repr__(self):
        owner = f"user={self.user_id}" if self.user_id else f"session={self.session_id}"
        return f"<Cart {owner} ({self.status})>"


class CartItem(Base):
    """
    A single product (+ optional variant) line in a cart.

    - unit_price is snapshotted at add-time so price changes don't
      silently alter the cart total.
    - The unique constraint prevents duplicate lines — adding the same
      product+variant increments quantity instead.
    """
    __tablename__ = "cart_items"

    __table_args__ = (
        UniqueConstraint(
            "cart_id", "product_id", "variant_id",
            name="uq_cart_item_cart_product_variant",
        ),
    )

    id         = Column(Integer, primary_key=True, index=True)
    cart_id    = Column(Integer, ForeignKey("carts.id",            ondelete="CASCADE"),  nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id",         ondelete="CASCADE"),  nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)

    quantity   = Column(Integer,       nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)   # snapshotted at add-time
    # "Was" price shown as strikethrough in UI
    original_price = Column(Numeric(12, 2), nullable=True)

    # Seller denorm — avoids a join when splitting a mixed-seller cart
    # into per-seller order groups at checkout
    seller_id = Column(
        Integer,
        ForeignKey("seller_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    saved_for_later = Column(Boolean, default=False)  # "save for later" toggle

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cart    = relationship("Cart",           back_populates="items")
    product = relationship("Product",        foreign_keys=[product_id])
    variant = relationship("ProductVariant", foreign_keys=[variant_id])
    seller  = relationship("SellerProfile",  foreign_keys=[seller_id])

    @property
    def subtotal(self):
        from decimal import Decimal
        return Decimal(str(self.unit_price)) * self.quantity

    def __repr__(self):
        return f"<CartItem cart={self.cart_id} product={self.product_id} qty={self.quantity}>"