from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./store.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base = declarative_base()


SEED_ITEMS: list[tuple[str, float]] = [
    ("T-shirt", 20.00),
    ("Mug", 10.00),
    ("Sticker pack", 5.00),
    ("Hoodie", 50.00),
    ("Notebook", 15.00),
]

DEFAULT_NTH_ORDER = 3
DEFAULT_DISCOUNT_PERCENT = 10


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models lazily so their tables register on Base.metadata
    # before create_all runs, while avoiding a circular import at module load.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def seed() -> None:
    from app.models import Item, StoreConfig

    with SessionLocal() as db:
        for name, price in SEED_ITEMS:
            existing = db.query(Item).filter(Item.name == name).first()
            if existing is None:
                db.add(Item(name=name, price=price))

        config = db.get(StoreConfig, 1)
        if config is None:
            db.add(
                StoreConfig(
                    id=1,
                    nth_order=DEFAULT_NTH_ORDER,
                    discount_percent=DEFAULT_DISCOUNT_PERCENT,
                )
            )

        db.commit()
