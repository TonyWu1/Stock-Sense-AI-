"""REFERENCE backend for Team Member 1 to replace/adapt.

Everything here operates on a LOCAL SQLite database. It never purchases stock.
See backend_adapter.py for the stable contract used by the AI agent.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("STOCKSENSE_DB_PATH", "data/stocksense.db"))

# ID, product, stock, reorder point, 7-day sales, supplier, buy price, sell price
SAMPLE_PRODUCTS = [
    (1, "Whole Milk 1L", 7, 12, 34, "FreshFields Dairy", 1.20, 2.20),
    (2, "Brown Eggs (12-pack)", 5, 10, 25, "Valley Farms", 2.10, 3.99),
    (3, "White Bread Loaf", 8, 15, 37, "Baker's Choice", 1.05, 2.49),
    (4, "Bananas 1kg", 11, 18, 42, "Tropical Produce Co.", 0.80, 1.65),
    (5, "Jasmine Rice 1kg", 27, 12, 14, "Pantry Partners", 1.75, 3.20),
    (6, "Black Beans 500g", 10, 13, 21, "Pantry Partners", 0.75, 1.65),
    (7, "Olive Oil 500ml", 4, 8, 12, "MedFoods Wholesale", 4.25, 7.99),
    (8, "Pasta 500g", 36, 14, 16, "Pantry Partners", 0.90, 2.10),
    (9, "Cheddar Cheese 200g", 6, 9, 19, "FreshFields Dairy", 1.90, 3.79),
    (10, "Ground Coffee 250g", 12, 10, 17, "Roast Republic", 3.50, 6.95),
    (11, "Orange Juice 1L", 9, 13, 27, "Sunrise Beverages", 1.40, 2.89),
    (12, "Granulated Sugar 1kg", 23, 10, 11, "Pantry Partners", 0.98, 1.99),
    (13, "Bottled Water 1.5L", 18, 25, 52, "Sunrise Beverages", 0.38, 1.09),
    (14, "Chicken Breast 1kg", 5, 10, 18, "Valley Farms", 4.10, 7.80),
    (15, "Dish Soap 500ml", 22, 9, 8, "HomeGoods Supply", 1.30, 3.15),
]


# SIMULATED planning assumptions: name -> (supplier lead days, shelf life days).
# None = no short shelf-life constraint in this prototype; it does NOT mean
# a product never expires. These are NOT connected to real supplier systems.
SAMPLE_PLANNING_ASSUMPTIONS = {
    "Whole Milk 1L": (2, 7),
    "Brown Eggs (12-pack)": (2, 21),
    "White Bread Loaf": (1, 5),
    "Bananas 1kg": (2, 6),
    "Jasmine Rice 1kg": (4, None),
    "Black Beans 500g": (4, None),
    "Olive Oil 500ml": (5, None),
    "Pasta 500g": (4, None),
    "Cheddar Cheese 200g": (2, 30),
    "Ground Coffee 250g": (5, None),
    "Orange Juice 1L": (3, 14),
    "Granulated Sugar 1kg": (4, None),
    "Bottled Water 1.5L": (4, None),
    "Chicken Breast 1kg": (2, 4),
    "Dish Soap 500ml": (5, None),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cents(value: object, *, allow_zero: bool = True) -> int:
    if isinstance(value, bool):
        raise ValueError("Amount must be a number.")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Amount must be a valid number.") from None
    if not d.is_finite() or d < 0 or (not allow_zero and d == 0):
        raise ValueError("Amount must be non-negative and finite.")
    if d > Decimal("1000000"):
        raise ValueError("Amount exceeds the prototype safety limit.")
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents: int) -> float:
    return round(cents / 100.0, 2)


@contextmanager
def _connect():
    """Commit or roll back and CLOSE each SQLite connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    """Create tables and seed 15 SIMULATED products on a fresh database."""
    with _connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
                reorder_level INTEGER NOT NULL CHECK(reorder_level >= 0),
                sales_last_7_days INTEGER NOT NULL CHECK(sales_last_7_days >= 0),
                supplier TEXT NOT NULL,
                unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents > 0),
                selling_price_cents INTEGER NOT NULL CHECK(selling_price_cents >= 0),
                supplier_lead_days INTEGER NOT NULL DEFAULT 3 CHECK(supplier_lead_days >= 0),
                shelf_life_days INTEGER CHECK(shelf_life_days IS NULL OR shelf_life_days > 0)
            );
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'approved')),
                total_cost_cents INTEGER NOT NULL,
                budget_cents INTEGER,
                created_at TEXT NOT NULL,
                approved_at TEXT
            );
            CREATE TABLE IF NOT EXISTS purchase_order_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES purchase_orders(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                product_name TEXT NOT NULL,
                supplier TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_cost_cents INTEGER NOT NULL,
                line_cost_cents INTEGER NOT NULL,
                UNIQUE(order_id, product_id)
            );
        """)
        # Additive migration: safe for the starter SQLite DB already on disk.
        old_columns = {r[1] for r in db.execute("PRAGMA table_info(products)")}
        new_lead = "supplier_lead_days" not in old_columns
        new_shelf = "shelf_life_days" not in old_columns
        if new_lead:
            db.execute("ALTER TABLE products ADD COLUMN supplier_lead_days INTEGER NOT NULL DEFAULT 3")
        if new_shelf:
            db.execute("ALTER TABLE products ADD COLUMN shelf_life_days INTEGER")
        # Only seed assumptions when upgrading older databases or on new seed.
        # Existing manually adjusted metadata is never overwritten on restart.
        if new_lead or new_shelf:
            for name, (lead, shelf) in SAMPLE_PLANNING_ASSUMPTIONS.items():
                if new_lead:
                    db.execute("UPDATE products SET supplier_lead_days=? WHERE name=?", (lead, name))
                if new_shelf:
                    db.execute("UPDATE products SET shelf_life_days=? WHERE name=?", (shelf, name))
        if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            db.executemany("""
                INSERT INTO products (id, name, stock_quantity, reorder_level,
                    sales_last_7_days, supplier, unit_cost_cents, selling_price_cents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [(p[0],p[1],p[2],p[3],p[4],p[5],_cents(p[6]),_cents(p[7]))
                  for p in SAMPLE_PRODUCTS])
            for name, (lead, shelf) in SAMPLE_PLANNING_ASSUMPTIONS.items():
                db.execute("UPDATE products SET supplier_lead_days=?, shelf_life_days=? WHERE name=?",
                           (lead, shelf, name))


