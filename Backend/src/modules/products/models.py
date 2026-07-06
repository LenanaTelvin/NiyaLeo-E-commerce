from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Text, ForeignKey, Float, Enum, JSON, Table, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


# ============================================
# ENUMS
# ============================================

class ProductStatus(str, enum.Enum):
    DRAFT = "draft"               # Not yet published
    ACTIVE = "active"             # Live and purchasable
    INACTIVE = "inactive"         # Hidden from buyers
    OUT_OF_STOCK = "out_of_stock" # Auto-set when stock hits 0
    ARCHIVED = "archived"         # Soft-deleted / discontinued


class ProductCondition(str, enum.Enum):
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class StockAdjustmentReason(str, enum.Enum):
    SALE = "sale"                   # Deducted by an order
    RETURN = "return"               # Restored by a return
    RESTOCK = "restock"             # Manual restock by seller
    CORRECTION = "correction"       # Inventory audit correction
    DAMAGE = "damage"               # Written off as damaged
    RESERVED = "reserved"           # Held for pending order


# ============================================
# ASSOCIATION TABLE — Product ↔ Tag (M2M)
# ============================================

product_tags = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id",     Integer, ForeignKey("tags.id",     ondelete="CASCADE"), primary_key=True),
)


# ============================================
# CATEGORY
# ============================================

class Category(Base):
    """Hierarchical product categories (up to 2 levels: parent → child)."""
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False, unique=True)
    slug        = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    image_url   = Column(String(500), nullable=True)
    parent_id   = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    is_active   = Column(Boolean, default=True)
    sort_order  = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Self-referential: one parent → many children
    parent   = relationship("Category", remote_side="Category.id", back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


# ============================================
# TAG
# ============================================

class Tag(Base):
    """Free-form labels for cross-category filtering (e.g. 'sale', 'handmade')."""
    __tablename__ = "tags"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(50),  nullable=False, unique=True)
    slug       = Column(String(60),  nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", secondary=product_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"


# ============================================
# PRODUCT
# ============================================

class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    seller_id   = Column(Integer, ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id",      ondelete="SET NULL"), nullable=True,  index=True)

    # Core fields
    name        = Column(String(255), nullable=False)
    slug        = Column(String(280), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)

    # Pricing
    price         = Column(Numeric(12, 2), nullable=False)
    compare_price = Column(Numeric(12, 2), nullable=True)   # "Was" price for sale display
    cost_price    = Column(Numeric(12, 2), nullable=True)   # For margin tracking (seller only)

    # Inventory (simple track — variants handled separately)
    sku              = Column(String(100), nullable=True, unique=True, index=True)
    stock_quantity   = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=5)       # Triggers low-stock warning
    track_inventory  = Column(Boolean, default=True)       # False = always in stock
    allow_backorder  = Column(Boolean, default=False)

    # Physical attributes
    weight = Column(Float, nullable=True)       # kg
    length = Column(Float, nullable=True)       # cm
    width  = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    # State
    status    = Column(Enum(ProductStatus),    default=ProductStatus.DRAFT)
    condition = Column(Enum(ProductCondition), default=ProductCondition.NEW)
    is_digital   = Column(Boolean, default=False)
    is_featured  = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)

    # SEO / metadata
    meta_title       = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    extra_data       = Column(JSON, nullable=True)   # Flexible attributes (colour, size, etc.)

    # Timestamps
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    seller   = relationship("SellerProfile", back_populates="products")
    category = relationship("Category", back_populates="products")
    tags     = relationship("Tag", secondary=product_tags, back_populates="products")
    images   = relationship("ProductMedia",    back_populates="product", cascade="all, delete-orphan", order_by="ProductMedia.sort_order")
    variants = relationship("ProductVariant",  back_populates="product", cascade="all, delete-orphan")
    inventory_logs = relationship("InventoryLog", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name} ({self.status})>"


# ============================================
# PRODUCT VARIANT
# ============================================

class ProductVariant(Base):
    """
    Optional variants per product (e.g. Size: S / M / L, Color: Red / Blue).
    Each variant can override price, SKU, and stock independently.
    """
    __tablename__ = "product_variants"

    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    name           = Column(String(255), nullable=False)   # e.g. "Red / Large"
    sku            = Column(String(100), nullable=True, unique=True)
    price_override = Column(Numeric(12, 2), nullable=True) # None = use product price
    stock_quantity = Column(Integer, default=0)
    is_active      = Column(Boolean, default=True)
    attributes     = Column(JSON, nullable=True)            # {"color": "red", "size": "L"}
    image_url      = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="variants")

    def __repr__(self):
        return f"<ProductVariant {self.name} (product_id={self.product_id})>"


# ============================================
# PRODUCT MEDIA
# ============================================

class ProductMedia(Base):
    """Images and videos attached to a product."""
    __tablename__ = "product_media"

    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    url        = Column(String(500), nullable=False)
    media_type = Column(Enum(MediaType), default=MediaType.IMAGE)
    alt_text   = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)    # The hero/thumbnail image
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductMedia {self.media_type} (product_id={self.product_id})>"


# ============================================
# INVENTORY LOG
# ============================================

class InventoryLog(Base):
    """Audit trail for every stock change."""
    __tablename__ = "inventory_logs"

    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)

    quantity_before = Column(Integer, nullable=False)
    quantity_change = Column(Integer, nullable=False)   # Negative = reduction
    quantity_after  = Column(Integer, nullable=False)
    reason          = Column(Enum(StockAdjustmentReason), nullable=False)
    reference_id    = Column(String(100), nullable=True)  # e.g. order ID
    notes           = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    product = relationship("Product", back_populates="inventory_logs")
    variant = relationship("ProductVariant")

    def __repr__(self):
        return f"<InventoryLog product={self.product_id} change={self.quantity_change:+d} ({self.reason})>"
