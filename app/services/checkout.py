from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cart, Order, OrderItem
from app.services.discount import DiscountService


class CheckoutService:
    """Atomic checkout: cart → order, in a single transaction.

    Takes a ``DiscountService`` for code validation (injected so tests can
    swap in a fake). Only the *read* path of ``DiscountService`` is used here
    (``validate_code``); the actual ``used`` flip happens inline so it lives
    in the same transaction as the order writes — calling
    ``DiscountService.mark_used`` would commit too early and break atomicity.
    """

    def __init__(
        self,
        discount_service: Union[type[DiscountService], DiscountService] = DiscountService,
    ) -> None:
        self.discount_service = discount_service

    def checkout(
        self,
        db: Session,
        user_id: str,
        discount_code: Optional[str] = None,
    ) -> Order:
        cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
        if cart is None or not cart.items:
            raise ValueError(f"cart for user {user_id!r} is empty")

        try:
            # Snapshot prices + compute subtotal up front.
            line_snapshots: list[tuple[int, int, float]] = []
            subtotal = 0.0
            for line in cart.items:
                unit_price = line.item.price
                line_total = unit_price * line.quantity
                subtotal += line_total
                line_snapshots.append((line.item_id, line.quantity, unit_price))

            # Validate the code BEFORE any writes so an invalid code is a
            # pure read-side failure.
            discount_record = None
            discount_amount = 0.0
            if discount_code:
                discount_record = self.discount_service.validate_code(db, discount_code)
                discount_amount = subtotal * (discount_record.percent / 100.0)

            total = subtotal - discount_amount

            order = Order(
                user_id=user_id,
                subtotal=subtotal,
                discount_code=discount_record.code if discount_record else None,
                discount_amount=discount_amount,
                total=total,
            )
            db.add(order)
            db.flush()  # populate order.id for child rows

            for item_id, qty, unit_price in line_snapshots:
                db.add(
                    OrderItem(
                        order_id=order.id,
                        item_id=item_id,
                        quantity=qty,
                        unit_price=unit_price,
                    )
                )

            # Inline mark-used + cart-clear so everything commits as one unit.
            if discount_record is not None:
                discount_record.used = True
                discount_record.used_at = datetime.now()

            cart.items.clear()

            db.commit()
            db.refresh(order)
            return order
        except Exception:
            db.rollback()
            raise
