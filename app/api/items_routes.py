from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item
from app.schemas import ItemOut

router = APIRouter(tags=["items"])


@router.get("/items", response_model=list[ItemOut])
def list_items(db: Session = Depends(get_db)) -> list[Item]:
    return db.query(Item).order_by(Item.id).all()
