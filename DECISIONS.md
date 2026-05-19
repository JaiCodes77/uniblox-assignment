# Design Decisions

Key design choices made while building this ecommerce backend, with tradeoffs noted. Each decision follows the format suggested in the assignment.

---

## Decision: SQLite + SQLAlchemy over in-memory store

**Context:** The spec allowed an in-memory store. I had to decide whether to take that shortcut or use a real DB.

**Options Considered:**

- Option A: Plain Python dicts wrapped in a Store class
- Option B: SQLite + SQLAlchemy ORM(in my practice projects im used to using SQLite)

**Choice:** Option B.

**Why:** Three things made the extra ~30 min of setup worth it:

- Data persists across restarts —> easier to demo
- In-memory SQLite per test gives clean isolation without resetting globals
- Free transaction support, which checkout relies on (order write + cart clear + code-mark-used must all succeed together)

The dict approach would have shipped faster, but the assignment is evaluating *how I think*, and showing a clean persistence layer which mirrors " production grade DB" was worth more than the time saved.

---

## Decision: Discount system —> admin-pull, single-use, percent off subtotal

**Context:** The spec said "Every Nth order gets a coupon code for X% discount" and described an admin endpoint to "generate a discount code if the condition above is satisfied." Several things were ambiguous: who triggers generation, whether the code is single-use, and what the discount applies to.

**Options Considered:**

- Option A: Auto-generate when the Nth order is placed, attach the code to that customer
- Option B: Admin manually calls generate; if the condition is met, mint a code anyone can redeem at checkout

**Choice:** Option B. Code is single-use globally. Discount is a percent off the entire order subtotal.

**Why:**

- Matches the spec —> "Generate IF the condition is satisfied" implies a check, not automatic creation
- Makes the admin endpoint meaningful — otherwise it would always succeed
- Single-use globally is the simplest semantic that prevents abuse
- Percent off subtotal avoids the per-item allocation problem

Sub-decision: `/admin/discount/generate` returns 200 with `{eligible: true, code, percent}` or `{eligible: false, reason}` instead of a 4xx. Calling it at the wrong time isn't really an error - it's a valid outcome the caller needs to handle.

Tradeoff: if admin doesn't call generate before the next order is placed, that cycle's milestone is missed. In production I'd add a scheduled job ... out of scope here.

---

## Decision: Layered architecture (models / schemas / services / api)

**Context:** For a small assignment, fat route handlers with DB calls inline would have shipped faster. I had to decide whether the extra layering was worth it.

**Options Considered:**

- Option A: FastAPI route handlers with logic and DB queries inline
- Option B: Thin routes calling a services layer; services take a Session; Pydantic schemas separate from SQLAlchemy models

**Choice:** Option B.

**Why:**

- 35 of 42 tests skip HTTP entirely and hit services directly —> faster to write, faster to run
- Routes become one-liners that translate request → service call → response
- Pydantic-vs-ORM separation keeps transport and persistence concerns independent

Cost: more files in a small codebase. Worth it for clarity.

---

## Decision: Float for monetary values

**Context:** Money in SQLAlchemy can be Float, Numeric(precision, scale), or integer cents - each with different precision and ergonomics(i thinkk)

**Options Considered:**

- Option A: Float —> easy, JSON-native, but inexact
- Option B: Numeric(10, 2) —> exact, but requires Decimal handling in Python and Pydantic
- Option C: Integer cents —> exact and fast, but every read/write needs ×100 / ÷100

**Choice:** Float.

**Why:** Conscious shortcut.  Float works and avoids Decimal-serialization boilerplate. In production this is wrong — Float gives `0.1 + 0.2 = 0.30000000000000004` and accumulates rounding errors at scale. The right fix is integer cents (Option C), and it's a contained refactor —> only models, service arithmetic, and schemas change.

---

## Decision: Snapshot unit_price on order items

**Context:** Order line items reference catalog items. If a catalog price changes later, what should historical orders show?

**Options Considered:**

- Option A: Store only item_id + quantity; compute totals from current item price
- Option B: Snapshot unit_price onto each order line at checkout

**Choice:** Option B.

**Why:** Orders are historical records —> the price the customer paid is part of that record and shouldn't change. This is how every real ecommerce system works (Shopify, Stripe, Amazon all snapshot (did a google search for this)). Cost is one extra column. The regression test (`test_order_items_snapshot_price_at_order_time`) mutates an item price after checkout and asserts the order still shows the original price —>  catches a class of bug that would otherwise be silent.

---

## Decision: Custom exceptions + service-internal transactions ( discussed this with the LLM)

**Context:** Services need to signal failures to routes (not-found, invalid input) and manage DB transactions. Several ways to wire both.

**Options Considered:**

- Option A: Stdlib exceptions (ValueError, LookupError); routes own transactions
- Option B: Custom hierarchy (NotFoundError, InvalidInputError); services own transactions internally

**Choice:** Option B for both.

**Why:**

- One FastAPI exception handler maps `NotFoundError → 404`, `InvalidInputError → 400`, etc. Routes stay one-liners.
- `ValueError` could mean a dozen things; `InvalidInputError` means one.
- Checkout already needs atomicity across multiple writes; keeping the commit inside the service guarantees it.

Tradeoff: if services ever need to compose into a larger transaction at the route layer, this design fights you. The fix would be a Unit-of-Work pattern is whart we deduced which is  premature here.

---

## Decision: Minimal React-vite frontend over a full SPA

**Context:** Frontend was "a plus" per the spec. I had limited time left and wanted the system demoable without curl or Swagger.

**Options Considered:**

- Option A: Skip frontend, rely on FastAPI `/docs`
- Option B: Full React/Vite SPA
- Option C: Single-page vanilla HTML + JS

**Choice:** Option C.

**Why:**

- A SPA would have eaten the remaining time and added build complexity disproportionate to a demo
- `/docs` works but isn't representative of how a customer would actually use the system
- React = easy to demo and i wanted the reviewers to be able to visualize the backend services/endpoints.

In a real product this would be React/Next with proper state management. Here, the point was just to prove the backend is usable.   
  
note : i have not deployed it yet since it was not needed, i could deploy this on vercel or railway if needed. the run steps for this project is in the readme! 