# Ecommerce Store API

A small FastAPI + SQLAlchemy backend for an ecommerce store: list a catalog, build a per-user cart, check out into an order, and apply admin-issued discount codes that unlock on every Nth order. SQLite-backed for zero-config local dev; fully covered by pytest. A minimal React + Vite UI under [`frontend/`](./frontend) is bundled so you can click through the API instead of curling it — see [Frontend](#frontend-optional-ui).

## Stack

- **Python 3.11+** — modern typing, `match`, `Self`, etc.
- **FastAPI** — typed routing, auto OpenAPI/Swagger at `/docs`.
- **SQLAlchemy 2.x** — typed ORM (`Mapped`/`mapped_column`) for the data layer.
- **SQLite** — file-based DB, no service to run.
- **Pydantic v2** — request/response validation, discriminated unions for richer responses.
- **pytest** — unit + integration tests; in-memory SQLite fixture for isolation.
- **uvicorn** — ASGI dev server.

## Setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open <http://localhost:8000/docs> for the interactive Swagger UI.

The first request triggers `init_db()` + `seed()`, which creates `./store.db`, inserts the 5 seed items, and pins a `StoreConfig` row at `nth_order=3, discount_percent=10`. Seeding is idempotent.

## Running Tests

```bash
pytest -v
```

Tests use an in-memory SQLite engine per test (`StaticPool`) for full isolation — no `store.db` is touched.

## Frontend (optional UI)

A small React 19 + TypeScript + Vite app lives in [`frontend/`](./frontend). It's there purely as a visualizer for the backend — three tabs (Shop / Cart / Admin) that exercise every endpoint, a user-id switcher in the header, and a live status dot that polls `/health`. Useful if you'd rather click through the demo than copy-paste curl.

Run it alongside the backend:

```bash
# Terminal 1 — backend
uvicorn app.main:app --reload                 # binds :8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev                                   # opens on :5173
```

Vite proxies `/api/*` → `http://localhost:8000`, so the frontend talks to the live API without any CORS setup. There's also `node scripts/verify-api.mjs` inside `frontend/` — a fast Node smoke test that walks the full happy path against a running backend and asserts every response shape, useful as a CI/sanity check.

## API Overview

| Method | Path                          | Purpose                                                                 |
|--------|-------------------------------|-------------------------------------------------------------------------|
| GET    | `/items`                      | List the catalog.                                                       |
| POST   | `/cart/add`                   | Add `{user_id, item_id, quantity}` to a user's cart (get-or-create).    |
| GET    | `/cart/{user_id}`             | View the user's current cart with computed line totals + subtotal.      |
| POST   | `/checkout`                   | Convert cart to order; optionally apply a `discount_code`.              |
| POST   | `/admin/discount/generate`    | Mint a code iff `total_orders % N == 0` and no unused code is outstanding. |
| GET    | `/admin/stats`                | Aggregate stats: items purchased, revenue, codes issued, total discount. |
| GET    | `/health`                     | Liveness probe.                                                         |

**Error contract**: service `ValueError` → `400 {"detail": "..."}`; "not found" cases → `404`; Pydantic validation failures → `422`.

## Example Flow

Walkthrough that triggers the Nth-order discount (N=3 in the seed config):

```bash
# 1. List the catalog
curl -s http://localhost:8000/items | jq

# 2. Alice builds a cart (two adds → one non-trivial cart)
curl -s -X POST http://localhost:8000/cart/add \
  -H 'content-type: application/json' \
  -d '{"user_id":"alice","item_id":1,"quantity":2}'   # T-shirt x2
curl -s -X POST http://localhost:8000/cart/add \
  -H 'content-type: application/json' \
  -d '{"user_id":"alice","item_id":2,"quantity":1}'   # Mug x1
curl -s http://localhost:8000/cart/alice | jq

# 3. Place 3 orders (one per user) to satisfy the Nth-order condition
curl -s -X POST http://localhost:8000/checkout \
  -H 'content-type: application/json' -d '{"user_id":"alice"}'

curl -s -X POST http://localhost:8000/cart/add \
  -H 'content-type: application/json' \
  -d '{"user_id":"bob","item_id":4,"quantity":1}'     # Hoodie
curl -s -X POST http://localhost:8000/checkout \
  -H 'content-type: application/json' -d '{"user_id":"bob"}'

curl -s -X POST http://localhost:8000/cart/add \
  -H 'content-type: application/json' \
  -d '{"user_id":"carol","item_id":5,"quantity":1}'   # Notebook
curl -s -X POST http://localhost:8000/checkout \
  -H 'content-type: application/json' -d '{"user_id":"carol"}'

# 4. Now eligible — mint a discount code
CODE=$(curl -s -X POST http://localhost:8000/admin/discount/generate | jq -r '.code')
echo "code: $CODE"

# 5. Dave builds a cart and redeems the code
curl -s -X POST http://localhost:8000/cart/add \
  -H 'content-type: application/json' \
  -d '{"user_id":"dave","item_id":4,"quantity":2}'    # Hoodie x2 = $100
curl -s -X POST http://localhost:8000/checkout \
  -H 'content-type: application/json' \
  -d "{\"user_id\":\"dave\",\"discount_code\":\"$CODE\"}" | jq
# → subtotal 100.0, discount_amount 10.0, total 90.0

# 6. Admin stats
curl -s http://localhost:8000/admin/stats | jq
# → items_purchased 7, total_revenue 205.0, discount_codes_issued 1,
#   total_discount_amount 10.0
#   (alice 3 + bob 1 + carol 1 + dave 2 = 7 items;
#    50 + 50 + 15 + 90 = 205 revenue)
```

## Project Structure

```
.
├── ARCHITECTURE.md           # System overview: domain, tables, endpoints
├── README.md                 # This file
├── requirements.txt
├── app/
│   ├── main.py               # FastAPI app factory + lifespan (init_db, seed)
│   ├── db.py                 # Engine, SessionLocal, get_db, init_db, seed
│   ├── models.py             # SQLAlchemy 2.x ORM models
│   ├── schemas.py            # Pydantic v2 request/response models
│   ├── api/                  # Routers — thin wrappers over services
│   │   ├── _errors.py        #   Shared service-error → HTTPException mapper
│   │   ├── items_routes.py
│   │   ├── cart_routes.py
│   │   ├── checkout_routes.py
│   │   └── admin_routes.py
│   └── services/             # Business logic — pure functions on a Session
│       ├── errors.py         #   NotFoundError(ValueError) for 404 mapping
│       ├── cart.py
│       ├── checkout.py       #   Atomic: order + items snapshot + cart clear
│       ├── discount.py
│       └── stats.py
├── tests/
│   ├── conftest.py           # In-memory db + seed_items + make_orders fixtures
│   ├── test_cart.py
│   ├── test_checkout.py
│   ├── test_discount.py
│   ├── test_stats.py
│   └── test_api.py           # FastAPI TestClient integration tests
└── frontend/                 # Optional React + Vite UI to visualize the backend
    ├── src/                  #   App.tsx, api.ts client, components/, hooks/
    ├── scripts/
    │   └── verify-api.mjs    #   Node smoke test against a running backend
    └── vite.config.ts        #   Dev server proxies /api → localhost:8000
```

## Design Decisions

See [DECISIONS.md](./DECISIONS.md) for design rationale (layering, transaction boundaries, price snapshots, discount lifecycle, error mapping, Float-vs-Numeric tradeoff).
