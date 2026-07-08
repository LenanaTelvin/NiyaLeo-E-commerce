import base64
import time
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.exceptions import CommerceException, NotFoundException
from fastapi import status as http_status

from .models import Payment, PaymentStatus, PaymentMethod
from .schemas import MpesaPaymentInitiate
from modules.orders.models import Order, OrderStatus

BASE_URL = (
    "https://sandbox.safaricom.co.ke"
    if settings.MPESA_ENV == "sandbox"
    else "https://api.safaricom.co.ke"
)

_token_cache: dict = {"token": None, "expires_at": 0}


async def _get_access_token() -> str:
    if _token_cache["token"] and _token_cache["expires_at"] > time.time():
        return _token_cache["token"]

    auth = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {auth}"},
            timeout=15,
        )
    resp.raise_for_status()
    data = resp.json()

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + int(data.get("expires_in", 3599)) - 60
    return _token_cache["token"]


def _stk_password_and_timestamp() -> tuple[str, str]:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


async def initiate_mpesa_payment(
    db: AsyncSession,
    user_id: int,
    data: MpesaPaymentInitiate,
) -> Payment:
    order_result = await db.execute(
        select(Order).where(Order.id == data.order_id, Order.user_id == user_id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    if order.status != OrderStatus.PENDING:
        raise CommerceException(
            f"Order is '{order.status}' — payment can only be initiated for a pending order",
            http_status.HTTP_409_CONFLICT,
        )

    amount = int(round(order.total))

    token = await _get_access_token()
    password, timestamp = _stk_password_and_timestamp()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": data.phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": data.phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": order.order_number or f"Order{order.id}",
        "TransactionDesc": f"Payment for order {order.order_number}",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )

    body = resp.json()
    if resp.status_code != 200 or body.get("ResponseCode") != "0":
        raise CommerceException(
            body.get("errorMessage") or body.get("ResponseDescription") or "STK push failed to send",
            http_status.HTTP_502_BAD_GATEWAY,
        )

    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        method=PaymentMethod.MPESA,
        status=PaymentStatus.PENDING,
        amount=amount,
        currency="KES",
        phone_number=data.phone_number,
        merchant_request_id=body.get("MerchantRequestID"),
        checkout_request_id=body.get("CheckoutRequestID"),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payment_status(db: AsyncSession, checkout_request_id: str, user_id: int) -> Payment:
    result = await db.execute(
        select(Payment).where(
            Payment.checkout_request_id == checkout_request_id,
            Payment.user_id == user_id,
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundException("Payment not found")
    return payment