def _product(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["id"], "name": row["name"],
        "stock_quantity": row["stock_quantity"],
        "reorder_level": row["reorder_level"],
        "sales_last_7_days": row["sales_last_7_days"],
        "supplier": row["supplier"],
        "unit_cost": _money(row["unit_cost_cents"]),
        "selling_price": _money(row["selling_price_cents"]),
        "supplier_lead_days": row["supplier_lead_days"],
        "shelf_life_days": row["shelf_life_days"],
    }



def add_product(
    name: str,
    supplier: str,
    stock_quantity: int,
    reorder_level: int,
    sales_last_7_days: int,
    unit_cost: float,
    selling_price: float,
    supplier_lead_days: int = 3,
    shelf_life_days: int | None = None,
) -> dict:
    """Add one owner-defined product to the existing SQLite catalog.

    No sample inventory is reset. Prices are stored in exact integer cents.
    A newly added product with zero recent sales will not receive a Smart
    Restock recommendation until a sales signal has been supplied.
    """
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
        raise ValueError("Product name must be 1–120 characters.")
    if not isinstance(supplier, str) or not 1 <= len(supplier.strip()) <= 120:
        raise ValueError("Supplier name must be 1–120 characters.")
    name, supplier = name.strip(), supplier.strip()
    numbers = {
        "Current stock": (stock_quantity, 0, 1_000_000),
        "Reorder threshold": (reorder_level, 0, 1_000_000),
        "Sales in the last 7 days": (sales_last_7_days, 0, 1_000_000),
        "Supplier lead time": (supplier_lead_days, 0, 365),
    }
    for label, (value, low, high) in numbers.items():
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{label} must be a whole number from {low} to {high}.")
    if shelf_life_days is not None and (
        type(shelf_life_days) is not int or not 1 <= shelf_life_days <= 3650
    ):
        raise ValueError("Shelf life must be blank or 1–3650 days.")
    cost_cents = _cents(unit_cost, allow_zero=False)
    price_cents = _cents(selling_price)
    if cost_cents < 1:
        raise ValueError("Unit cost must be at least $0.01.")

    with _connect() as db:
        duplicate = db.execute(
            "SELECT id FROM products WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if duplicate is not None:
            raise ValueError("A product with this name already exists. Choose a distinct name.")
        cur = db.execute("""
            INSERT INTO products (name, stock_quantity, reorder_level,
                sales_last_7_days, supplier, unit_cost_cents,
                selling_price_cents, supplier_lead_days, shelf_life_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, stock_quantity, reorder_level, sales_last_7_days,
              supplier, cost_cents, price_cents, supplier_lead_days,
              shelf_life_days))
        product = _product(db.execute(
            "SELECT * FROM products WHERE id=?", (cur.lastrowid,)
        ).fetchone())
    return product


def get_inventory() -> list[dict]:
    with _connect() as db:
        return [_product(r) for r in db.execute("SELECT * FROM products ORDER BY id")]


def get_low_stock_products() -> list[dict]:
    return [p for p in get_inventory() if p["stock_quantity"] <= p["reorder_level"]]


def recommend_restock(max_budget: float | None = None) -> dict:
    """Simple, transparent rule: target=max(2*reorder level, 2*7-day sales).

    Limited budget: fulfill most urgent items first; reduce quantities if needed.
    These are illustrative heuristics, NOT statistically validated forecasts.
    """
    remaining_cents = None if max_budget is None else _cents(max_budget)
    inventory = get_low_stock_products()
    inventory.sort(key=lambda p: (p["stock_quantity"] / max(p["reorder_level"], 1),
                                   -p["sales_last_7_days"], p["product_id"]))
    lines = []
    skipped = []
    for p in inventory:
        target = max(p["reorder_level"] * 2, p["sales_last_7_days"] * 2)
        needed = max(0, target - p["stock_quantity"])
        unit_cents = _cents(p["unit_cost"], allow_zero=False)
        qty = needed if remaining_cents is None else min(needed, remaining_cents // unit_cents)
        if qty == 0:
            skipped.append(p["name"])
            continue
        line_cents = qty * unit_cents
        lines.append({
            "product_id": p["product_id"], "name": p["name"],
            "supplier": p["supplier"], "quantity": qty,
            "unit_cost": p["unit_cost"], "line_cost": _money(line_cents),
            "current_stock": p["stock_quantity"], "target_stock": target,
        })
        if remaining_cents is not None:
            remaining_cents -= line_cents
    total_cents = sum(_cents(line["line_cost"]) for line in lines)
    return {
        "items": lines,
        "total_cost": _money(total_cents),
        "max_budget": None if max_budget is None else _money(_cents(max_budget)),
        "skipped_due_to_budget": skipped,
        "heuristic": "Target stock = max(2 × reorder level, 2 × sales in last 7 days).",
    }


def create_purchase_order_draft(items: list[dict], max_budget: float | None = None) -> dict:
    """Create a persistent LOCAL draft. Backend computes all prices itself."""
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise ValueError("Include between 1 and 50 product lines.")
    budget_cents = None if max_budget is None else _cents(max_budget)
    validated: list[tuple[int, int]] = []
    seen: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each line must have product_id and quantity.")
        product_id, qty = item.get("product_id"), item.get("quantity")
        if type(product_id) is not int or type(qty) is not int:
            raise ValueError("product_id and quantity must be integers.")
        if product_id <= 0 or not 1 <= qty <= 500:
            raise ValueError("Product ID must be positive; quantity must be 1–500.")
        if product_id in seen:
            raise ValueError("Duplicate product IDs are not allowed.")
        seen.add(product_id)
        validated.append((product_id, qty))

    with _connect() as db:
        # SQLite transaction keeps order header and lines consistent.
        products = {}
        for product_id, qty in validated:
            row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if row is None:
                raise ValueError(f"Unknown product ID: {product_id}.")
            products[product_id] = row
        total_cents = sum(products[pid]["unit_cost_cents"] * qty for pid, qty in validated)
        if budget_cents is not None and total_cents > budget_cents:
            raise ValueError(f"Draft costs ${_money(total_cents):.2f}, "
                             f"which exceeds the ${_money(budget_cents):.2f} cap.")
        cur = db.execute("""
            INSERT INTO purchase_orders(status, total_cost_cents, budget_cents, created_at)
            VALUES ('draft', ?, ?, ?)
        """, (total_cents, budget_cents, _now()))
        order_id = cur.lastrowid
        for pid, qty in validated:
            row = products[pid]
            db.execute("""
                INSERT INTO purchase_order_lines(order_id, product_id, product_name,
                    supplier, quantity, unit_cost_cents, line_cost_cents)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_id, pid, row["name"], row["supplier"], qty,
                  row["unit_cost_cents"], qty * row["unit_cost_cents"]))
    return get_purchase_order(order_id)


