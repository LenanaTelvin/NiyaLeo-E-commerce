from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from fastapi import status
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os

from .models import (
    StoreCustomization, StorePage, StoreSection, 
    StoreMedia, StoreThemeType, StorePageType
)
from .schemas import (
    StoreCustomizationCreate, StoreCustomizationUpdate,
    StorePageCreate, StorePageUpdate,
    StoreSectionCreate, StoreSectionUpdate,
    StoreMediaCreate, StoreMediaUpdate,
    StoreThemeConfig
)
from modules.sellers.models import SellerProfile, StoreStatus
from core.exceptions import CommerceException, NotFoundException


# ============================================
# THEME TEMPLATE LOADER
# ============================================

def load_theme_template(theme_type: StoreThemeType) -> Dict[str, Any]:
    """
    Load theme template from JSON files in templates directory.
    Falls back to default if theme not found.
    """
    theme_file = f"{theme_type.value}.json"
    theme_path = os.path.join(os.path.dirname(__file__), "templates", theme_file)
    
    try:
        with open(theme_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "primary_color": "#4F46E5",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B",
            "background_color": "#FFFFFF",
            "text_color": "#1F2937",
            "font_family": "Inter",
            "heading_font": "Inter",
            "layout": {
                "header_style": "centered",
                "product_grid_columns": 3,
                "container_width": "large"
            },
            "header_config": {
                "sticky_header": True,
                "navigation_style": "horizontal"
            },
            "footer_config": {
                "footer_style": "dark",
                "columns": 4
            }
        }


# ============================================
# STORE CUSTOMIZATION SERVICE
# ============================================

async def create_store_customization(
    db: AsyncSession,
    customization_data: StoreCustomizationCreate
) -> StoreCustomization:
    """Create store customization for a seller"""
    
    seller_result = await db.execute(
        select(SellerProfile).where(SellerProfile.id == customization_data.seller_id)
    )
    seller = seller_result.scalar_one_or_none()
    if not seller:
        raise NotFoundException("Seller not found")
    
    existing = await db.execute(
        select(StoreCustomization).where(StoreCustomization.seller_id == customization_data.seller_id)
    )
    if existing.scalar_one_or_none():
        raise CommerceException("Store customization already exists", status.HTTP_409_CONFLICT)
    
    theme_data = load_theme_template(customization_data.theme_type)

    # FIX: customization_data's themed fields are now genuinely Optional[None]
    # in schemas.py (no hardcoded defaults), so this merge actually works now —
    # previously every field had a non-None pydantic default, so the template
    # values below were almost never applied.
    customization_dict = customization_data.model_dump(exclude={"seller_id"})
    for key, value in theme_data.items():
        if customization_dict.get(key) is None:
            customization_dict[key] = value

    # FIX: keep `theme` (string label) and `theme_type` (enum) in sync at
    # creation time — previously `theme` was left at whatever default/explicit
    # value came in and could silently mismatch theme_type.
    customization_dict["theme"] = customization_data.theme_type.value
    customization_dict["seller_id"] = customization_data.seller_id

    customization = StoreCustomization(**customization_dict)
    db.add(customization)
    await db.commit()
    await db.refresh(customization)
    
    default_pages = [
        {"title": "About Us", "slug": "about", "page_type": StorePageType.ABOUT, "is_published": True, "show_in_nav": True, "nav_order": 1},
        {"title": "Contact", "slug": "contact", "page_type": StorePageType.CONTACT, "is_published": True, "show_in_nav": True, "nav_order": 2},
        {"title": "FAQ", "slug": "faq", "page_type": StorePageType.FAQ, "is_published": True, "show_in_nav": True, "nav_order": 3},
    ]
    
    for page_data in default_pages:
        page = StorePage(
            store_id=customization.id,
            **page_data
        )
        db.add(page)
    
    await db.commit()
    await db.refresh(customization)
    
    return customization


