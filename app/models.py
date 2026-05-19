from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

# NOTE: Prices and money amounts are stored as Float for simplicity. This
# trades exact decimal precision for ease of use; revisit with Numeric(10, 2)
# if real-money rounding matters.


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)

    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    item: Mapped["Item"] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    discount_code: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("discount_codes.code"), nullable=True
    )
    discount_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    item: Mapped["Item"] = relationship()


class DiscountCode(Base):
    __tablename__ = "discount_codes"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    percent: Mapped[float] = mapped_column(Float, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class StoreConfig(Base):
    __tablename__ = "store_config"

    # Singleton row pinned at id=1.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nth_order: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
