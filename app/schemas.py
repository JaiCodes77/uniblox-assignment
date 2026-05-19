from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


class ItemOut(BaseModel):
    """Catalog item shape returned by GET /items."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------


class AddToCartIn(BaseModel):
    """Body for POST /cart/add."""

    user_id: str = Field(min_length=1)
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartItemOut(BaseModel):
    """One line in a cart view; unit_price is the current catalog price."""

    item_id: int
    name: str
    quantity: int
    unit_price: float
    line_total: float


class CartOut(BaseModel):
    """Body for GET /cart/{user_id}."""

    user_id: str
    items: list[CartItemOut]
    subtotal: float


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------


class CheckoutIn(BaseModel):
    """Body for POST /checkout."""

    user_id: str = Field(min_length=1)
    discount_code: Optional[str] = None


class OrderItemOut(BaseModel):
    """One line in a finalized order; unit_price is snapshotted at checkout."""

    item_id: int
    name: str
    quantity: int
    unit_price: float
    line_total: float


class OrderOut(BaseModel):
    """Response shape for POST /checkout."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    items: list[OrderItemOut]
    subtotal: float
    discount_code: Optional[str] = None
    discount_amount: float
    total: float
    created_at: datetime


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------


class DiscountEligibleOut(BaseModel):
    """Returned by POST /admin/discount/generate when a code was minted."""

    eligible: Literal[True] = True
    code: str
    percent: float


class DiscountIneligibleOut(BaseModel):
    """Returned by POST /admin/discount/generate when not yet eligible."""

    eligible: Literal[False] = False
    reason: str


# Discriminated union — FastAPI/OpenAPI will render this as a oneOf
# keyed on the `eligible` boolean.
DiscountGenerateOut = Annotated[
    Union[DiscountEligibleOut, DiscountIneligibleOut],
    Field(discriminator="eligible"),
]


class StatsOut(BaseModel):
    """Response shape for GET /admin/stats."""

    items_purchased: int
    total_revenue: float
    discount_codes_issued: int
    total_discount_amount: float
