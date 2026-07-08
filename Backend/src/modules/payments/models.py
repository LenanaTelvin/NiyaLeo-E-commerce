from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class PaymentMethod(str, enum.Enum):
    MPESA = "mpesa"
    STRIPE = "stripe"  # reserved, not implemented yet


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Payment(Base):
    __tablename__ = "payments"

    id       = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    method   = Column(Enum(PaymentMethod), nullable=False, default=PaymentMethod.MPESA)
    status   = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    amount   = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="KES")
    phone_number = Column(String(15), nullable=True)

    merchant_request_id = Column(String(100), nullable=True, index=True)
    checkout_request_id = Column(String(100), nullable=True, unique=True, index=True)
    mpesa_receipt_number = Column(String(50), nullable=True)

    result_code = Column(Integer, nullable=True)
    result_desc = Column(String(255), nullable=True)
    raw_callback = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    order = relationship("Order")

    def __repr__(self):
        return f"<Payment order_id={self.order_id} {self.method} {self.status}>"