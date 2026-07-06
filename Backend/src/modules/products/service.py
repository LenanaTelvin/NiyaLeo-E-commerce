from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import (
    Product, ProductVariant, ProductMedia, ProductStatus,
    InventoryLog, StockAdjustmentReason, Category, Tag, product_tags
)
from .schemas import (
    ProductCreate, ProductUpdate, ProductMediaCreate, ProductMediaUpdate,
    ProductVariantCreate, ProductVariantUpdate, InventoryAdjust,
    CategoryCreate, CategoryUpdate, TagCreate, ProductFilterParams
)
from modules.Auth.models import User
from core.exceptions import CommerceException, NotFoundException
from fastapi import status as http_status


# ============================================
# HELPERS
# ============================================

async def _get_product_or_404(
    db: AsyncSession,
    product_id: int,
    seller_id: Optional[int] = None,
    load_relations: bool = True
) -> Product:
    """
    Fetch a product by ID.
    If seller_id is provided, also asserts ownership (returns 404 for
    non-owners so we don't leak existence of other sellers' products).
    """
    query = select(Product).where(Product.id == product_id)

    if seller_id is not None:
        query = query.where(Product.seller_id == seller_id)

    if load_relations:
        query = query.options(
            selectinload(Product.images),
            selectinload(Product.variants),
            selectinload(Product.tags),
            selectinload(Product.category),
        )

    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundException("Product not found")

    return product


async def _resolve_tags(db: AsyncSession, tag_ids: List[int]) -> List[Tag]:
    if not tag_ids:
        return []
    result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
    return list(result.scalars().all())


async def _build_product_query(
    filters: ProductFilterParams,
    seller_id: Optional[int] = None,
    public_only: bool = False,
):
    """Return a base SELECT with all filter conditions applied."""
    query = (
        select(Product)
        .options(
            selectinload(Product.images),
            selectinload(Product.tags),
            selectinload(Product.category),
        )
    )

    conditions = []

    if seller_id is not None:
        conditions.append(Product.seller_id == seller_id)

    if public_only:
        conditions.append(Product.status == ProductStatus.ACTIVE)
        conditions.append(Product.is_published == True)

    if filters.status:
        conditions.append(Product.status == filters.status)

    if filters.category_id is not None:
        conditions.append(Product.category_id == filters.category_id)

    if filters.is_published is not None:
        conditions.append(Product.is_published == filters.is_published)

    if filters.is_featured is not None:
        conditions.append(Product.is_featured == filters.is_featured)

    if filters.min_price is not None:
        conditions.append(Product.price >= filters.min_price)

    if filters.max_price is not None:
        conditions.append(Product.price <= filters.max_price)

    if filters.low_stock_only:
        conditions.append(Product.stock_quantity <= Product.low_stock_threshold)
        conditions.append(Product.track_inventory == True)

    if filters.search:
        term = f"%{filters.search}%"
        conditions.append(
            or_(
                Product.name.ilike(term),
                Product.short_description.ilike(term),
                Product.sku.ilike(term),
            )
        )

    if filters.tag_ids:
        # Products must have ALL requested tags (conjunctive filter)
        for tag_id in filters.tag_ids:
            query = query.where(
                Product.id.in_(
                    select(product_tags.c.product_id).where(
                        product_tags.c.tag_id == tag_id
                    )
                )
            )

    if conditions:
        query = query.where(and_(*conditions))

    sort_col = {
        "created_at": Product.created_at,
        "price": Product.price,
        "name": Product.name,
        "stock_quantity": Product.stock_quantity,
    }.get(filters.sort_by, Product.created_at)

    query = query.order_by(
        asc(sort_col) if filters.sort_dir == "asc" else desc(sort_col)
    )

    return query


# ============================================
# PRODUCT CRUD
# ============================================

