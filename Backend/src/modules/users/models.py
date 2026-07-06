from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    Text, ForeignKey, Enum, JSON, Date, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class UserProfile(Base):
    """Extended user profile information"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    
    phone_number = Column(String(20), nullable=True)
    alternate_email = Column(String(255), nullable=True)
    
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(Gender), default=Gender.PREFER_NOT_TO_SAY)
    
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    currency = Column(String(3), default="USD")
    
    avatar_url = Column(String(500), nullable=True)
    avatar_public_id = Column(String(255), nullable=True)
    
    # FIX: default= must be a callable (lambda), not a shared dict literal —
    # same mutable-default bug we fixed in modules/stores/models.py.
    social_links = Column(JSON, default=lambda: {
        "twitter": None,
        "linkedin": None,
        "github": None,
        "website": None,
        "instagram": None,
        "facebook": None
    })
    
    email_notifications = Column(JSON, default=lambda: {
        "order_updates": True,
        "promotions": True,
        "newsletter": False,
        "security_alerts": True,
        "seller_updates": True
    })
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile user_id={self.user_id}, display_name={self.display_name}>"


class UserAddress(Base):
    """User saved addresses for shipping/billing"""
    __tablename__ = "user_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    address_type = Column(String(20), default="shipping")
    
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    
    recipient_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    is_default = Column(Boolean, default=False)
    label = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="addresses")
    
    def __repr__(self):
        return f"<UserAddress {self.label or self.address_type} - {self.city}>"


class UserActivityLog(Base):
    """Track user activity for audit and analytics"""
    __tablename__ = "user_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    activity_type = Column(String(50), nullable=False)
    activity_category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)
    
    # FIX: renamed from `metadata` — that name collides with SQLAlchemy's
    # reserved declarative attribute (every Base subclass already has a
    # class-level `metadata` referring to the MetaData registry). Declaring
    # a column with that name raises InvalidRequestError at mapper
    # configuration time, i.e. on first import/request. Renamed to
    # `extra_data` and updated every reference in schemas.py and service.py.
    extra_data = Column(JSON, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<UserActivityLog user_id={self.user_id}, type={self.activity_type}>"


class UserDevice(Base):
    """Track user devices for security"""
    __tablename__ = "user_devices"

    # FIX: device_id was `unique=True` on its own, meaning globally unique
    # across ALL users. But register_device() in service.py looks up devices
    # scoped by (user_id, device_id) together — implying two different users
    # should be able to register the same physical device_id (e.g. a shared
    # family tablet). As written, the second user to do so passes the
    # existence check (no row for THEIR user_id) then hits the DB's global
    # unique constraint on insert -> unhandled IntegrityError. Replaced with
    # a composite unique constraint on the actual intended scope.
    __table_args__ = (
        UniqueConstraint('user_id', 'device_id', name='uq_user_device_user_id_device_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    device_id = Column(String(255), nullable=False)  # UUID, unique per-user now (see __table_args__)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)
    browser = Column(String(50), nullable=True)
    
    is_trusted = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_ip = Column(String(45), nullable=True)
    
    push_token = Column(String(500), nullable=True)
    push_provider = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="devices")
    
    def __repr__(self):
        return f"<UserDevice user_id={self.user_id}, device_type={self.device_type}>"


class UserPreference(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    theme = Column(String(20), default="light")
    font_size = Column(String(10), default="medium")
    
    email_frequency = Column(String(20), default="daily")
    push_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    
    profile_visibility = Column(String(20), default="public")
    show_email = Column(Boolean, default=False)
    show_phone = Column(Boolean, default=False)
    
    preferred_language = Column(String(10), default="en")
    preferred_currency = Column(String(3), default="USD")
    
    # FIX: lambda defaults (was shared dict/list literals)
    seller_dashboard_layout = Column(JSON, default=lambda: {})
    product_views = Column(String(20), default="grid")
    custom_preferences = Column(JSON, default=lambda: {})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference user_id={self.user_id}, theme={self.theme}>"


class PasswordResetToken(Base):
    """Store password reset tokens"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="password_reset_tokens")
    
    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id}, expires_at={self.expires_at}>"


class EmailVerificationToken(Base):
    """Store email verification tokens"""
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    token = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="email_verification_tokens")
    
    def __repr__(self):
        return f"<EmailVerificationToken user_id={self.user_id}, email={self.email}>"