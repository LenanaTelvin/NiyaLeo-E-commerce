from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from core.database import get_db
from modules.sellers.dependencies import get_current_seller_profile
from modules.sellers.models import SellerProfile

from . import service
from . import schemas
from .models import StoreThemeType


# ============================================================
# THREE ROUTERS — register all three in main.py
#
# FIX 1: /me routes and /themes routes were shadowed by
# /{store_slug}/... because FastAPI matches top-to-bottom.
# Splitting into separate routers with explicit prefixes
# guarantees /me and /themes are never treated as a slug.
#
# In main.py add:
#   from modules.stores.router import seller_router, public_router, themes_router
#   app.include_router(themes_router)   # must be first
#   app.include_router(seller_router)
#   app.include_router(public_router)   # slug-based routes last
# ============================================================

themes_router = APIRouter(prefix="/api/v1/store-themes", tags=["Store Themes"])
seller_router = APIRouter(prefix="/api/v1/stores/me",    tags=["Stores - Seller"])
public_router = APIRouter(prefix="/api/v1/stores",       tags=["Stores - Public"])


# ============================================================
# THEMES ROUTER  — no auth, moved off /stores to avoid slug clash
# ============================================================

@themes_router.get("/")
async def list_available_themes():
    """List all available store themes."""
    themes = [
        {
            "id": "modern",
            "name": "Modern",
            "description": "Clean and contemporary design with bold accents",
            "preview_image": "/static/themes/modern-preview.jpg",
            "features": ["Full-width layout", "Mega menu", "Product carousel"],
        },
        {
            "id": "minimalist",
            "name": "Minimalist",
            "description": "Simple, clean, and focused on content",
            "preview_image": "/static/themes/minimalist-preview.jpg",
            "features": ["White space", "Typography focused", "Grid layout"],
        },
        {
            "id": "vibrant",
            "name": "Vibrant",
            "description": "Bold colors and energetic design",
            "preview_image": "/static/themes/vibrant-preview.jpg",
            "features": ["Colorful", "Animations", "Dynamic layout"],
        },
        {
            "id": "elegant",
            "name": "Elegant",
            "description": "Sophisticated and premium feel",
            "preview_image": "/static/themes/elegant-preview.jpg",
            "features": ["Serif fonts", "Gold accents", "Luxury layout"],
        },
        {
            "id": "bold",
            "name": "Bold",
            "description": "Strong typography and impactful design",
            "preview_image": "/static/themes/bold-preview.jpg",
            "features": ["Large typography", "High contrast", "Statement design"],
        },
    ]
    return {"themes": themes}


@themes_router.post("/preview")
async def preview_theme(preview_data: schemas.StorePreviewData):
    """Preview a theme without applying it."""
    theme_data = service.load_theme_template(preview_data.theme_type)

    return {
        "theme": preview_data.theme_type.value,
        "store_name": preview_data.store_name,
        "store_logo": preview_data.store_logo,
        "store_banner": preview_data.store_banner,
        "primary_color":     preview_data.primary_color     or theme_data.get("primary_color",     "#4F46E5"),
        "secondary_color":   preview_data.secondary_color   or theme_data.get("secondary_color",   "#10B981"),
        "accent_color":      preview_data.accent_color      or theme_data.get("accent_color",      "#F59E0B"),
        "background_color":  preview_data.background_color  or theme_data.get("background_color",  "#FFFFFF"),
        "text_color":        preview_data.text_color        or theme_data.get("text_color",        "#1F2937"),
        "layout":            theme_data.get("layout",            {}),
        "header_config":     theme_data.get("header_config",     {}),
        "footer_config":     theme_data.get("footer_config",     {}),
        "product_page_config": theme_data.get("product_page_config", {}),
        "sample_product": {
            "name":        preview_data.product_name,
            "price":       preview_data.product_price,
            "image":       preview_data.product_image,
            "description": preview_data.description,
        },
    }


# ============================================================
# SELLER ROUTER  — all /api/v1/stores/me/... routes
# ============================================================

