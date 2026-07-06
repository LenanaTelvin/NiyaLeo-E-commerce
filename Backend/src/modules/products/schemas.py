from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal

from .models import ProductStatus, ProductCondition, MediaType, StockAdjustmentReason


# ============================================
# CATEGORY SCHEMAS
# ============================================

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=120, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0

    @field_validator("slug")
    @classmethod
    def lowercase_slug(cls, v: str) -> str:
        return v.lower()


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = Field(None, min_length=2, max_length=120, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    @field_validator("slug")
    @classmethod
    def lowercase_slug(cls, v: Optional[str]) -> Optional[str]:
        return v.lower() if v else v


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    children: List["CategoryResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# Allow self-referential nesting
CategoryResponse.model_rebuild()


# ============================================
# TAG SCHEMAS
# ============================================

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=60, pattern="^[a-z0-9-]+$")

    @field_validator("slug")
    @classmethod
    def lowercase_slug(cls, v: str) -> str:
        return v.lower()


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PRODUCT MEDIA SCHEMAS
# ============================================

class ProductMediaBase(BaseModel):
    url: str = Field(..., max_length=500)
    media_type: MediaType = MediaType.IMAGE
    alt_text: Optional[str] = Field(None, max_length=255)
    is_primary: bool = False
    sort_order: int = 0


class ProductMediaCreate(ProductMediaBase):
    pass


class ProductMediaUpdate(BaseModel):
    alt_text: Optional[str] = Field(None, max_length=255)
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None


class ProductMediaResponse(ProductMediaBase):
    id: int
    product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PRODUCT VARIANT SCHEMAS
# ============================================

class ProductVariantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    price_override: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    stock_quantity: int = Field(0, ge=0)
    is_active: bool = True
    attributes: Optional[dict] = None   # {"color": "red", "size": "L"}
    image_url: Optional[str] = Field(None, max_length=500)


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    price_override: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    attributes: Optional[dict] = None
    image_url: Optional[str] = Field(None, max_length=500)


class ProductVariantResponse(ProductVariantBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PRODUCT SCHEMAS
# ============================================

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=3, max_length=280, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)

    price: Decimal = Field(..., gt=0, decimal_places=2)
    compare_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cost_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    sku: Optional[str] = Field(None, max_length=100)
    stock_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(5, ge=0)
    track_inventory: bool = True
    allow_backorder: bool = False

    weight: Optional[float] = Field(None, ge=0)
    length: Optional[float] = Field(None, ge=0)
    width: Optional[float] = Field(None, ge=0)
    height: Optional[float] = Field(None, ge=0)

    condition: ProductCondition = ProductCondition.NEW
    is_digital: bool = False
    is_featured: bool = False

    category_id: Optional[int] = None
    tag_ids: List[int] = []

    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    extra_data: Optional[dict] = None

    @field_validator("slug")
    @classmethod
    def lowercase_slug(cls, v: str) -> str:
        return v.lower()

    @model_validator(mode="after")
    def compare_price_must_exceed_price(self) -> "ProductBase":
        if self.compare_price is not None and self.compare_price <= self.price:
            raise ValueError("compare_price (original price) must be greater than price (sale price)")
        return self


class ProductCreate(ProductBase):
    # Optionally attach images and variants at creation time
    images: List[ProductMediaCreate] = []
    variants: List[ProductVariantCreate] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=3, max_length=280, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)

    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    compare_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cost_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    sku: Optional[str] = Field(None, max_length=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    track_inventory: Optional[bool] = None
    allow_backorder: Optional[bool] = None

    weight: Optional[float] = Field(None, ge=0)
    length: Optional[float] = Field(None, ge=0)
    width: Optional[float] = Field(None, ge=0)
    height: Optional[float] = Field(None, ge=0)

    condition: Optional[ProductCondition] = None
    is_digital: Optional[bool] = None
    is_featured: Optional[bool] = None

    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    extra_data: Optional[dict] = None

    @field_validator("slug")
    @classmethod
    def lowercase_slug(cls, v: Optional[str]) -> Optional[str]:
        return v.lower() if v else v


class ProductPublishToggle(BaseModel):
    is_published: bool


class ProductStatusUpdate(BaseModel):
    status: ProductStatus


class ProductResponse(ProductBase):
    id: int
    seller_id: int
    status: ProductStatus
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    images: List[ProductMediaResponse] = []
    variants: List[ProductVariantResponse] = []
    tags: List[TagResponse] = []
    category: Optional[CategoryResponse] = None

    # Convenience computed from the images list
    primary_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def set_primary_image(self) -> "ProductResponse":
        primary = next((img for img in self.images if img.is_primary), None)
        if primary is None and self.images:
            primary = self.images[0]
        self.primary_image_url = primary.url if primary else None
        return self


# Lightweight card used in list endpoints (no full description / variants)
class ProductListItem(BaseModel):
    id: int
    seller_id: int
    name: str
    slug: str
    short_description: Optional[str]
    price: Decimal
    compare_price: Optional[Decimal]
    stock_quantity: int
    status: ProductStatus
    is_published: bool
    is_featured: bool
    primary_image_url: Optional[str] = None
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: List[ProductListItem]
    total: int
    page: int
    per_page: int
    total_pages: int


# ============================================
# INVENTORY SCHEMAS
# ============================================

class InventoryAdjust(BaseModel):
    quantity_change: int = Field(..., description="Positive = add stock, negative = remove stock")
    reason: StockAdjustmentReason
    variant_id: Optional[int] = None
    reference_id: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class InventoryLogResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int]
    quantity_before: int
    quantity_change: int
    quantity_after: int
    reason: StockAdjustmentReason
    reference_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    created_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class InventoryLogListResponse(BaseModel):
    items: List[InventoryLogResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ============================================
# FILTER / SEARCH SCHEMAS
# ============================================

class ProductFilterParams(BaseModel):
    status: Optional[ProductStatus] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    search: Optional[str] = None
    low_stock_only: bool = False
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|price|name|stock_quantity)$")
    sort_dir: str = Field("desc", pattern="^(asc|desc)$")