async def create_product(
    db: AsyncSession,
    seller_id: int,
    data: ProductCreate
) -> Product:
    """Create a product with optional images and variants."""
    # Slug uniqueness
    slug_check = await db.execute(select(Product).where(Product.slug == data.slug))
    if slug_check.scalar_one_or_none():
        raise CommerceException("A product with this slug already exists", http_status.HTTP_409_CONFLICT)

    # SKU uniqueness (if provided)
    if data.sku:
        sku_check = await db.execute(select(Product).where(Product.sku == data.sku))
        if sku_check.scalar_one_or_none():
            raise CommerceException("A product with this SKU already exists", http_status.HTTP_409_CONFLICT)

    tags = await _resolve_tags(db, data.tag_ids)

    product_data = data.model_dump(exclude={"tag_ids", "images", "variants"}, mode="json")
    product = Product(seller_id=seller_id, **product_data)
    product.tags = tags

    db.add(product)
    await db.flush()  # get product.id before adding children

    # Attach images
    for idx, img in enumerate(data.images):
        media = ProductMedia(product_id=product.id, sort_order=idx, **img.model_dump())
        db.add(media)

    # Ensure exactly one primary image
    await _enforce_single_primary(db, product.id)

    # Attach variants
    for variant in data.variants:
        v = ProductVariant(product_id=product.id, **variant.model_dump(mode="json"))
        db.add(v)

    await db.commit()
    await db.refresh(product)

    return await _get_product_or_404(db, product.id)


async def get_product(
    db: AsyncSession,
    product_id: int,
    seller_id: Optional[int] = None
) -> Product:
    return await _get_product_or_404(db, product_id, seller_id=seller_id)


async def list_products(
    db: AsyncSession,
    filters: ProductFilterParams,
    seller_id: Optional[int] = None,
    public_only: bool = False,
) -> Dict[str, Any]:
    """Paginated product listing with filters."""
    query = await _build_product_query(filters, seller_id=seller_id, public_only=public_only)

    # Count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

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
    }


async def update_product(
    db: AsyncSession,
    product_id: int,
    seller_id: int,
    data: ProductUpdate
) -> Product:
    product = await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    update_dict = data.model_dump(exclude_unset=True, mode="json")

    # Slug uniqueness check
    if "slug" in update_dict and update_dict["slug"] != product.slug:
        slug_check = await db.execute(
            select(Product).where(
                and_(Product.slug == update_dict["slug"], Product.id != product_id)
            )
        )
        if slug_check.scalar_one_or_none():
            raise CommerceException("A product with this slug already exists", http_status.HTTP_409_CONFLICT)

    # SKU uniqueness check
    if "sku" in update_dict and update_dict["sku"] and update_dict["sku"] != product.sku:
        sku_check = await db.execute(
            select(Product).where(
                and_(Product.sku == update_dict["sku"], Product.id != product_id)
            )
        )
        if sku_check.scalar_one_or_none():
            raise CommerceException("A product with this SKU already exists", http_status.HTTP_409_CONFLICT)

    # Tags — replace entire set if provided
    if "tag_ids" in update_dict:
        product.tags = await _resolve_tags(db, update_dict.pop("tag_ids"))
    else:
        update_dict.pop("tag_ids", None)

    for field, value in update_dict.items():
        setattr(product, field, value)

    product.updated_at = datetime.utcnow()
    await db.commit()

    return await _get_product_or_404(db, product_id)


async def delete_product(
    db: AsyncSession,
    product_id: int,
    seller_id: int
) -> bool:
    """Soft-delete: archive the product instead of hard-deleting."""
    product = await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)
    product.status = ProductStatus.ARCHIVED
    product.is_published = False
    product.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def set_product_published(
    db: AsyncSession,
    product_id: int,
    seller_id: int,
    is_published: bool
) -> Product:
    product = await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    if is_published and product.status == ProductStatus.ARCHIVED:
        raise CommerceException("Archived products cannot be published. Restore the product first.", http_status.HTTP_400_BAD_REQUEST)

    product.is_published = is_published
    product.status = ProductStatus.ACTIVE if is_published else ProductStatus.INACTIVE
    product.published_at = datetime.utcnow() if is_published else None
    product.updated_at = datetime.utcnow()

    await db.commit()
    return await _get_product_or_404(db, product_id)


# ============================================
# PRODUCT MEDIA
# ============================================

async def _enforce_single_primary(db: AsyncSession, product_id: int) -> None:
    """Ensure at most one image is marked is_primary; picks the first if none set."""
    result = await db.execute(
        select(ProductMedia)
        .where(ProductMedia.product_id == product_id)
        .order_by(ProductMedia.sort_order)
    )
    images: List[ProductMedia] = list(result.scalars().all())
    if not images:
        return

    primaries = [img for img in images if img.is_primary]
    if len(primaries) > 1:
        for img in primaries[1:]:
            img.is_primary = False
    elif len(primaries) == 0:
        images[0].is_primary = True


