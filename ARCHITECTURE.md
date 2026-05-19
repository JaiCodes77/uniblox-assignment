# Ecommerce Store — Architecture

## Stack
Python 3.11+, FastAPI, SQLAlchemy 2.x, SQLite, pytest.

## Domain
Customers add items to a cart and checkout. Every Nth order qualifies for a discount code that admin generates and customers redeem at checkout. Two admin endpoints: generate code (when Nth-order condition met) and view stats.

## Layering
- `app/models.py` — SQLAlchemy ORM models (DB schema)
- `app/schemas.py` — Pydantic request/response models
- `app/db.py` — engine, SessionLocal, get_db dependency, init_db, seed
- `app/store.py` — N/A (using SQLAlchemy)
- `app/services/` — pure business logic, take a `Session` arg, return domain objects/dicts
- `app/api/` — FastAPI routers, thin wrappers around services
- `app/main.py` — app factory, includes routers, runs init_db + seed on startup
- `tests/` — pytest with in-memory SQLite fixture

## Tables
- items(id, name, price)
- carts(id, user_id UNIQUE)
- cart_items(cart_id, item_id, quantity) — composite PK (cart_id, item_id)
- orders(id, user_id, subtotal, discount_code nullable, discount_amount, total, created_at)
- order_items(order_id, item_id, quantity, unit_price) — snapshot price
- discount_codes(code PK, percent, used bool, created_at, used_at nullable)
- store_config(id=1 singleton, nth_order, discount_percent)

## Discount logic
- Admin calls POST /admin/discount/generate
- Eligible iff: total_orders > 0 AND total_orders % N == 0 AND no unused code currently exists
- If eligible: mint a random short code (e.g. uuid4 first 8 chars uppercased), percent = X from config, return it
- If not eligible: return 200 with {eligible: false, reason: "..."}
- Single-use globally: once redeemed at checkout, `used = true`
- Applied as percent off subtotal at checkout

## Endpoints
- GET    /items                      → list catalog
- POST   /cart/add                   → {user_id, item_id, quantity}
- GET    /cart/{user_id}             → view cart
- POST   /checkout                   → {user_id, discount_code?} → order
- POST   /admin/discount/generate    → mint code if eligible
- GET    /admin/stats                → {items_purchased, total_revenue, discount_codes_issued, total_discount_amount}

## Seed data
- ~5 items with varied prices
- StoreConfig: nth_order=3, discount_percent=10 (small N for easy demo)
