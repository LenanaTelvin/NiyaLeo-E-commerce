from sqlalchemy import (
    Column, Enum, Integer, String, Boolean, DateTime, 
    Text, ForeignKey, JSON, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class StoreThemeType(str, enum.Enum):
    MODERN = "modern"
    MINIMALIST = "minimalist"
    VIBRANT = "vibrant"
    ELEGANT = "elegant"
    BOLD = "bold"
    CUSTOM = "custom"


class StorePageType(str, enum.Enum):
    HOME = "home"
    ABOUT = "about"
    CONTACT = "contact"
    FAQ = "faq"
    POLICY = "policy"
    CUSTOM = "custom"


class StoreCustomization(Base):
    """Main store customization settings"""
    __tablename__ = "store_customizations"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Theme
    # NOTE: theme_type is the single source of truth for which preset is applied.
    # Keep this string column only for a human-readable label if you want one;
    # it must always be set from theme_type.value, never independently.
    theme = Column(String(50), default="modern")
    theme_type = Column(Enum(StoreThemeType), default=StoreThemeType.MODERN)
    
    # Colors
    primary_color = Column(String(7), default="#4F46E5")  # Hex color
    secondary_color = Column(String(7), default="#10B981")
    accent_color = Column(String(7), default="#F59E0B")
    background_color = Column(String(7), default="#FFFFFF")
    text_color = Column(String(7), default="#1F2937")
    
    # Typography
    font_family = Column(String(100), default="Inter")
    heading_font = Column(String(100), default="Inter")
    font_size = Column(String(10), default="medium")  # small, medium, large
    
    # Layout
    # FIX: default must be a callable, not a shared dict literal,
    # or every row without an explicit value points at the SAME dict instance.
    layout = Column(JSON, default=lambda: {
        "header_style": "centered",  # centered, left-aligned, right-aligned
        "product_grid_columns": 3,
        "products_per_page": 12,
        "show_sidebar": False,
        "sidebar_position": "left",  # left, right
        "show_banner": True,
        "banner_position": "top",  # top, bottom, full_width
        "footer_style": "simple",  # simple, full, minimal
        "container_width": "large",  # small, medium, large, full
        "show_search": True,
        "show_categories": True,
        "show_featured_products": True,
        "show_testimonials": False,
        "show_trust_badges": True
    })
    
    # Header
    header_config = Column(JSON, default=lambda: {
        "show_logo": True,
        "show_store_name": True,
        "show_navigation": True,
        "show_cart": True,
        "show_search_bar": True,
        "show_wishlist": True,
        "show_login_link": True,
        "logo_size": "medium",  # small, medium, large
        "header_height": "auto",
        "sticky_header": True,
        "transparent_header": False,
        "navigation_style": "horizontal"  # horizontal, vertical, dropdown
    })
    
    # Footer
    footer_config = Column(JSON, default=lambda: {
        "show_social_links": True,
        "show_contact_info": True,
        "show_policy_links": True,
        "show_newsletter": False,
        "show_payment_icons": True,
        "show_copyright": True,
        "columns": 4,
        "footer_style": "dark"  # light, dark, minimal
    })
    
    # Product Page
    product_page_config = Column(JSON, default=lambda: {
        "show_gallery": True,
        "gallery_style": "thumbnails",  # thumbnails, dots, slider
        "show_description": True,
        "show_variants": True,
        "show_quantity_selector": True,
        "show_add_to_cart": True,
        "show_reviews": True,
        "show_related_products": True,
        "related_products_count": 4,
        "show_breadcrumb": True,
        "show_social_share": True
    })
    
    # Custom CSS/JS
    custom_css = Column(Text, nullable=True)
    custom_js = Column(Text, nullable=True)
    custom_head_html = Column(Text, nullable=True)
    custom_body_html = Column(Text, nullable=True)
    
    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    og_image = Column(String(500), nullable=True)
    
    # Social Links
    social_links = Column(JSON, default=lambda: {
        "facebook": None,
        "instagram": None,
        "twitter": None,
        "youtube": None,
        "linkedin": None,
        "tiktok": None,
        "pinterest": None,
        "whatsapp": None,
        "telegram": None,
        "discord": None
    })
    
    # Contact Info
    contact_info = Column(JSON, default=lambda: {
        "phone": None,
        "email": None,
        "address": None,
        "hours": None,
        "map_embed": None
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    seller = relationship("SellerProfile", back_populates="store_customization")
    pages = relationship("StorePage", back_populates="store", cascade="all, delete-orphan")
    sections = relationship("StoreSection", back_populates="store", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<StoreCustomization seller_id={self.seller_id}, theme={self.theme}>"


class StorePage(Base):
    """Custom pages for the store"""
    __tablename__ = "store_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("store_customizations.id", ondelete="CASCADE"), nullable=False)
    
    # Page Info
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    page_type = Column(Enum(StorePageType), default=StorePageType.CUSTOM)
    
    # Content
    content = Column(Text, nullable=True)
    content_json = Column(JSON, nullable=True)  # Rich content with formatting
    
    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    
    # Visibility
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    show_in_nav = Column(Boolean, default=True)
    nav_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    store = relationship("StoreCustomization", back_populates="pages")
    
    def __repr__(self):
        return f"<StorePage {self.title} ({self.slug})>"


class StoreSection(Base):
    """Custom sections for the store homepage"""
    __tablename__ = "store_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("store_customizations.id", ondelete="CASCADE"), nullable=False)
    
    # Section Info
    title = Column(String(255), nullable=True)
    section_type = Column(String(50), nullable=False)  # hero, featured, categories, testimonial, blog, newsletter, custom
    section_key = Column(String(100), unique=True, nullable=True)  # For identifying specific sections
    
    # Content
    # FIX: lambda default (was a shared dict literal)
    content = Column(JSON, default=lambda: {
        "heading": None,
        "subheading": None,
        "description": None,
        "image_url": None,
        "video_url": None,
        "button_text": None,
        "button_url": None,
        "items": [],  # Array of items (products, categories, etc.)
        "settings": {}
    })
    
    # Layout
    # FIX: lambda default (was a shared dict literal)
    layout = Column(JSON, default=lambda: {
        "style": "default",  # default, full_width, boxed, split
        "alignment": "center",  # left, center, right
        "columns": 1,
        "background_color": None,
        "background_image": None,
        "padding": "medium",  # none, small, medium, large
        "order": 0
    })
    
    # Visibility
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    store = relationship("StoreCustomization", back_populates="sections")
    
    def __repr__(self):
        return f"<StoreSection {self.section_type} ({self.order})>"


class StoreMedia(Base):
    """Store media assets (banners, logos, images)"""
    __tablename__ = "store_media"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False)
    
    # Media Info
    media_type = Column(String(50), nullable=False)  # logo, banner, gallery, icon
    title = Column(String(255), nullable=True)
    url = Column(String(500), nullable=False)
    public_id = Column(String(255), nullable=True)  # Cloudinary public ID
    
    # Metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Alt text for accessibility
    alt_text = Column(String(255), nullable=True)
    
    # Sorting
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    seller = relationship("SellerProfile", back_populates="store_media")
    
    def __repr__(self):
        return f"<StoreMedia {self.media_type} - {self.title or self.url[:30]}>"


# NOTE: StoreAnalytics intentionally removed from this module.
# It belongs with the orders/payments domain (populated by checkout/order
# events, not by anything in store customization). Move it to an
# `analytics` or `vendor_dashboard` module when that's built, with its
# own schemas.py and service.py — keeping it here blurs module boundaries.


# Add relationships to SellerProfile
# This will be resolved when SellerProfile is imported