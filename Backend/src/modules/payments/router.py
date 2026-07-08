from fastapi import APIRouter, Depends, Request

from core.database import get_db
from modules.Auth.dependencies import get_current_user
from modules.Auth.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from . import service, webhooks
from .schemas import MpesaPaymentInitiate, PaymentResponse

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post("/mpesa/initiate", response_model=PaymentResponse)
async def initiate_mpesa(
    data: MpesaPaymentInitiate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.initiate_mpesa_payment(db, current_user.id, data)


@router.get("/mpesa/status/{checkout_request_id}", response_model=PaymentResponse)
async def mpesa_status(
    checkout_request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_payment_status(db, checkout_request_id, current_user.id)


@router.post("/mpesa/callback")
async def mpesa_callback(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    return await webhooks.handle_stk_callback(db, payload)