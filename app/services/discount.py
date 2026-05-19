from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DiscountCode, Order, StoreConfig
from app.services.errors import NotFoundError


class DiscountService:
    """Discount code minting + redemption."""

    # ----- internal helpers ------------------------------------------------

    @staticmethod
    def _get_config(db: Session) -> StoreConfig:
        config = db.get(StoreConfig, 1)
        if config is None:
            raise RuntimeError("StoreConfig (id=1) not initialized")
        return config

    @staticmethod
    def _unused_code(db: Session) -> Optional[DiscountCode]:
        return db.scalar(
            select(DiscountCode).where(DiscountCode.used.is_(False)).limit(1)
        )

    @staticmethod
    def _total_orders(db: Session) -> int:
        return db.scalar(select(func.count()).select_from(Order)) or 0

    @staticmethod
    def _mint() -> str:
        return uuid4().hex[:8].upper()

    # ----- public API ------------------------------------------------------

    @staticmethod
    def generate_code(db: Session) -> dict:
        """Mint a new discount code iff the Nth-order condition is met
        AND there is no unused code already outstanding."""
        config = DiscountService._get_config(db)
        total_orders = DiscountService._total_orders(db)

        if total_orders == 0:
            return {"eligible": False, "reason": "no orders yet"}

        if total_orders % config.nth_order != 0:
            return {
                "eligible": False,
                "reason": (
                    f"order count {total_orders} not at multiple of "
                    f"{config.nth_order}"
                ),
            }

        if DiscountService._unused_code(db) is not None:
            return {"eligible": False, "reason": "unused code already exists"}

        code = DiscountService._mint()
        db.add(
            DiscountCode(
                code=code,
                percent=config.discount_percent,
                used=False,
            )
        )
        db.commit()
        return {
            "eligible": True,
            "code": code,
            "percent": config.discount_percent,
        }

    @staticmethod
    def validate_code(db: Session, code: str) -> DiscountCode:
        """Return the DiscountCode row iff it exists and has not been used.

        Raises ``NotFoundError`` if the code is unknown and ``ValueError``
        if the code exists but is already used.
        """
        record = db.get(DiscountCode, code)
        if record is None:
            raise NotFoundError(f"discount code {code!r} not found")
        if record.used:
            raise ValueError(f"discount code {code!r} already used")
        return record

    @staticmethod
    def mark_used(db: Session, code: str) -> None:
        record = db.get(DiscountCode, code)
        if record is None:
            raise NotFoundError(f"discount code {code!r} not found")
        record.used = True
        record.used_at = datetime.now()
        db.commit()
