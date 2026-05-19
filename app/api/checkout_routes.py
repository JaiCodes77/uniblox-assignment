from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api._errors import service_errors
from app.db import get_db
from app.models import Order
from app.schemas import CheckoutIn, OrderItemOut, OrderOut
from app.services.checkout import CheckoutService

router = APIRouter(tags=["checkout"])


def _to_order_out(order: Order) -> OrderOut:
    """Adapt an Order ORM (+ joined items) into the OrderOut wire shape."""
    items = [
        OrderItemOut(
            item_id=oi.item_id,
            name=oi.item.name,
            quantity=oi.quantity,
            unit_price=oi.unit_price,
            line_total=oi.unit_price * oi.quantity,
        )
        for oi in order.items
    ]
    return OrderOut(
        id=order.id,
        user_id=order.user_id,
        items=items,
        subtotal=order.subtotal,
        discount_code=order.discount_code,
        discount_amount=order.discount_amount,
        total=order.total,
        created_at=order.created_at,
    )


@router.post("/checkout", response_model=OrderOut)
def checkout(payload: CheckoutIn, db: Session = Depends(get_db)) -> OrderOut:
    with service_errors():
        order = CheckoutService().checkout(
            db, user_id=payload.user_id, discount_code=payload.discount_code
        )
    return _to_order_out(order)