def get_purchase_order(order_id: int) -> dict | None:
    if type(order_id) is not int or order_id <= 0:
        raise ValueError("Order ID must be a positive integer.")
    with _connect() as db:
        row = db.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            return None
        items = db.execute("SELECT * FROM purchase_order_lines WHERE order_id = ? ORDER BY id",
                           (order_id,)).fetchall()
        return {
            "order_id": row["id"], "status": row["status"],
            "total_cost": _money(row["total_cost_cents"]),
            "max_budget": None if row["budget_cents"] is None else _money(row["budget_cents"]),
            "created_at": row["created_at"], "approved_at": row["approved_at"],
            "items": [{
                "product_id": p["product_id"], "name": p["product_name"],
                "supplier": p["supplier"], "quantity": p["quantity"],
                "unit_cost": _money(p["unit_cost_cents"]),
                "line_cost": _money(p["line_cost_cents"]),
            } for p in items],
        }


def get_purchase_orders(limit: int = 50) -> list[dict]:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Limit must be 1–100.")
    with _connect() as db:
        ids = [r[0] for r in db.execute("SELECT id FROM purchase_orders ORDER BY id DESC LIMIT ?", (limit,))]
    return [get_purchase_order(order_id) for order_id in ids]


def approve_purchase_order(order_id: int, *, confirmed: bool = False) -> dict:
    """Local status transition only. NO purchase is sent to a supplier."""
    if confirmed is not True:
        raise PermissionError("Explicit user confirmation is required.")
    if type(order_id) is not int or order_id <= 0:
        raise ValueError("Order ID must be a positive integer.")
    with _connect() as db:
        row = db.execute("SELECT status, total_cost_cents, budget_cents FROM purchase_orders WHERE id=?",
                         (order_id,)).fetchone()
        if row is None:
            raise ValueError(f"Order #{order_id} does not exist.")
        if row["status"] != "draft":
            raise ValueError(f"Order #{order_id} is already {row['status']}.")
        if row["budget_cents"] is not None and row["total_cost_cents"] > row["budget_cents"]:
            raise ValueError("Order exceeds its stored budget; approval blocked.")
        db.execute("UPDATE purchase_orders SET status='approved', approved_at=? "
                   "WHERE id=? AND status='draft'", (_now(), order_id))
    return get_purchase_order(order_id)


