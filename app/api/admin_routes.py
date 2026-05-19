from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api._errors import service_errors
from app.db import get_db
from app.schemas import DiscountGenerateOut, StatsOut
from app.services.discount import DiscountService
from app.services.stats import StatsService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/discount/generate", response_model=DiscountGenerateOut)
def generate_discount(db: Session = Depends(get_db)) -> dict:
    with service_errors():
        return DiscountService.generate_code(db)


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)) -> dict:
    return StatsService.get_stats(db)
