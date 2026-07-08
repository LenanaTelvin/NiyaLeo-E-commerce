from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from .models import Payment, PaymentStatus
from modules.orders.models import Order, SellerOrder, OrderStatus, SellerOrderStatus, OrderStatusHistory


def _extract_metadata(callback_metadata: dict | None) -> dict:
    result = {}
    if not callback_metadata:
        return result
    for item in callback_metadata.get("Item", []):
        name = item.get("Name")
        if name:
            result[name] = item.get("Value")
    return result


async def handle_stk_callback(db: AsyncSession, payload: dict) -> dict:
    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    ack = {"ResultCode": 0, "ResultDesc": "Accepted"}

    if not checkout_request_id:
        return ack

    result = await db.execute(
        select(Payment).where(Payment.checkout_request_id == checkout_request_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        return ack

    payment.result_code = result_code
    payment.result_desc = result_desc
    payment.raw_callback = payload

    if result_code == 0:
        meta = _extract_metadata(stk_callback.get("CallbackMetadata"))
        payment.status = PaymentStatus.COMPLETED
        payment.mpesa_receipt_number = meta.get("MpesaReceiptNumber")

        order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
        order = order_result.scalar_one_or_none()
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CONFIRMED
            db.add(OrderStatusHistory(
                order_id=order.id, seller_order_id=None,
                from_status=OrderStatus.PENDING.value, to_status=OrderStatus.CONFIRMED.value,
                changed_by=None, note="Payment confirmed via M-Pesa callback",
            ))

            so_result = await db.execute(select(SellerOrder).where(SellerOrder.order_id == order.id))
            for seller_order in so_result.scalars().all():
                if seller_order.status == SellerOrderStatus.PENDING:
                    seller_order.status = SellerOrderStatus.CONFIRMED
                    seller_order.updated_at = datetime.utcnow()
                    db.add(OrderStatusHistory(
                        order_id=None, seller_order_id=seller_order.id,
                        from_status=SellerOrderStatus.PENDING.value,
                        to_status=SellerOrderStatus.CONFIRMED.value,
                        changed_by=None, note="Payment confirmed via M-Pesa callback",
                    ))
    else:
        payment.status = PaymentStatus.FAILED

    await db.commit()
    return ack