async def get_store_customization(
    db: AsyncSession,
    seller_id: int
) -> StoreCustomization:
    """Get store customization for a seller"""
    result = await db.execute(
        select(StoreCustomization)
        .where(StoreCustomization.seller_id == seller_id)
        .options(
            selectinload(StoreCustomization.pages),
            selectinload(StoreCustomization.sections)
        )
    )
    customization = result.scalar_one_or_none()
    
    if not customization:
        raise NotFoundException("Store customization not found")
    
    return customization


async def update_store_customization(
    db: AsyncSession,
    seller_id: int,
    update_data: StoreCustomizationUpdate
) -> StoreCustomization:
    """Update store customization"""
    customization = await get_store_customization(db, seller_id)

    update_dict = update_data.model_dump(exclude_unset=True)

    # If theme_type is changing, apply the new template's values FIRST,
    # but only into fields the caller did NOT also explicitly set in this
    # same request — an explicit field in the request should win over the
    # template every time.
    if "theme_type" in update_dict and update_dict["theme_type"] != customization.theme_type:
        theme_data = load_theme_template(update_dict["theme_type"])
        for key, value in theme_data.items():
            if key not in update_dict:
                setattr(customization, key, value)
        # FIX: keep theme label in sync with the new theme_type
        customization.theme = update_dict["theme_type"].value

    for field, value in update_dict.items():
        setattr(customization, field, value)
    
    customization.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(customization)
    
    return customization


async def get_store_theme_config(
    db: AsyncSession,
    seller_id: int
) -> StoreThemeConfig:
    """Get theme configuration for frontend rendering"""
    customization = await get_store_customization(db, seller_id)
    
    seller_result = await db.execute(
        select(SellerProfile).where(SellerProfile.id == seller_id)
    )
    seller = seller_result.scalar_one_or_none()
    
    if not seller:
        raise NotFoundException("Seller not found")
    
    return StoreThemeConfig(
        store_name=seller.store_name,
        store_slug=seller.store_slug,
        store_logo=seller.store_logo_url,
        store_banner=seller.store_banner_url,
        store_description=seller.store_description,
        theme=customization.theme,
        primary_color=customization.primary_color,
        secondary_color=customization.secondary_color,
        accent_color=customization.accent_color,
        background_color=customization.background_color,
        text_color=customization.text_color,
        font_family=customization.font_family,
        heading_font=customization.heading_font,
        font_size=customization.font_size,
        layout=customization.layout,
        header_config=customization.header_config,
        footer_config=customization.footer_config,
        product_page_config=customization.product_page_config,
        custom_css=customization.custom_css,
        custom_js=customization.custom_js,
        meta={
            "title": customization.meta_title or seller.store_name,
            "description": customization.meta_description or seller.store_description,
            "keywords": customization.meta_keywords,
            "og_image": customization.og_image
        },
        social_links=customization.social_links,
        contact_info=customization.contact_info
    )


async def apply_theme_preset(
    db: AsyncSession,
    seller_id: int,
    theme_type: StoreThemeType
) -> StoreCustomization:
    """Apply a theme preset to a store, overwriting current visual config."""
    customization = await get_store_customization(db, seller_id)
    
    theme_data = load_theme_template(theme_type)
    
    for key, value in theme_data.items():
        setattr(customization, key, value)
    
    customization.theme = theme_type.value
    customization.theme_type = theme_type
    customization.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(customization)
    
    return customization


# ============================================
# STORE PAGES SERVICE
# ============================================

async def create_store_page(
    db: AsyncSession,
    page_data: StorePageCreate
) -> StorePage:
    """Create a new store page"""
    
    await get_store_customization_by_id(db, page_data.store_id)
    
    existing = await db.execute(
        select(StorePage).where(
            and_(
                StorePage.store_id == page_data.store_id,
                StorePage.slug == page_data.slug
            )
        )
    )
    if existing.scalar_one_or_none():
        raise CommerceException("Page with this slug already exists", status.HTTP_409_CONFLICT)
    
    page = StorePage(**page_data.model_dump())
    db.add(page)
    await db.commit()
    await db.refresh(page)
    
    return page


