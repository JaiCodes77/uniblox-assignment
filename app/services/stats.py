from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DiscountCode, Order, OrderItem


class StatsService:
    """Aggregations over orders, line items, and discount codes for /admin/stats."""

    @staticmethod
    def get_stats(db: Session) -> dict:
        # Each aggregate is its own scalar() call. ``coalesce`` defends against
        # the empty-state case where SUM returns NULL on an empty table.
        items_purchased: int = (
            db.scalar(
                select(func.coalesce(func.sum(OrderItem.quantity), 0))
            )
            or 0
        )
        total_revenue: float = (
            db.scalar(
                select(func.coalesce(func.sum(Order.total), 0.0))
            )
            or 0.0
        )
        discount_codes_issued: int = (
            db.scalar(select(func.count()).select_from(DiscountCode)) or 0
        )
        total_discount_amount: float = (
            db.scalar(
                select(func.coalesce(func.sum(Order.discount_amount), 0.0))
            )
            or 0.0
        )

        return {
            "items_purchased": int(items_purchased),
            "total_revenue": float(total_revenue),
            "discount_codes_issued": int(discount_codes_issued),
            "total_discount_amount": float(total_discount_amount),
        }
