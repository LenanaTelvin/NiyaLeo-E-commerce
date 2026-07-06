from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import StoreThemeType, StorePageType


# ============================================
# STORE CUSTOMIZATION SCHEMAS
# ============================================

class StoreCustomizationBase(BaseModel):
    """
    Shared fields. NOTE: themed visual fields (colors/fonts) have NO
    hardcoded defaults here on purpose — see StoreCustomizationCreate.
    This base class is also used for *Response*, where every field is
    populated from the DB row, so missing defaults are harmless there.
    """
    theme_type: StoreThemeType = StoreThemeType.MODERN

    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None

    font_family: Optional[str] = None
    heading_font: Optional[str] = None
    font_size: Optional[str] = None

    layout: Optional[Dict[str, Any]] = None
    header_config: Optional[Dict[str, Any]] = None
    footer_config: Optional[Dict[str, Any]] = None
    product_page_config: Optional[Dict[str, Any]] = None

    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    custom_head_html: Optional[str] = None
    custom_body_html: Optional[str] = None

    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    og_image: Optional[HttpUrl] = None

    social_links: Optional[Dict[str, Optional[str]]] = None
    contact_info: Optional[Dict[str, Optional[str]]] = None

    @field_validator(
        'primary_color', 'secondary_color', 'accent_color',
        'background_color', 'text_color'
    )
    @classmethod
    def validate_hex_color(cls, v):
        if v is None:
            return v
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a 7-character hex code, e.g. #4F46E5')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Color must contain valid hex digits after #')
        return v


class StoreCustomizationCreate(StoreCustomizationBase):
    seller_id: int

    @model_validator(mode='after')
    def custom_theme_requires_css(self):
        if self.theme_type == StoreThemeType.CUSTOM and not self.custom_css:
            raise ValueError('Custom theme requires custom_css to be provided')
        return self

class StoreCustomizationUpdate(BaseModel):
    theme_type: Optional[StoreThemeType] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    font_family: Optional[str] = None
    heading_font: Optional[str] = None
    font_size: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    header_config: Optional[Dict[str, Any]] = None
    footer_config: Optional[Dict[str, Any]] = None
    product_page_config: Optional[Dict[str, Any]] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    custom_head_html: Optional[str] = None
    custom_body_html: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    og_image: Optional[HttpUrl] = None
    social_links: Optional[Dict[str, Optional[str]]] = None
    contact_info: Optional[Dict[str, Optional[str]]] = None

    @field_validator(
        'primary_color', 'secondary_color', 'accent_color',
        'background_color', 'text_color'
    )
    @classmethod
    def validate_hex_color(cls, v):
        if v is None:
            return v
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a 7-character hex code, e.g. #4F46E5')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Color must contain valid hex digits after #')
        return v


class StoreCustomizationCreate(StoreCustomizationBase):
    seller_id: int

    @model_validator(mode='after')
    def custom_theme_requires_css(self):
        if self.theme_type == StoreThemeType.CUSTOM and not self.custom_css:
            raise ValueError('Custom theme requires custom_css to be provided')
        return self


class StoreCustomizationResponse(StoreCustomizationBase):
    id: int
    seller_id: int
    theme: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# STORE PAGE SCHEMAS
# ============================================

class StorePageBase(BaseModel):
    title: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255, pattern="^[a-z0-9-]+$")
    page_type: StorePageType = StorePageType.CUSTOM
    content: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    is_published: bool = True
    is_featured: bool = False
    show_in_nav: bool = True
    nav_order: int = 0

class StorePageCreate(StorePageBase):
    store_id: int

class StorePageUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255, pattern="^[a-z0-9-]+$")
    page_type: Optional[StorePageType] = None
    content: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    show_in_nav: Optional[bool] = None
    nav_order: Optional[int] = None

class StorePageResponse(StorePageBase):
    id: int
    store_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# STORE SECTION SCHEMAS
# ============================================

class StoreSectionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    section_type: str = Field(..., max_length=50)
    section_key: Optional[str] = Field(None, max_length=100)
    content: Dict[str, Any] = Field(default_factory=lambda: {
        "heading": None,
        "subheading": None,
        "description": None,
        "image_url": None,
        "video_url": None,
        "button_text": None,
        "button_url": None,
        "items": [],
        "settings": {}
    })
    layout: Dict[str, Any] = Field(default_factory=lambda: {
        "style": "default",
        "alignment": "center",
        "columns": 1,
        "background_color": None,
        "background_image": None,
        "padding": "medium",
        "order": 0
    })
    is_active: bool = True
    is_featured: bool = False
    order: int = 0

class StoreSectionCreate(StoreSectionBase):
    store_id: int

class StoreSectionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    section_type: Optional[str] = Field(None, max_length=50)
    section_key: Optional[str] = Field(None, max_length=100)
    content: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    order: Optional[int] = None

class StoreSectionResponse(StoreSectionBase):
    id: int
    store_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# STORE MEDIA SCHEMAS
# ============================================

class StoreMediaBase(BaseModel):
    media_type: str = Field(..., max_length=50)  # logo, banner, gallery, icon
    title: Optional[str] = Field(None, max_length=255)
    url: HttpUrl
    public_id: Optional[str] = Field(None, max_length=255)
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    alt_text: Optional[str] = Field(None, max_length=255)
    order: int = 0
    is_active: bool = True
    is_default: bool = False

class StoreMediaCreate(StoreMediaBase):
    seller_id: int

class StoreMediaUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    url: Optional[HttpUrl] = None
    alt_text: Optional[str] = Field(None, max_length=255)
    order: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class StoreMediaResponse(StoreMediaBase):
    id: int
    seller_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# STORE THEME SCHEMAS
# ============================================

class StoreThemeConfig(BaseModel):
    """Theme configuration for frontend rendering"""
    store_name: str
    store_slug: str
    store_logo: Optional[str]
    store_banner: Optional[str]
    store_description: Optional[str]

    theme: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    font_family: str
    heading_font: str
    font_size: str

    layout: Dict[str, Any]
    header_config: Dict[str, Any]
    footer_config: Dict[str, Any]
    product_page_config: Dict[str, Any]

    custom_css: Optional[str]
    custom_js: Optional[str]

    meta: Dict[str, Optional[str]]

    social_links: Dict[str, Optional[str]]
    contact_info: Dict[str, Optional[str]]


class StorePreviewData(BaseModel):
    """Data for previewing store theme"""
    theme_type: StoreThemeType
    store_name: str = "Your Store Name"
    store_logo: Optional[HttpUrl] = None
    store_banner: Optional[HttpUrl] = None

    primary_color: str = "#4F46E5"
    secondary_color: str = "#10B981"
    accent_color: str = "#F59E0B"
    background_color: str = "#FFFFFF"
    text_color: str = "#1F2937"

    product_image: Optional[HttpUrl] = None
    product_name: str = "Sample Product"
    product_price: float = 29.99
    description: str = "This is a sample product description for preview purposes."