from __future__ import annotations

from collections.abc import Iterator

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
from app.models import Item, StoreConfig


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
