from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime

from .models import PaymentMethod, PaymentStatus


class MpesaPaymentInitiate(BaseModel):
    order_id: int
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if digits.startswith("0") and len(digits) == 10:
            return "254" + digits[1:]
        if digits.startswith("254") and len(digits) == 12:
            return digits
        if digits.startswith("7") and len(digits) == 9:
            return "254" + digits
        raise ValueError("Enter a valid Safaricom number, e.g. 0712345678")


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    method: PaymentMethod
    status: PaymentStatus
    amount: Decimal
    currency: str
    phone_number: Optional[str]
    checkout_request_id: Optional[str]
    mpesa_receipt_number: Optional[str]
    result_desc: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)