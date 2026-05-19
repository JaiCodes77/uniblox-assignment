from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app

TSHIRT_ID = 1
MUG_ID = 2


@pytest.fixture
def client(db: Session, seed_items) -> Iterator[TestClient]:
    """A TestClient bound to the test in-memory DB.

    We deliberately instantiate ``TestClient`` *without* a ``with`` context,
    so the app lifespan (which would call ``init_db``/``seed`` against the
    production engine and create a stray ``./store.db``) doesn't run.
    """

    def _override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_list_items_returns_seeded_items(client: TestClient) -> None:
    response = client.get("/items")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    names = {row["name"] for row in body}
    assert names == {"T-shirt", "Mug", "Sticker pack", "Hoodie", "Notebook"}


# ---------------------------------------------------------------------------
# Happy path: cart → checkout
# ---------------------------------------------------------------------------


def test_happy_path_add_to_cart_then_checkout(client: TestClient) -> None:
    # T-shirt $20 x 2
    r1 = client.post(
        "/cart/add",
        json={"user_id": "alice", "item_id": TSHIRT_ID, "quantity": 2},
    )
    assert r1.status_code == 200, r1.text
    cart1 = r1.json()
    assert cart1["user_id"] == "alice"
    assert cart1["subtotal"] == 40.0
    assert len(cart1["items"]) == 1

    # Mug $10 x 1 → subtotal $50
    r2 = client.post(
        "/cart/add",
        json={"user_id": "alice", "item_id": MUG_ID, "quantity": 1},
    )
    assert r2.status_code == 200, r2.text
    cart2 = r2.json()
    assert cart2["subtotal"] == 50.0
    assert len(cart2["items"]) == 2

    # GET reflects the same state.
    r3 = client.get("/cart/alice")
    assert r3.status_code == 200
    assert r3.json() == cart2

    # Checkout (no discount).
    r4 = client.post("/checkout", json={"user_id": "alice"})
    assert r4.status_code == 200, r4.text
    order = r4.json()
    assert order["user_id"] == "alice"
    assert order["subtotal"] == 50.0
    assert order["discount_amount"] == 0.0
    assert order["discount_code"] is None
    assert order["total"] == 50.0
    assert len(order["items"]) == 2
    assert {it["name"] for it in order["items"]} == {"T-shirt", "Mug"}
    assert "id" in order and isinstance(order["id"], int)
    assert "created_at" in order

    # Cart is empty after checkout.
    r5 = client.get("/cart/alice")
    assert r5.status_code == 200
    assert r5.json()["items"] == []
    assert r5.json()["subtotal"] == 0.0


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


def test_add_to_cart_unknown_item_returns_404(client: TestClient) -> None:
    response = client.post(
        "/cart/add",
        json={"user_id": "alice", "item_id": 9999, "quantity": 1},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_add_to_cart_invalid_quantity_returns_422(client: TestClient) -> None:
    # Pydantic rejects quantity=0 at the schema layer → 422.
    response = client.post(
        "/cart/add",
        json={"user_id": "alice", "item_id": TSHIRT_ID, "quantity": 0},
    )
    assert response.status_code == 422


def test_get_cart_unknown_user_returns_404(client: TestClient) -> None:
    response = client.get("/cart/ghost")
    assert response.status_code == 404


def test_checkout_empty_cart_returns_400(client: TestClient) -> None:
    response = client.post("/checkout", json={"user_id": "nobody"})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_checkout_unknown_discount_code_returns_404(client: TestClient) -> None:
    client.post(
        "/cart/add",
        json={"user_id": "alice", "item_id": TSHIRT_ID, "quantity": 1},
    )
    response = client.post(
        "/checkout",
        json={"user_id": "alice", "discount_code": "DOESNOT"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


def test_admin_discount_generate_not_eligible_initially(client: TestClient) -> None:
    response = client.post("/admin/discount/generate")
    assert response.status_code == 200
    assert response.json() == {"eligible": False, "reason": "no orders yet"}


def test_admin_stats_placeholder_returns_zeros(client: TestClient) -> None:
    response = client.get("/admin/stats")
    assert response.status_code == 200
    assert response.json() == {
        "items_purchased": 0,
        "total_revenue": 0.0,
        "discount_codes_issued": 0,
        "total_discount_amount": 0.0,
    }


# ---------------------------------------------------------------------------
# OpenAPI surface — confirms every endpoint is registered.
# ---------------------------------------------------------------------------


def test_openapi_lists_every_endpoint(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    paths = set(schema["paths"].keys())
    assert {
        "/items",
        "/cart/add",
        "/cart/{user_id}",
        "/checkout",
        "/admin/discount/generate",
        "/admin/stats",
        "/health",
    } <= paths