async def get_store_pages(
    db: AsyncSession,
    store_id: int,
    only_published: bool = True
) -> List[StorePage]:
    """Get all pages for a store"""
    query = select(StorePage).where(StorePage.store_id == store_id)
    
    if only_published:
        query = query.where(StorePage.is_published == True)
    
    query = query.order_by(StorePage.nav_order, StorePage.created_at)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_store_page(
    db: AsyncSession,
    store_id: int,
    page_id: int
) -> StorePage:
    """Get a specific store page"""
    result = await db.execute(
        select(StorePage).where(
            and_(
                StorePage.store_id == store_id,
                StorePage.id == page_id
            )
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise NotFoundException("Page not found")
    
    return page


async def get_store_page_by_slug(
    db: AsyncSession,
    store_slug: str,
    page_slug: str
) -> StorePage:
    """Get a store page by slug"""
    seller_result = await db.execute(
        select(SellerProfile).where(
            and_(
                SellerProfile.store_slug == store_slug,
                SellerProfile.status == StoreStatus.APPROVED,
                SellerProfile.is_active == True
            )
        )
    )
    seller = seller_result.scalar_one_or_none()
    
    if not seller:
        raise NotFoundException("Store not found")
    
    customization = await get_store_customization(db, seller.id)
    
    result = await db.execute(
        select(StorePage).where(
            and_(
                StorePage.store_id == customization.id,
                StorePage.slug == page_slug,
                StorePage.is_published == True
            )
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise NotFoundException("Page not found")
    
    return page


async def update_store_page(
    db: AsyncSession,
    store_id: int,
    page_id: int,
    update_data: StorePageUpdate
) -> StorePage:
    """Update a store page"""
    page = await get_store_page(db, store_id, page_id)
    
    update_dict = update_data.model_dump(exclude_unset=True)

    if "slug" in update_dict and update_dict["slug"] != page.slug:
        existing = await db.execute(
            select(StorePage).where(
                and_(
                    StorePage.store_id == store_id,
                    StorePage.slug == update_dict["slug"],
                    StorePage.id != page_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise CommerceException("Page with this slug already exists", status.HTTP_409_CONFLICT)
    
    for field, value in update_dict.items():
        setattr(page, field, value)
    
    page.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(page)
    
    return page


async def delete_store_page(
    db: AsyncSession,
    store_id: int,
    page_id: int
) -> bool:
    """Delete a store page"""
    page = await get_store_page(db, store_id, page_id)
    await db.delete(page)
    await db.commit()
    return True


# ============================================
# STORE SECTIONS SERVICE
# ============================================

async def create_store_section(
    db: AsyncSession,
    section_data: StoreSectionCreate
) -> StoreSection:
    """Create a new store section"""
    
    await get_store_customization_by_id(db, section_data.store_id)
    
    if section_data.section_key:
        existing = await db.execute(
            select(StoreSection).where(
                and_(
                    StoreSection.store_id == section_data.store_id,
                    StoreSection.section_key == section_data.section_key
                )
            )
        )
        if existing.scalar_one_or_none():
            raise CommerceException("Section with this key already exists", status.HTTP_409_CONFLICT)
    
    section = StoreSection(**section_data.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    
    return section


async def get_store_sections(
    db: AsyncSession,
    store_id: int,
    only_active: bool = True
) -> List[StoreSection]:
    """Get all sections for a store"""
    query = select(StoreSection).where(StoreSection.store_id == store_id)
    
    if only_active:
        query = query.where(StoreSection.is_active == True)
    
    query = query.order_by(StoreSection.order, StoreSection.created_at)
    
    result = await db.execute(query)
    return result.scalars().all()


async def update_store_section(
    db: AsyncSession,
    store_id: int,
    section_id: int,
    update_data: StoreSectionUpdate
) -> StoreSection:
    """Update a store section"""
    result = await db.execute(
        select(StoreSection).where(
            and_(
                StoreSection.store_id == store_id,
                StoreSection.id == section_id
            )
        )
    )
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundException("Section not found")
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    
    section.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(section)
    
    return section


async def delete_store_section(
    db: AsyncSession,
    store_id: int,
    section_id: int
) -> bool:
    """Delete a store section"""
    result = await db.execute(
        select(StoreSection).where(
            and_(
                StoreSection.store_id == store_id,
                StoreSection.id == section_id
            )
        )
    )
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundException("Section not found")
    
    await db.delete(section)
    await db.commit()
    return True


# ============================================
# STORE MEDIA SERVICE
# ============================================

async def add_store_media(
    db: AsyncSession,
    media_data: StoreMediaCreate
) -> StoreMedia:
    """Add media to store"""
    
    seller_result = await db.execute(
        select(SellerProfile).where(SellerProfile.id == media_data.seller_id)
    )
    if not seller_result.scalar_one_or_none():
        raise NotFoundException("Seller not found")
    
    if media_data.is_default:
        await db.execute(
            StoreMedia.__table__.update()
            .where(
                and_(
                    StoreMedia.seller_id == media_data.seller_id,
                    StoreMedia.media_type == media_data.media_type,
                    StoreMedia.is_default == True
                )
            )
            .values(is_default=False)
        )
    
    # FIX: HttpUrl (pydantic v2) must be cast to str before SQLAlchemy
    # writes it to a String column — passing the HttpUrl object directly
    # can fail or store a repr instead of the plain URL string depending
    # on driver. model_dump(mode="json") serializes HttpUrl -> str safely.
    media = StoreMedia(**media_data.model_dump(mode="json"))
    db.add(media)
    await db.commit()
    await db.refresh(media)
    
    return media


async def get_store_media(
    db: AsyncSession,
    seller_id: int,
    media_type: Optional[str] = None
) -> List[StoreMedia]:
    """Get store media"""
    query = select(StoreMedia).where(StoreMedia.seller_id == seller_id)
    
    if media_type:
        query = query.where(StoreMedia.media_type == media_type)
    
    query = query.order_by(StoreMedia.order, StoreMedia.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


async def update_store_media(
    db: AsyncSession,
    media_id: int,
    seller_id: int,
    update_data: StoreMediaUpdate
) -> StoreMedia:
    """Update store media"""
    result = await db.execute(
        select(StoreMedia).where(
            and_(
                StoreMedia.id == media_id,
                StoreMedia.seller_id == seller_id
            )
        )
    )
    media = result.scalar_one_or_none()
    
    if not media:
        raise NotFoundException("Media not found")
    
    if update_data.is_default:
        await db.execute(
            StoreMedia.__table__.update()
            .where(
                and_(
                    StoreMedia.seller_id == seller_id,
                    StoreMedia.media_type == media.media_type,
                    StoreMedia.is_default == True,
                    StoreMedia.id != media_id
                )
            )
            .values(is_default=False)
        )
    
    for field, value in update_data.model_dump(exclude_unset=True, mode="json").items():
        setattr(media, field, value)
    
    media.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(media)
    
    return media


async def delete_store_media(
    db: AsyncSession,
    media_id: int,
    seller_id: int
) -> bool:
    """Delete store media"""
    result = await db.execute(
        select(StoreMedia).where(
            and_(
                StoreMedia.id == media_id,
                StoreMedia.seller_id == seller_id
            )
        )
    )
    media = result.scalar_one_or_none()
    
    if not media:
        raise NotFoundException("Media not found")
    
    await db.delete(media)
    await db.commit()
    return True


# ============================================
# INTERNAL HELPER
# ============================================

async def get_store_customization_by_id(
    db: AsyncSession,
    store_id: int
) -> StoreCustomization:
    """
    Look up a StoreCustomization by its own primary key (not seller_id).
    NOTE: this fixes a real bug — create_store_page/create_store_section
    previously called get_store_customization(db, page_data.store_id),
    but get_store_customization filters by seller_id. store_id IS the
    StoreCustomization's own id, not a seller id, so that existence
    check was silently querying the wrong column and would raise
    NotFoundException for every valid store_id.
    """
    result = await db.execute(
        select(StoreCustomization).where(StoreCustomization.id == store_id)
    )
    customization = result.scalar_one_or_none()
    if not customization:
        raise NotFoundException("Store customization not found")
    return customization