from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    Text, ForeignKey, Float, Enum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class StoreStatus(str, enum.Enum):
    PENDING = "pending"          # Awaiting admin approval
    APPROVED = "approved"        # Approved and active
    SUSPENDED = "suspended"      # Temporarily suspended
    REJECTED = "rejected"        # Rejected by admin
    CLOSED = "closed"            # Seller closed their store


class BusinessType(str, enum.Enum):
    INDIVIDUAL = "individual"
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership"
    LLC = "llc"
    CORPORATION = "corporation"
    NON_PROFIT = "non_profit"


class SellerProfile(Base):
    """Seller profile linked to User model"""
    __tablename__ = "seller_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Business Info
    business_name = Column(String(255), nullable=False)
    business_type = Column(Enum(BusinessType), default=BusinessType.INDIVIDUAL)
    business_registration_number = Column(String(100), nullable=True)
    tax_id = Column(String(50), nullable=True)  # VAT/GST/EIN
    
    # Contact Info
    phone_number = Column(String(20), nullable=True)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Store Info
    store_name = Column(String(255), nullable=False)
    store_slug = Column(String(255), unique=True, index=True, nullable=False)
    store_description = Column(Text, nullable=True)
    store_logo_url = Column(String(500), nullable=True)
    store_banner_url = Column(String(500), nullable=True)
    
    # Status
    status = Column(Enum(StoreStatus), default=StoreStatus.PENDING)
    is_active = Column(Boolean, default=True)
    
    # Commission
    custom_commission_rate = Column(Float, nullable=True)  # Override platform default
    
    # Persona KYB Integration
    persona_account_id = Column(String(100), nullable=True, index=True)
    persona_inquiry_id = Column(String(100), nullable=True)
    kyb_status = Column(String(50), nullable=True)
    kyb_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    suspension_reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="seller_profile")
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    bank_accounts = relationship("SellerBankAccount", back_populates="seller", cascade="all, delete-orphan")
    #payout_requests = relationship("PayoutRequest", back_populates="seller")
    kyb_inquiries = relationship("KYBInquiry", back_populates="seller", cascade="all, delete-orphan")

    # FIX: these two were referenced by modules/stores/models.py's back_populates
    # but never declared here — SQLAlchemy raises InvalidRequestError at mapper
    # configuration time without them. StoreCustomization is now the single
    # source of truth for store theming (StoreSetting has been removed).
    store_customization = relationship(
        "StoreCustomization", back_populates="seller",
        uselist=False, cascade="all, delete-orphan"
    )
    store_media = relationship(
        "StoreMedia", back_populates="seller", cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<SellerProfile {self.business_name} ({self.status})>"


# NOTE: StoreSetting has been removed entirely. It duplicated everything
# modules/stores/models.py's StoreCustomization already does, but with a
# JSON blob for pages instead of a real StorePage table — and the two
# systems were silently diverging. StoreCustomization is the keeper.
# See create_seller_profile / update_seller_status in service.py for
# where StoreCustomization now gets provisioned instead.


class SellerBankAccount(Base):
    """Bank account details for payouts"""
    __tablename__ = "seller_bank_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False)
    
    account_holder_name = Column(String(255), nullable=False)
    bank_name = Column(String(255), nullable=False)
    account_number = Column(String(50), nullable=False)  # Encrypted in production
    routing_number = Column(String(50), nullable=True)
    swift_code = Column(String(20), nullable=True)
    iban = Column(String(50), nullable=True)
    
    payment_provider = Column(String(50), default="stripe")
    provider_account_id = Column(String(255), nullable=True)
    provider_customer_id = Column(String(255), nullable=True)
    
    is_default = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    seller = relationship("SellerProfile", back_populates="bank_accounts")
    
    def __repr__(self):
        return f"<SellerBankAccount {self.bank_name} - {self.account_number[-4:]}>"


# ============================================
# PERSONA KYB MODELS
# ============================================

class KYBInquiryStatus(str, enum.Enum):
    INITIATED = "initiated"
    WAITING = "waiting"
    PROCESSING = "processing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    DECLINED = "declined"


class UBOStatus(str, enum.Enum):
    PENDING = "pending"
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KYBInquiry(Base):
    """Tracks Persona KYB inquiries for sellers."""
    __tablename__ = "kyb_inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False)
    
    persona_account_id = Column(String(100), nullable=False, index=True)
    persona_inquiry_id = Column(String(100), nullable=False, unique=True, index=True)
    
    status = Column(Enum(KYBInquiryStatus), default=KYBInquiryStatus.INITIATED)
    
    business_verified = Column(Boolean, default=False)
    business_verification_data = Column(JSON, nullable=True)
    
    ubo_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    seller = relationship("SellerProfile", back_populates="kyb_inquiries")
    
    def __repr__(self):
        return f"<KYBInquiry {self.persona_inquiry_id} - {self.status}>"


class UBOInvitation(Base):
    """Tracks individual UBO KYC invitations."""
    __tablename__ = "ubo_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    kyb_inquiry_id = Column(Integer, ForeignKey("kyb_inquiries.id", ondelete="CASCADE"), nullable=False)
    
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)
    ownership_percentage = Column(Float, nullable=True)