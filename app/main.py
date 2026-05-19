from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import (
    admin_routes,
    cart_routes,
    checkout_routes,
    items_routes,
)
from app.db import init_db, seed


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    seed()
    yield


app = FastAPI(title="Ecommerce Store", lifespan=lifespan)

app.include_router(items_routes.router)
app.include_router(cart_routes.router)
app.include_router(checkout_routes.router)
app.include_router(admin_routes.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
