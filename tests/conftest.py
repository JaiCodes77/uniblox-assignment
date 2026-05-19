from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Importing models registers them on Base.metadata before create_all runs.
from app import models  # noqa: F401
from app.db import (
    DEFAULT_DISCOUNT_PERCENT,
    DEFAULT_NTH_ORDER,
    SEED_ITEMS,
    Base,
)
from app.models import Item, Order, StoreConfig


@pytest.fixture
def db() -> Iterator[Session]:
    """A fresh in-memory SQLite session per test.

    StaticPool keeps the single in-memory database alive across the session's
    connections (a SQLite memory DB is otherwise per-connection).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def seed_items(db: Session) -> list[Item]:
    """Insert the canonical 5 items + StoreConfig into the test db."""
    for name, price in SEED_ITEMS:
        db.add(Item(name=name, price=price))
    db.add(
        StoreConfig(
            id=1,
            nth_order=DEFAULT_NTH_ORDER,
            discount_percent=DEFAULT_DISCOUNT_PERCENT,
        )
    )
    db.commit()
    return db.query(Item).order_by(Item.id).all()


@pytest.fixture
def make_orders(db: Session) -> Callable[..., list[Order]]:
    """Factory to insert dummy Order rows without going through the
    (not-yet-implemented) checkout service.

    Usage::

        make_orders(3)                          # 3 orders @ $10 each
        make_orders(2, subtotal=25.0)
    """
    counter = {"i": 0}

    def _make(
        n: int = 1,
        *,
        user_id: str = "tester",
        subtotal: float = 10.0,
        discount_amount: float = 0.0,
        discount_code: str | None = None,
    ) -> list[Order]:
        created: list[Order] = []
        for _ in range(n):
            counter["i"] += 1
            order = Order(
                user_id=f"{user_id}-{counter['i']}",
                subtotal=subtotal,
                discount_amount=discount_amount,
                discount_code=discount_code,
                total=subtotal - discount_amount,
            )
            db.add(order)
            created.append(order)
        db.commit()
        return created

    return _make