def recommend_smart_restock(max_budget: float, delay_days: int = 0,
                            planning_days: int = 7) -> dict:
    """Explainable cash- and perishability-aware demo planning."""
    from decision_engine import recommend_smart_restock as calculate
    return calculate(max_budget, delay_days, planning_days)


def prepare_smart_order(max_budget: float, delay_days: int = 0,
                        planning_days: int = 7) -> dict:
    """Create a draft ONLY, using server-computed smart quantities and real costs."""
    recommendation = recommend_smart_restock(max_budget, delay_days, planning_days)
    if not recommendation["items"]:
        raise ValueError("No products fit this budget and planning scenario. No draft saved.")
    requested = sorted((item["product_id"], item["quantity"])
                       for item in recommendation["items"])
    # Avoid accidentally saving an identical automated proposal twice.
    # Custom manually reviewed drafts can still be prepared separately.
    with _connect() as db:
        draft_ids = [row[0] for row in db.execute(
            "SELECT id FROM purchase_orders WHERE status='draft' ORDER BY id DESC"
        )]
        for existing_id in draft_ids:
            old_lines = sorted((row["product_id"], row["quantity"])
                for row in db.execute(
                    "SELECT product_id, quantity FROM purchase_order_lines WHERE order_id=?",
                    (existing_id,)
                ))
            if requested == old_lines:
                raise ValueError(
                    f"An identical automated order is already pending as draft #{existing_id}. "
                    "Review that draft in Purchase Orders before preparing another."
                )
    draft = create_purchase_order_draft([
        {"product_id": item["product_id"], "quantity": item["quantity"]}
        for item in recommendation["items"]
    ], max_budget=max_budget)
    return {**draft, "recommendation_method": recommendation["method"],
            "planning_assumptions": recommendation["caveat"],
            "decision_reasons": [
                {"product_id": p["product_id"], "name": p["name"],
                 "quantity": p["quantity"], "reason": p["reason"], "risk": p["risk"]}
                for p in recommendation["items"]
            ],
            "supplier_delay_days": delay_days, "planning_days": planning_days}
