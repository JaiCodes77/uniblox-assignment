from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models import DiscountCode
from app.services.cart import CartService
from app.services.checkout import CheckoutService
from app.services.stats import StatsService

# Seeded item IDs:
#   1=T-shirt $20, 2=Mug $10, 3=Sticker pack $5, 4=Hoodie $50, 5=Notebook $15
TSHIRT_ID = 1
MUG_ID = 2
HOODIE_ID = 4
NOTEBOOK_ID = 5


def _seed_unused_code(db: Session, code: str, percent: float = 10.0) -> None:
    db.add(DiscountCode(code=code, percent=percent, used=False))
    db.commit()


def test_stats_empty_state_returns_zeros(db: Session, seed_items) -> None:
    assert StatsService.get_stats(db) == {
        "items_purchased": 0,
        "total_revenue": 0.0,
        "discount_codes_issued": 0,
        "total_discount_amount": 0.0,
    }


def test_stats_after_one_order_no_discount(db: Session, seed_items) -> None:
    # T-shirt $20 x 2 + Mug $10 x 1 = $50 subtotal, $50 total
    CartService.add_to_cart(db, "alice", TSHIRT_ID, 2)
    CartService.add_to_cart(db, "alice", MUG_ID, 1)
    CheckoutService().checkout(db, "alice")

    stats = StatsService.get_stats(db)
    assert stats == {
        "items_purchased": 3,
        "total_revenue": 50.0,
        "discount_codes_issued": 0,
        "total_discount_amount": 0.0,
    }


def test_stats_after_orders_with_and_without_discount(
    db: Session, seed_items
) -> None:
    # Issue one discount code (issued count = 1 even before redemption).
    _seed_unused_code(db, "PROMO123", percent=10.0)

    # Order 1: no discount. Hoodie $50 x 1 = $50, total $50.
    CartService.add_to_cart(db, "alice", HOODIE_ID, 1)
    CheckoutService().checkout(db, "alice")

    # Order 2: with discount. T-shirt $20 x 2 + Mug $10 x 1 = $50,
    #   10% off → discount $5, total $45.
    CartService.add_to_cart(db, "bob", TSHIRT_ID, 2)
    CartService.add_to_cart(db, "bob", MUG_ID, 1)
    CheckoutService().checkout(db, "bob", discount_code="PROMO123")

    # Order 3: no discount. Notebook $15 x 1 = $15, total $15.
    CartService.add_to_cart(db, "carol", NOTEBOOK_ID, 1)
    CheckoutService().checkout(db, "carol")

    stats = StatsService.get_stats(db)
    assert stats["items_purchased"] == 1 + (2 + 1) + 1  # = 5
    assert stats["total_revenue"] == pytest.approx(50.0 + 45.0 + 15.0)
    assert stats["discount_codes_issued"] == 1
    assert stats["total_discount_amount"] == pytest.approx(5.0)


def test_items_purchased_sums_quantities_across_orders(
    db: Session, seed_items
) -> None:
    # Order 1: T-shirt x 2 + Mug x 3 = 5 items
    CartService.add_to_cart(db, "u1", TSHIRT_ID, 2)
    CartService.add_to_cart(db, "u1", MUG_ID, 3)
    CheckoutService().checkout(db, "u1")

    # Order 2: Hoodie x 1 + Notebook x 4 = 5 items
    CartService.add_to_cart(db, "u2", HOODIE_ID, 1)
    CartService.add_to_cart(db, "u2", NOTEBOOK_ID, 4)
    CheckoutService().checkout(db, "u2")

    stats = StatsService.get_stats(db)
    assert stats["items_purchased"] == 10
