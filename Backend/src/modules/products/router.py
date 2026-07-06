from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from core.database import get_db
from modules.Auth.dependencies import get_current_user, get_current_admin
from modules.Auth.models import User
from modules.sellers.dependencies import get_current_seller_profile
from modules.sellers.models import SellerProfile

from . import service
from .schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductListItem, ProductPublishToggle, ProductMediaCreate,
    ProductMediaUpdate, ProductMediaResponse, ProductVariantCreate,
    ProductVariantUpdate, ProductVariantResponse, InventoryAdjust,
    InventoryLogResponse, InventoryLogListResponse, ProductFilterParams,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    TagCreate, TagResponse,
)

# ============================================
# SUB-ROUTERS
# ============================================

# Seller-facing product management
seller_router = APIRouter(
    prefix="/api/v1/seller/products",
    tags=["Seller - Products"],
)

# Public storefront browsing
public_router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products - Public"],
)

# Admin management
admin_router = APIRouter(
    prefix="/api/v1/admin/products",
    tags=["Admin - Products"],
)

# Categories & Tags (shared — public reads, admin writes)
categories_router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Categories & Tags"],
)

tags_router = APIRouter(
    prefix="/api/v1/tags",
    tags=["Categories & Tags"],
)


# ============================================================
# SELLER — PRODUCT CRUD
# ============================================================

@seller_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Create a new product. Starts in DRAFT status."""
    return await service.create_product(db, seller.id, data)


@seller_router.get("/", response_model=ProductListResponse)
async def list_my_products(
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    is_published: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|price|name|stock_quantity)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """List the current seller's products with filters and pagination."""
    from decimal import Decimal
    from .models import ProductStatus as PS

    filters = ProductFilterParams(
        status=PS(status) if status else None,
        category_id=category_id,
        is_published=is_published,
        is_featured=is_featured,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        search=search,
        low_stock_only=low_stock_only,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return await service.list_products(db, filters, seller_id=seller.id)


@seller_router.get("/{product_id}", response_model=ProductResponse)
async def get_my_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Get a single product owned by the current seller."""
    return await service.get_product(db, product_id, seller_id=seller.id)


@seller_router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Update product details."""
    return await service.update_product(db, product_id, seller.id, data)


@seller_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Soft-delete (archive) a product."""
    await service.delete_product(db, product_id, seller.id)


@seller_router.patch("/{product_id}/publish", response_model=ProductResponse)
async def toggle_publish(
    product_id: int,
    data: ProductPublishToggle,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Publish or unpublish a product."""
    return await service.set_product_published(db, product_id, seller.id, data.is_published)


# ============================================================
# SELLER — IMAGES
# ============================================================

@seller_router.post("/{product_id}/images", response_model=ProductMediaResponse, status_code=status.HTTP_201_CREATED)
async def add_image(
    product_id: int,
    data: ProductMediaCreate,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Add an image (or video) to a product."""
    return await service.add_product_image(db, product_id, seller.id, data)


@seller_router.patch("/{product_id}/images/{image_id}", response_model=ProductMediaResponse)
async def update_image(
    product_id: int,
    image_id: int,
    data: ProductMediaUpdate,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Update image metadata (alt text, sort order, primary flag)."""
    return await service.update_product_image(db, image_id, product_id, seller.id, data)


@seller_router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    product_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Remove an image from a product."""
    await service.delete_product_image(db, image_id, product_id, seller.id)


# ============================================================
# SELLER — VARIANTS
# ============================================================

@seller_router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def add_variant(
    product_id: int,
    data: ProductVariantCreate,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Add a variant (e.g. size, colour) to a product."""
    return await service.add_variant(db, product_id, seller.id, data)


@seller_router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_variant(
    product_id: int,
    variant_id: int,
    data: ProductVariantUpdate,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Update a variant."""
    return await service.update_variant(db, variant_id, product_id, seller.id, data)


@seller_router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    product_id: int,
    variant_id: int,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Delete a variant."""
    await service.delete_variant(db, variant_id, product_id, seller.id)


# ============================================================
# SELLER — INVENTORY
# ============================================================

@seller_router.post("/{product_id}/inventory/adjust", response_model=ProductResponse)
async def adjust_inventory(
    product_id: int,
    data: InventoryAdjust,
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
    current_user: User = Depends(get_current_user),
):
    """
    Manually adjust stock.

    - Positive `quantity_change` = add stock (restock, return)
    - Negative `quantity_change` = remove stock (damage, correction)
    """
    return await service.adjust_inventory(db, product_id, seller.id, data, adjusted_by_user_id=current_user.id)


@seller_router.get("/{product_id}/inventory/logs", response_model=InventoryLogListResponse)
async def get_inventory_logs(
    product_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    seller: SellerProfile = Depends(get_current_seller_profile),
):
    """Paginated audit trail of all stock changes for this product."""
    return await service.get_inventory_logs(db, product_id, seller.id, page, per_page)


# ============================================================
# PUBLIC — STOREFRONT BROWSING
# ============================================================

@public_router.get("/", response_model=ProductListResponse)
async def browse_products(
    category_id: Optional[int] = None,
    tag_ids: Optional[List[int]] = Query(None),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    is_featured: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|price|name)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Public product catalogue — returns only active, published products."""
    from decimal import Decimal

    filters = ProductFilterParams(
        category_id=category_id,
        tag_ids=tag_ids,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        search=search,
        is_featured=is_featured,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return await service.list_products(db, filters, public_only=True)


@public_router.get("/{product_id}", response_model=ProductResponse)
async def get_product_detail(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single public product by ID."""
    from .models import ProductStatus as PS
    product = await service.get_product(db, product_id)
    if not product.is_published or product.status not in (PS.ACTIVE,):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ============================================================
# ADMIN — PRODUCT OVERSIGHT
# ============================================================

@admin_router.get("/", response_model=ProductListResponse)
async def admin_list_products(
    seller_id: Optional[int] = None,
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List all products across all sellers (admin view)."""
    from .models import ProductStatus as PS

    filters = ProductFilterParams(
        status=PS(status) if status else None,
        category_id=category_id,
        search=search,
        page=page,
        per_page=per_page,
    )
    return await service.list_products(db, filters, seller_id=seller_id)


@admin_router.get("/{product_id}", response_model=ProductResponse)
async def admin_get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return await service.get_product(db, product_id)


@admin_router.patch("/{product_id}/publish", response_model=ProductResponse)
async def admin_toggle_publish(
    product_id: int,
    data: ProductPublishToggle,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Admin can publish/unpublish any product."""
    product = await service.get_product(db, product_id)
    return await service.set_product_published(db, product_id, product.seller_id, data.is_published)


@admin_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Admin force-archive any product."""
    product = await service.get_product(db, product_id)
    await service.delete_product(db, product_id, product.seller_id)


# ============================================================
# CATEGORIES  (public reads / admin writes)
# ============================================================

@categories_router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List top-level categories with their children."""
    return await service.list_categories(db, include_inactive=include_inactive)


@categories_router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await service.get_category(db, category_id)


@categories_router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return await service.create_category(db, data)


@categories_router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return await service.update_category(db, category_id, data)


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    await service.delete_category(db, category_id)


# ============================================================
# TAGS  (public reads / admin writes)
# ============================================================

@tags_router.get("/", response_model=List[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)):
    return await service.list_tags(db)


@tags_router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return await service.create_tag(db, data)


@tags_router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    await service.delete_tag(db, tag_id)