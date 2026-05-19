from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cart, CartItem
from app.services.cart import CartService

# Item IDs assigned during seeding (insertion order in SEED_ITEMS):
#   1=T-shirt $20, 2=Mug $10, 3=Sticker pack $5, 4=Hoodie $50, 5=Notebook $15
TSHIRT_ID = 1
MUG_ID = 2
HOODIE_ID = 4


def _cart_for(db: Session, user_id: str) -> Cart | None:
    return db.scalar(select(Cart).where(Cart.user_id == user_id))


def test_add_new_item_creates_cart(db: Session, seed_items) -> None:
    line = CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=2)

    cart = _cart_for(db, "u1")
    assert cart is not None
    assert line.cart_id == cart.id
    assert line.item_id == TSHIRT_ID
    assert line.quantity == 2
    assert len(cart.items) == 1


def test_add_same_item_twice_sums_quantity(db: Session, seed_items) -> None:
    CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=2)
    CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=3)

    cart = _cart_for(db, "u1")
    assert cart is not None
    assert len(cart.items) == 1
    line = db.get(CartItem, (cart.id, TSHIRT_ID))
    assert line is not None
    assert line.quantity == 5


def test_add_multiple_distinct_items(db: Session, seed_items) -> None:
    CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=1)
    CartService.add_to_cart(db, user_id="u1", item_id=MUG_ID, quantity=4)

    cart = _cart_for(db, "u1")
    assert cart is not None
    by_item = {line.item_id: line.quantity for line in cart.items}
    assert by_item == {TSHIRT_ID: 1, MUG_ID: 4}


def test_add_nonexistent_item_raises(db: Session, seed_items) -> None:
    with pytest.raises(ValueError, match="item 9999 not found"):
        CartService.add_to_cart(db, user_id="u1", item_id=9999, quantity=1)

    assert _cart_for(db, "u1") is None


@pytest.mark.parametrize("bad_qty", [0, -1, -100])
def test_add_invalid_quantity_raises(db: Session, seed_items, bad_qty: int) -> None:
    with pytest.raises(ValueError, match="quantity must be greater than 0"):
        CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=bad_qty)

    assert _cart_for(db, "u1") is None


def test_get_cart_returns_none_for_unknown_user(db: Session, seed_items) -> None:
    assert CartService.get_cart(db, user_id="ghost") is None


def test_get_cart_computes_subtotal_correctly(db: Session, seed_items) -> None:
    # T-shirt $20 x 2 = $40
    # Mug     $10 x 1 = $10
    # Hoodie  $50 x 1 = $50
    # subtotal = $100
    CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=2)
    CartService.add_to_cart(db, user_id="u1", item_id=MUG_ID, quantity=1)
    CartService.add_to_cart(db, user_id="u1", item_id=HOODIE_ID, quantity=1)

    cart = CartService.get_cart(db, user_id="u1")
    assert cart is not None
    assert cart["user_id"] == "u1"
    assert cart["subtotal"] == pytest.approx(100.0)

    by_item = {line["item_id"]: line for line in cart["items"]}
    assert by_item[TSHIRT_ID]["quantity"] == 2
    assert by_item[TSHIRT_ID]["unit_price"] == pytest.approx(20.0)
    assert by_item[TSHIRT_ID]["line_total"] == pytest.approx(40.0)
    assert by_item[TSHIRT_ID]["name"] == "T-shirt"

    assert by_item[MUG_ID]["line_total"] == pytest.approx(10.0)
    assert by_item[HOODIE_ID]["line_total"] == pytest.approx(50.0)


def test_clear_cart_empties_items(db: Session, seed_items) -> None:
    CartService.add_to_cart(db, user_id="u1", item_id=TSHIRT_ID, quantity=2)
    CartService.add_to_cart(db, user_id="u1", item_id=MUG_ID, quantity=1)

    CartService.clear_cart(db, user_id="u1")

    cart = CartService.get_cart(db, user_id="u1")
    assert cart is not None
    assert cart["items"] == []
    assert cart["subtotal"] == 0.0

    # Cart row itself is preserved; only its lines are gone.
    cart_row = _cart_for(db, "u1")
    assert cart_row is not None
    assert cart_row.items == []
