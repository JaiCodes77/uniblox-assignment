from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api._errors import service_errors
from app.db import get_db
from app.schemas import DiscountGenerateOut, StatsOut
from app.services.discount import DiscountService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/discount/generate", response_model=DiscountGenerateOut)
def generate_discount(db: Session = Depends(get_db)) -> dict:
    with service_errors():
        return DiscountService.generate_code(db)


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)) -> StatsOut:
    # TODO: implement AdminStatsService — should aggregate over orders:
    #   items_purchased       = SUM(order_items.quantity)
    #   total_revenue         = SUM(orders.total)
    #   discount_codes_issued = COUNT(discount_codes)
    #   total_discount_amount = SUM(orders.discount_amount)
    # For now wire the endpoint with zeros so callers/UI can light up.
    return StatsOut(
        items_purchased=0,
        total_revenue=0.0,
        discount_codes_issued=0,
        total_discount_amount=0.0,
    )
