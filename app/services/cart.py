from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cart, CartItem, Item
from app.services.errors import NotFoundError


class CartService:
    """Cart operations. Each method commits its own unit of work."""

    @staticmethod
    def _get_cart(db: Session, user_id: str) -> Optional[Cart]:
        return db.scalar(select(Cart).where(Cart.user_id == user_id))

    @staticmethod
    def _get_or_create_cart(db: Session, user_id: str) -> Cart:
        cart = CartService._get_cart(db, user_id)
        if cart is None:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.flush()  # populate cart.id without committing the outer txn
        return cart

    @staticmethod
    def add_to_cart(
        db: Session, user_id: str, item_id: int, quantity: int
    ) -> CartItem:
        if quantity <= 0:
            raise ValueError("quantity must be greater than 0")

        item = db.get(Item, item_id)
        if item is None:
            raise NotFoundError(f"item {item_id} not found")

        cart = CartService._get_or_create_cart(db, user_id)

        line = db.get(CartItem, (cart.id, item_id))
        if line is None:
            line = CartItem(cart_id=cart.id, item_id=item_id, quantity=quantity)
            db.add(line)
        else:
            line.quantity += quantity

        db.commit()
        db.refresh(line)
        return line

    @staticmethod
    def get_cart(db: Session, user_id: str) -> Optional[dict]:
        cart = CartService._get_cart(db, user_id)
        if cart is None:
            return None

        items: list[dict] = []
        subtotal = 0.0
        for line in cart.items:
            line_total = line.quantity * line.item.price
            items.append(
                {
                    "item_id": line.item_id,
                    "name": line.item.name,
                    "quantity": line.quantity,
                    "unit_price": line.item.price,
                    "line_total": line_total,
                }
            )
            subtotal += line_total

        return {
            "user_id": user_id,
            "items": items,
            "subtotal": subtotal,
        }

    @staticmethod
    def clear_cart(db: Session, user_id: str) -> None:
        """Wipe all line items from the user's cart. Cart row is preserved.

        Clears the relationship collection so the `delete-orphan` cascade
        emits DELETEs *and* the in-memory `Cart.items` collection stays in
        sync with the database after commit.
        """
        cart = CartService._get_cart(db, user_id)
        if cart is None:
            return
        cart.items.clear()
        db.commit()
