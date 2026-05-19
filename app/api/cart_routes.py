from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api._errors import service_errors
from app.db import get_db
from app.schemas import AddToCartIn, CartOut
from app.services.cart import CartService

router = APIRouter(tags=["cart"])


@router.post("/cart/add", response_model=CartOut)
def add_to_cart(payload: AddToCartIn, db: Session = Depends(get_db)) -> dict:
    with service_errors():
        CartService.add_to_cart(
            db, payload.user_id, payload.item_id, payload.quantity
        )
    cart = CartService.get_cart(db, payload.user_id)
    assert cart is not None  # add_to_cart guarantees the cart exists
    return cart


@router.get("/cart/{user_id}", response_model=CartOut)
def get_cart(user_id: str, db: Session = Depends(get_db)) -> dict:
    cart = CartService.get_cart(db, user_id)
    if cart is None:
        raise HTTPException(
            status_code=404, detail=f"cart for user {user_id!r} not found"
        )
    return cart