async def add_product_image(
    db: AsyncSession,
    product_id: int,
    seller_id: int,
    data: ProductMediaCreate
) -> ProductMedia:
    await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    # If this new image is primary, demote all existing primaries
    if data.is_primary:
        await db.execute(
            ProductMedia.__table__.update()
            .where(ProductMedia.product_id == product_id)
            .values(is_primary=False)
        )

    media = ProductMedia(product_id=product_id, **data.model_dump())
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


async def update_product_image(
    db: AsyncSession,
    image_id: int,
    product_id: int,
    seller_id: int,
    data: ProductMediaUpdate
) -> ProductMedia:
    # Ownership: verify product belongs to seller
    await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    result = await db.execute(
        select(ProductMedia).where(
            and_(ProductMedia.id == image_id, ProductMedia.product_id == product_id)
        )
    )
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException("Image not found")

    if data.is_primary:
        await db.execute(
            ProductMedia.__table__.update()
            .where(ProductMedia.product_id == product_id)
            .values(is_primary=False)
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(media, field, value)

    await db.commit()
    await db.refresh(media)
    return media


async def delete_product_image(
    db: AsyncSession,
    image_id: int,
    product_id: int,
    seller_id: int
) -> bool:
    await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    result = await db.execute(
        select(ProductMedia).where(
            and_(ProductMedia.id == image_id, ProductMedia.product_id == product_id)
        )
    )
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException("Image not found")

    was_primary = media.is_primary
    await db.delete(media)
    await db.flush()

    # Reassign primary if we deleted the primary image
    if was_primary:
        await _enforce_single_primary(db, product_id)

    await db.commit()
    return True


# ============================================
# PRODUCT VARIANTS
# ============================================

async def add_variant(
    db: AsyncSession,
    product_id: int,
    seller_id: int,
    data: ProductVariantCreate
) -> ProductVariant:
    await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    if data.sku:
        sku_check = await db.execute(
            select(ProductVariant).where(ProductVariant.sku == data.sku)
        )
        if sku_check.scalar_one_or_none():
            raise CommerceException("A variant with this SKU already exists", http_status.HTTP_409_CONFLICT)

    variant = ProductVariant(product_id=product_id, **data.model_dump(mode="json"))
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return variant


async def update_variant(
    db: AsyncSession,
    variant_id: int,
    product_id: int,
    seller_id: int,
    data: ProductVariantUpdate
) -> ProductVariant:
    await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    result = await db.execute(
        select(ProductVariant).where(
            and_(ProductVariant.id == variant_id, ProductVariant.product_id == product_id)
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundException("Variant not found")

    if data.sku and data.sku != variant.sku:
        sku_check = await db.execute(
            select(ProductVariant).where(
                and_(ProductVariant.sku == data.sku, ProductVariant.id != variant_id)
            )
        )
        if sku_check.scalar_one_or_none():
            raise CommerceException("A variant with this SKU already exists", http_status.HTTP_409_CONFLICT)

    for field, value in data.model_dump(exclude_unset=True, mode="json").items():
        setattr(variant, field, value)

    variant.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(variant)
    return variant


async def delete_variant(
    db: AsyncSession,
    variant_id: int,
    product_id: int,
    seller_id: int
) -> bool:
    await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    result = await db.execute(
        select(ProductVariant).where(
            and_(ProductVariant.id == variant_id, ProductVariant.product_id == product_id)
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundException("Variant not found")

    await db.delete(variant)
    await db.commit()
    return True


# ============================================
# INVENTORY MANAGEMENT
# ============================================

async def adjust_inventory(
    db: AsyncSession,
    product_id: int,
    seller_id: int,
    data: InventoryAdjust,
    adjusted_by_user_id: Optional[int] = None
) -> Product:
    product = await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    if data.variant_id:
        # Adjust variant stock
        result = await db.execute(
            select(ProductVariant).where(
                and_(
                    ProductVariant.id == data.variant_id,
                    ProductVariant.product_id == product_id
                )
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise NotFoundException("Variant not found")

        qty_before = variant.stock_quantity
        new_qty = qty_before + data.quantity_change

        if new_qty < 0 and not product.allow_backorder:
            raise CommerceException(
                f"Insufficient stock. Available: {qty_before}",
                http_status.HTTP_400_BAD_REQUEST
            )

        variant.stock_quantity = max(new_qty, 0)
    else:
        # Adjust product-level stock
        qty_before = product.stock_quantity
        new_qty = qty_before + data.quantity_change

        if new_qty < 0 and not product.allow_backorder:
            raise CommerceException(
                f"Insufficient stock. Available: {qty_before}",
                http_status.HTTP_400_BAD_REQUEST
            )

        product.stock_quantity = max(new_qty, 0)

        # Auto-flip status
        if product.track_inventory:
            if product.stock_quantity == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK:
                product.status = ProductStatus.ACTIVE

    # Write audit log
    log = InventoryLog(
        product_id=product_id,
        variant_id=data.variant_id,
        quantity_before=qty_before,
        quantity_change=data.quantity_change,
        quantity_after=product.stock_quantity if not data.variant_id else variant.stock_quantity,
        reason=data.reason,
        reference_id=data.reference_id,
        notes=data.notes,
        created_by=adjusted_by_user_id,
    )
    db.add(log)

    product.updated_at = datetime.utcnow()
    await db.commit()
    return await _get_product_or_404(db, product_id)


async def get_inventory_logs(
    db: AsyncSession,
    product_id: int,
    seller_id: int,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    await _get_product_or_404(db, product_id, seller_id=seller_id, load_relations=False)

    count_result = await db.execute(
        select(func.count()).where(InventoryLog.product_id == product_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(InventoryLog)
        .where(InventoryLog.product_id == product_id)
        .order_by(desc(InventoryLog.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


# ============================================
# CATEGORIES
# ============================================

async def create_category(db: AsyncSession, data: CategoryCreate) -> Category:
    slug_check = await db.execute(select(Category).where(Category.slug == data.slug))
    if slug_check.scalar_one_or_none():
        raise CommerceException("A category with this slug already exists", http_status.HTTP_409_CONFLICT)

    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def list_categories(db: AsyncSession, include_inactive: bool = False) -> List[Category]:
    query = (
        select(Category)
        .where(Category.parent_id == None)
        .options(selectinload(Category.children))
        .order_by(Category.sort_order, Category.name)
    )
    if not include_inactive:
        query = query.where(Category.is_active == True)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_category(db: AsyncSession, category_id: int) -> Category:
    result = await db.execute(
        select(Category)
        .where(Category.id == category_id)
        .options(selectinload(Category.children))
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundException("Category not found")
    return category


async def update_category(db: AsyncSession, category_id: int, data: CategoryUpdate) -> Category:
    category = await get_category(db, category_id)
    update_dict = data.model_dump(exclude_unset=True)

    if "slug" in update_dict and update_dict["slug"] != category.slug:
        slug_check = await db.execute(
            select(Category).where(
                and_(Category.slug == update_dict["slug"], Category.id != category_id)
            )
        )
        if slug_check.scalar_one_or_none():
            raise CommerceException("A category with this slug already exists", http_status.HTTP_409_CONFLICT)

    for field, value in update_dict.items():
        setattr(category, field, value)

    category.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category_id: int) -> bool:
    category = await get_category(db, category_id)
    await db.delete(category)
    await db.commit()
    return True


# ============================================
# TAGS
# ============================================

async def create_tag(db: AsyncSession, data: TagCreate) -> Tag:
    slug_check = await db.execute(select(Tag).where(Tag.slug == data.slug))
    if slug_check.scalar_one_or_none():
        raise CommerceException("A tag with this slug already exists", http_status.HTTP_409_CONFLICT)

    tag = Tag(**data.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def list_tags(db: AsyncSession) -> List[Tag]:
    result = await db.execute(select(Tag).order_by(Tag.name))
    return list(result.scalars().all())


async def delete_tag(db: AsyncSession, tag_id: int) -> bool:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise NotFoundException("Tag not found")
    await db.delete(tag)
    await db.commit()
    return True
