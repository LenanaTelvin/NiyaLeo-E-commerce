from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Text, ForeignKey, Numeric, Enum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SellerOrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    """
    Parent order — one per checkout, regardless of how many sellers
    are involved. Ties to the originating cart and captures a snapshot
    of the shipping address so it's immutable even if the user later
    edits their address book.
    """
    __tablename__ = "orders"

    id             = Column(Integer, primary_key=True, index=True)
    order_number   = Column(String(30), unique=True, index=True, nullable=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    cart_id        = Column(Integer, ForeignKey("carts.id", ondelete="SET NULL"), nullable=True)

    subtotal         = Column(Numeric(12, 2), nullable=False)
    discount_amount  = Column(Numeric(12, 2), nullable=False, default=0)
    shipping_amount  = Column(Numeric(12, 2), nullable=False, default=0)
    total            = Column(Numeric(12, 2), nullable=False)
    currency         = Column(String(3), nullable=False, default="USD")

    # Immutable address snapshot copied from UserAddress at checkout time.
    # Stored as JSON so it survives address edits/deletions without a FK.
    shipping_address = Column(JSON, nullable=True)

    notes       = Column(Text, nullable=True)
    coupon_code = Column(String(50), nullable=True)
    status      = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    seller_orders = relationship(
        "SellerOrder", back_populates="order", cascade="all, delete-orphan"
    )
    status_history = relationship(
        "OrderStatusHistory",
        primaryjoin="and_(OrderStatusHistory.order_id == Order.id, "
                    "OrderStatusHistory.seller_order_id == None)",
        cascade="all, delete-orphan",
        overlaps="status_history"
    )

    def __repr__(self):
        return f"<Order {self.order_number} ({self.status})>"


class SellerOrder(Base):
    """
    Child order — one per seller present in the parent order.
    Carries its own status (the seller manages their own fulfilment),
    commission figures, and tracking info.
    """
    __tablename__ = "seller_orders"

    id        = Column(Integer, primary_key=True, index=True)
    order_id  = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="SET NULL"), nullable=True, index=True)

    subtotal          = Column(Numeric(12, 2), nullable=False)
    commission_rate   = Column(Numeric(5, 2), nullable=False)
    commission_amount = Column(Numeric(12, 2), nullable=False)
    seller_earnings   = Column(Numeric(12, 2), nullable=False)

    status          = Column(Enum(SellerOrderStatus), default=SellerOrderStatus.PENDING, nullable=False)
    tracking_number = Column(String(100), nullable=True)
    shipped_at      = Column(DateTime(timezone=True), nullable=True)
    delivered_at    = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    order  = relationship("Order", back_populates="seller_orders")
    seller = relationship("SellerProfile")
    items  = relationship(
        "SellerOrderItem", back_populates="seller_order", cascade="all, delete-orphan"
    )
    status_history = relationship(
        "OrderStatusHistory",
        primaryjoin="OrderStatusHistory.seller_order_id == SellerOrder.id",
        cascade="all, delete-orphan",
        overlaps="status_history"
    )

    def __repr__(self):
        return f"<SellerOrder order_id={self.order_id} seller_id={self.seller_id} ({self.status})>"


class SellerOrderItem(Base):
    """
    Line item — one row per distinct product/variant in a SellerOrder.
    Snapshots all fields that could change on the product later
    (name, SKU, variant name, price).
    """
    __tablename__ = "seller_order_items"

    id              = Column(Integer, primary_key=True, index=True)
    seller_order_id = Column(Integer, ForeignKey("seller_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id      = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    variant_id      = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)

    product_name = Column(String(255), nullable=False)
    product_sku  = Column(String(100), nullable=True)
    variant_name = Column(String(255), nullable=True)
    unit_price   = Column(Numeric(12, 2), nullable=False)
    quantity     = Column(Integer, nullable=False)
    subtotal     = Column(Numeric(12, 2), nullable=False)

    seller_order = relationship("SellerOrder", back_populates="items")
    product      = relationship("Product")
    variant      = relationship("ProductVariant")

    def __repr__(self):
        return f"<SellerOrderItem {self.product_name} x{self.quantity}>"


class OrderStatusHistory(Base):
    """
    Immutable audit trail for every status transition on both Order and
    SellerOrder. Exactly one of order_id / seller_order_id will be set —
    the other will be NULL. Use the primaryjoin conditions on the
    Order/SellerOrder relationships to filter correctly.
    """
    __tablename__ = "order_status_history"

    id              = Column(Integer, primary_key=True, index=True)
    order_id        = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True)
    seller_order_id = Column(Integer, ForeignKey("seller_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    changed_by      = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    from_status = Column(String(30), nullable=True)
    to_status   = Column(String(30), nullable=False)
    note        = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<OrderStatusHistory {self.from_status} → {self.to_status}>"