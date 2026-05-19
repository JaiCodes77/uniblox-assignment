from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cart, DiscountCode, Item, Order
from app.services.cart import CartService
from app.services.checkout import CheckoutService

# Seeded items (insertion order):
#   1=T-shirt $20, 2=Mug $10, 3=Sticker pack $5, 4=Hoodie $50, 5=Notebook $15
TSHIRT_ID = 1
MUG_ID = 2
HOODIE_ID = 4


def _cart_for(db: Session, user_id: str) -> Cart | None:
    return db.scalar(select(Cart).where(Cart.user_id == user_id))


# ---------------------------------------------------------------------------
# Empty / missing cart
# ---------------------------------------------------------------------------


def test_checkout_empty_cart_raises(db: Session, seed_items) -> None:
    svc = CheckoutService()

    # No cart row at all.
    with pytest.raises(ValueError, match="empty"):
        svc.checkout(db, user_id="ghost")

    # Cart exists but is empty (e.g. cleared by a prior checkout).
    CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=1)
    CartService.clear_cart(db, user_id="u1")
    with pytest.raises(ValueError, match="empty"):
        svc.checkout(db, user_id="u1")

    assert db.query(Order).count() == 0


# ---------------------------------------------------------------------------
# Basic math
# ---------------------------------------------------------------------------


def test_checkout_computes_subtotal_and_total_without_code(
    db: Session, seed_items
) -> None:
    # T-shirt $20 x 2 + Mug $10 x 1 = $50
    CartService.add_to_cart(db, "u1", TSHIRT_ID, 2)
    CartService.add_to_cart(db, "u1", MUG_ID, 1)

    order = CheckoutService().checkout(db, user_id="u1")

    assert order.user_id == "u1"
    assert order.subtotal == pytest.approx(50.0)
    assert order.discount_amount == 0.0
    assert order.discount_code is None
    assert order.total == pytest.approx(50.0)

    by_item = {oi.item_id: oi for oi in order.items}
    assert by_item[TSHIRT_ID].quantity == 2
    assert by_item[TSHIRT_ID].unit_price == pytest.approx(20.0)
    assert by_item[MUG_ID].quantity == 1
    assert by_item[MUG_ID].unit_price == pytest.approx(10.0)


def test_checkout_clears_cart(db: Session, seed_items) -> None:
    CartService.add_to_cart(db, "u1", TSHIRT_ID, 2)
    CartService.add_to_cart(db, "u1", MUG_ID, 1)

    CheckoutService().checkout(db, user_id="u1")

    cart = _cart_for(db, "u1")
    assert cart is not None
    assert cart.items == []

    # And the service-level view agrees.
    snapshot = CartService.get_cart(db, "u1")
    assert snapshot is not None
    assert snapshot["items"] == []
    assert snapshot["subtotal"] == 0.0


# ---------------------------------------------------------------------------
# Discount application
# ---------------------------------------------------------------------------


def _seed_unused_code(db: Session, code: str = "GOOD1234", percent: float = 10) -> None:
    db.add(DiscountCode(code=code, percent=percent, used=False))
    db.commit()


def test_checkout_with_valid_code_applies_discount(
    db: Session, seed_items
) -> None:
    _seed_unused_code(db, "PROMO123", percent=10)

    # T-shirt $20 x 2 + Hoodie $50 x 1 + Mug $10 x 1 = $100
    CartService.add_to_cart(db, "u1", TSHIRT_ID, 2)
    CartService.add_to_cart(db, "u1", HOODIE_ID, 1)
    CartService.add_to_cart(db, "u1", MUG_ID, 1)

    order = CheckoutService().checkout(db, "u1", discount_code="PROMO123")

    assert order.subtotal == pytest.approx(100.0)
    assert order.discount_code == "PROMO123"
    assert order.discount_amount == pytest.approx(10.0)
    assert order.total == pytest.approx(90.0)


def test_checkout_with_invalid_code_raises_and_does_not_create_order(
    db: Session, seed_items
) -> None:
    CartService.add_to_cart(db, "u1", TSHIRT_ID, 2)

    with pytest.raises(ValueError, match="not found"):
        CheckoutService().checkout(db, "u1", discount_code="BOGUSXXX")

    # No order persisted, cart untouched.
    assert db.query(Order).count() == 0
    cart_snapshot = CartService.get_cart(db, "u1")
    assert cart_snapshot is not None
    assert cart_snapshot["subtotal"] == pytest.approx(40.0)
    assert len(cart_snapshot["items"]) == 1


def test_checkout_with_used_code_raises(db: Session, seed_items) -> None:
    db.add(
        DiscountCode(
            code="USED1234",
            percent=10,
            used=True,
            used_at=datetime.now(),
        )
    )
    db.commit()

    CartService.add_to_cart(db, "u1", TSHIRT_ID, 2)

    with pytest.raises(ValueError, match="already used"):
        CheckoutService().checkout(db, "u1", discount_code="USED1234")

    assert db.query(Order).count() == 0


def test_checkout_marks_code_as_used(db: Session, seed_items) -> None:
    _seed_unused_code(db, "MARKME12", percent=10)

    CartService.add_to_cart(db, "u1", TSHIRT_ID, 1)

    before = datetime.now()
    CheckoutService().checkout(db, "u1", discount_code="MARKME12")
    after = datetime.now()

    code = db.get(DiscountCode, "MARKME12")
    assert code is not None
    assert code.used is True
    assert code.used_at is not None
    assert before <= code.used_at <= after


# ---------------------------------------------------------------------------
# Price snapshot
# ---------------------------------------------------------------------------


def test_order_items_snapshot_price_at_order_time(
    db: Session, seed_items
) -> None:
    CartService.add_to_cart(db, "u1", TSHIRT_ID, 1)

    order = CheckoutService().checkout(db, "u1")
    original_oi = order.items[0]
    assert original_oi.unit_price == pytest.approx(20.0)

    # Catalog price changes after the fact.
    tshirt = db.get(Item, TSHIRT_ID)
    assert tshirt is not None
    tshirt.price = 99.0
    db.commit()

    # Re-fetch the order from the DB to confirm the snapshot is durable,
    # not just cached in memory.
    db.expire_all()
    refetched = db.get(Order, order.id)
    assert refetched is not None
    assert refetched.items[0].unit_price == pytest.approx(20.0)
    assert refetched.subtotal == pytest.approx(20.0)
    assert refetched.total == pytest.approx(20.0)