@seller_router.get("/", response_model=schemas.StoreCustomizationResponse)
async def get_my_store_customization(
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get current seller's store customization."""
    return await service.get_store_customization(db, seller.id)


@seller_router.put("/", response_model=schemas.StoreCustomizationResponse)
async def update_my_store_customization(
    update_data: schemas.StoreCustomizationUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update current seller's store customization."""
    return await service.update_store_customization(db, seller.id, update_data)


@seller_router.post("/apply-theme")
async def apply_theme_to_my_store(
    theme_type: StoreThemeType,
    preserve_colors: bool = True,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply a theme preset to current seller's store.

    Set preserve_colors=false to also reset colors to the theme defaults,
    otherwise the seller's custom brand colors are kept.
    """
    customization = await service.apply_theme_preset(
        db, seller.id, theme_type, preserve_colors=preserve_colors
    )
    return {
        "message": f"Theme {theme_type.value} applied successfully",
        "theme": customization.theme_type.value,
    }


@seller_router.get("/theme-config")
async def get_my_theme_config(
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get current seller's full theme configuration for frontend rendering."""
    return await service.get_store_theme_config(db, seller.id)


# ---- Pages ----------------------------------------------------------

@seller_router.get("/pages", response_model=List[schemas.StorePageResponse])
async def get_my_store_pages(
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get all pages (published and draft) for current seller's store."""
    customization = await service.get_store_customization(db, seller.id)
    return await service.get_store_pages(db, customization.id, only_published=False)


@seller_router.post("/pages", response_model=schemas.StorePageResponse, status_code=status.HTTP_201_CREATED)
async def create_my_store_page(
    page_data: schemas.StorePageCreate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new page for current seller's store.

    FIX 3: store_id is no longer part of StorePageCreate — it is resolved
    server-side from the authenticated seller so it cannot be spoofed, and
    we avoid mutating a Pydantic model (illegal in v2 by default).
    """
    customization = await service.get_store_customization(db, seller.id)
    return await service.create_store_page(db, customization.id, page_data)


@seller_router.get("/pages/{page_id}", response_model=schemas.StorePageResponse)
async def get_my_store_page(
    page_id: int,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific page from current seller's store."""
    customization = await service.get_store_customization(db, seller.id)
    return await service.get_store_page(db, customization.id, page_id)


@seller_router.put("/pages/{page_id}", response_model=schemas.StorePageResponse)
async def update_my_store_page(
    page_id: int,
    update_data: schemas.StorePageUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update a page in current seller's store."""
    customization = await service.get_store_customization(db, seller.id)
    return await service.update_store_page(db, customization.id, page_id, update_data)


@seller_router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_store_page(
    page_id: int,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Delete a page from current seller's store."""
    customization = await service.get_store_customization(db, seller.id)
    await service.delete_store_page(db, customization.id, page_id)


# ---- Sections -------------------------------------------------------

@seller_router.get("/sections", response_model=List[schemas.StoreSectionResponse])
async def get_my_store_sections(
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get all sections (active and inactive) for current seller's store."""
    customization = await service.get_store_customization(db, seller.id)
    return await service.get_store_sections(db, customization.id, only_active=False)


@seller_router.post("/sections", response_model=schemas.StoreSectionResponse, status_code=status.HTTP_201_CREATED)
async def create_my_store_section(
    section_data: schemas.StoreSectionCreate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new section for current seller's store.

    FIX 3: same as pages — store_id resolved server-side, not from request body.
    """
    customization = await service.get_store_customization(db, seller.id)
    return await service.create_store_section(db, customization.id, section_data)


@seller_router.put("/sections/{section_id}", response_model=schemas.StoreSectionResponse)
async def update_my_store_section(
    section_id: int,
    update_data: schemas.StoreSectionUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update a section in current seller's store."""
    customization = await service.get_store_customization(db, seller.id)
    return await service.update_store_section(db, customization.id, section_id, update_data)


@seller_router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_store_section(
    section_id: int,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Delete a section from current seller's store."""
    customization = await service.get_store_customization(db, seller.id)
    await service.delete_store_section(db, customization.id, section_id)


# ---- Media ----------------------------------------------------------

@seller_router.get("/media", response_model=List[schemas.StoreMediaResponse])
async def get_my_store_media(
    media_type: Optional[str] = None,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get all media for current seller's store, optionally filtered by type."""
    return await service.get_store_media(db, seller.id, media_type)


@seller_router.post("/media", response_model=schemas.StoreMediaResponse, status_code=status.HTTP_201_CREATED)
async def add_my_store_media(
    media_data: schemas.StoreMediaCreate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Add media to current seller's store.

    FIX 3: seller_id resolved from auth, not from request body.
    """
    return await service.add_store_media(db, seller.id, media_data)


@seller_router.put("/media/{media_id}", response_model=schemas.StoreMediaResponse)
async def update_my_store_media(
    media_id: int,
    update_data: schemas.StoreMediaUpdate,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update a media item in current seller's store."""
    return await service.update_store_media(db, media_id, seller.id, update_data)


@seller_router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_store_media(
    media_id: int,
    seller: SellerProfile = Depends(get_current_seller_profile),
    db: AsyncSession = Depends(get_db),
):
    """Delete a media item from current seller's store."""
    await service.delete_store_media(db, media_id, seller.id)


# ============================================================
# PUBLIC ROUTER  — slug-based, no auth, always registered last
# ============================================================

@public_router.get("/{store_slug}/theme")
async def get_store_theme(
    store_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get store theme configuration for frontend rendering."""
    from modules.sellers.service import get_seller_profile_by_slug
    seller = await get_seller_profile_by_slug(db, store_slug)
    return await service.get_store_theme_config(db, seller.id)


@public_router.get("/{store_slug}/pages", response_model=List[schemas.StorePageResponse])
async def get_store_pages(
    store_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all published pages for a store."""
    from modules.sellers.service import get_seller_profile_by_slug
    seller = await get_seller_profile_by_slug(db, store_slug)
    customization = await service.get_store_customization(db, seller.id)
    return await service.get_store_pages(db, customization.id, only_published=True)


@public_router.get("/{store_slug}/pages/{page_slug}", response_model=schemas.StorePageResponse)
async def get_store_page_by_slug(
    store_slug: str,
    page_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific published store page by slug."""
    return await service.get_store_page_by_slug(db, store_slug, page_slug)


@public_router.get("/{store_slug}/sections")
async def get_store_sections(
    store_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all active sections for a store."""
    from modules.sellers.service import get_seller_profile_by_slug
    seller = await get_seller_profile_by_slug(db, store_slug)
    customization = await service.get_store_customization(db, seller.id)
    return await service.get_store_sections(db, customization.id, only_active=True)