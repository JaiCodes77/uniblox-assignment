from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models import DiscountCode
from app.services.discount import DiscountService

# Seeded StoreConfig: nth_order=3, discount_percent=10
N = 3


def test_generate_not_eligible_with_zero_orders(db: Session, seed_items) -> None:
    result = DiscountService.generate_code(db)

    assert result == {"eligible": False, "reason": "no orders yet"}
    assert db.query(DiscountCode).count() == 0


def test_generate_eligible_at_exactly_N_orders(
    db: Session, seed_items, make_orders
) -> None:
    make_orders(N)

    result = DiscountService.generate_code(db)

    assert result["eligible"] is True
    assert result["percent"] == 10
    code = result["code"]
    assert isinstance(code, str)
    assert len(code) == 8
    assert code == code.upper()

    # The code should be persisted as unused.
    stored = db.get(DiscountCode, code)
    assert stored is not None
    assert stored.used is False
    assert stored.percent == 10


def test_generate_not_eligible_between_multiples(
    db: Session, seed_items, make_orders
) -> None:
    make_orders(N + 1)  # 4 orders, not a multiple of 3

    result = DiscountService.generate_code(db)

    assert result["eligible"] is False
    assert "4" in result["reason"]
    assert "3" in result["reason"]
    assert db.query(DiscountCode).count() == 0


def test_generate_eligible_at_2N(db: Session, seed_items, make_orders) -> None:
    make_orders(2 * N)  # 6 orders, no prior code

    result = DiscountService.generate_code(db)

    assert result["eligible"] is True
    assert result["percent"] == 10
    assert db.query(DiscountCode).count() == 1


def test_generate_twice_in_same_cycle_returns_not_eligible(
    db: Session, seed_items, make_orders
) -> None:
    make_orders(N)

    first = DiscountService.generate_code(db)
    assert first["eligible"] is True

    second = DiscountService.generate_code(db)
    assert second == {"eligible": False, "reason": "unused code already exists"}

    # Still only one code in the DB.
    assert db.query(DiscountCode).count() == 1


def test_generate_again_after_code_used_and_next_cycle(
    db: Session, seed_items, make_orders
) -> None:
    # First cycle: 3 orders → mint code → mark it used.
    make_orders(N)
    first = DiscountService.generate_code(db)
    assert first["eligible"] is True
    DiscountService.mark_used(db, first["code"])

    # Second cycle: 3 more orders (total 6 = 2N).
    make_orders(N)
    second = DiscountService.generate_code(db)

    assert second["eligible"] is True
    assert second["code"] != first["code"]
    assert db.query(DiscountCode).count() == 2


def test_validate_unknown_code_raises(db: Session, seed_items) -> None:
    with pytest.raises(ValueError, match="not found"):
        DiscountService.validate_code(db, "NOPE1234")


def test_validate_used_code_raises(db: Session, seed_items) -> None:
    db.add(
        DiscountCode(
            code="USED1234",
            percent=10,
            used=True,
            used_at=datetime.now(),
        )
    )
    db.commit()

    with pytest.raises(ValueError, match="already used"):
        DiscountService.validate_code(db, "USED1234")


def test_mark_used_sets_flags(db: Session, seed_items) -> None:
    db.add(DiscountCode(code="FRESH123", percent=10, used=False))
    db.commit()

    before = datetime.now()
    DiscountService.mark_used(db, "FRESH123")
    after = datetime.now()

    record = db.get(DiscountCode, "FRESH123")
    assert record is not None
    assert record.used is True
    assert record.used_at is not None
    assert before <= record.used_at <= after

    # Now validate_code should reject it.
    with pytest.raises(ValueError, match="already used"):
        DiscountService.validate_code(db, "FRESH123")
