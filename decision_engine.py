"""Explainable cash-aware restocking over StockSense's actual SQLite inventory.

Supplier lead times and shelf lives are *simulated planning assumptions*.
This is a transparent heuristic, NOT a trained demand forecast or expiry tracker.
"""
from __future__ import annotations

import backend


def _ceil_ratio(numerator: int, denominator: int = 7) -> int:
    return (numerator + denominator - 1) // denominator


def recommend_smart_restock(max_budget: float, delay_days: int = 0,
                            planning_days: int = 7) -> dict:
    """Allocate an owner's budget to sales-based shortage risk.

    1. Estimate sales/day from the last 7 days.
    2. Rank products likely to run out before their supplier can replenish them.
    3. For perishables, limit quantities to estimated sales within assumed shelf life.
    4. Purchase in priority order without exceeding the budget.

    Predictions and parameters are demonstrative assumptions, not guarantees.
    """
    if type(delay_days) is not int or not 0 <= delay_days <= 7:
        raise ValueError("Extra supplier delay must be a whole number from 0 to 7 days.")
    if type(planning_days) is not int or not 1 <= planning_days <= 14:
        raise ValueError("Planning horizon must be a whole number from 1 to 14 days.")
    budget_cents = backend._cents(max_budget)
    candidates = []
    for p in backend.get_inventory():
        sales = p["sales_last_7_days"]
        if sales == 0:
            continue  # No velocity signal; don't invent demand.
        stock = p["stock_quantity"]
        lead = p["supplier_lead_days"] + delay_days
        days_cover = round(stock * 7 / sales, 1)
        shortage_before_arrival = max(0, _ceil_ratio(sales * lead) - stock)
        horizon_target = _ceil_ratio(sales * (lead + planning_days))
        desired = max(0, horizon_target - stock)
        shelf_life = p["shelf_life_days"]
        capped_for_perishability = False
        if shelf_life is not None:
            # This cap estimates what can sell before a freshly delivered batch spoils.
            # No batch expiration timestamps are available in the starter database.
            shelf_target = _ceil_ratio(sales * shelf_life)
            shelf_capacity = max(0, shelf_target - stock)
            capped_for_perishability = desired > shelf_capacity
            desired = min(desired, shelf_capacity)
        if desired <= 0:
            continue
        risk = "Before delivery" if shortage_before_arrival > 0 else "Within planning window"
        candidates.append({
            "product_id": p["product_id"], "name": p["name"],
            "supplier": p["supplier"], "current_stock": stock,
            "sales_last_7_days": sales,
            "estimated_daily_sales": round(sales / 7, 2),
            "days_of_cover": days_cover,
            "supplier_lead_days": lead, "shelf_life_days": shelf_life,
            "risk": risk, "shortfall_before_delivery": shortage_before_arrival,
            "max_recommended_qty": min(desired, 500),
            "perishable_cap_applied": capped_for_perishability,
            "unit_cost": p["unit_cost"],
            "_unit_cents": backend._cents(p["unit_cost"], allow_zero=False),
            "_margin_cents": backend._cents(p["selling_price"]) - backend._cents(p["unit_cost"]),
        })
    # Ties broken deterministically: first imminent shortage, then urgency,
    # then projected pre-delivery shortfall, then gross unit margin, then product ID.
    candidates.sort(key=lambda p: (
        0 if p["shortfall_before_delivery"] else 1,
        p["days_of_cover"] - p["supplier_lead_days"],
        -p["shortfall_before_delivery"],
        -p["_margin_cents"], p["product_id"],
    ))
    remaining = budget_cents
    # Fund a narrow near-term safety target across endangered products first,
    # then allocate the remaining money to longer-horizon stock goals. This
    # avoids spending the entire budget on one expensive SKU at the outset.
    for p in candidates:
        p["_funded_qty"] = 0
    for stage in ("near_term", "planning_horizon"):
        for p in candidates:
            max_qty = p["max_recommended_qty"]
            if stage == "near_term":
                # Roughly one extra sales day beyond assumed arrival, no more
                # than the shelf-life-capped target.
                target = min(max_qty, max(0,
                    _ceil_ratio(p["sales_last_7_days"] * (p["supplier_lead_days"] + 1))
                    - p["current_stock"]))
            else:
                target = max_qty
            units_to_add = max(0, target - p["_funded_qty"])
            qty = min(units_to_add, remaining // p["_unit_cents"])
            p["_funded_qty"] += qty
            remaining -= qty * p["_unit_cents"]
    lines = []
    unfunded = []
    for p in candidates:
        qty = p["_funded_qty"]
        if qty < p["max_recommended_qty"]:
            unfunded.append(p["name"])
        if qty == 0:
            continue
        cents = qty * p["_unit_cents"]
        lines.append({
            k: v for k, v in p.items() if not k.startswith("_")
        } | {
            "quantity": qty, "line_cost": backend._money(cents),
            "reason": (
                f"Estimated stock lasts {p['days_of_cover']} days; "
                f"delivery takes {p['supplier_lead_days']} assumed days"
                + (" including simulated delay" if delay_days else "")
                + ("; quantity capped using assumed shelf life" if p["perishable_cap_applied"] else "")
                + ". Purchase arriving after a projected stockout cannot prevent that earlier shortage."
            ),
        })
    return {
        "items": lines,
        "total_cost": backend._money(budget_cents - remaining),
        "max_budget": backend._money(budget_cents),
        "remaining_budget": backend._money(remaining),
        "supplier_delay_days": delay_days,
        "planning_days": planning_days,
        "at_risk_before_delivery": sum(bool(p["shortfall_before_delivery"]) for p in candidates),
        "not_fully_funded": unfunded,
        "method": "Seven-day average sales; assumed supplier lead plus horizon; shelf-life cap for perishables; first allocate one day of post-arrival safety to shortage-risk products, then use remaining budget for target quantities.",
        "caveat": "SIMULATED lead times and shelf lives. Orders cannot prevent shortages occurring before delivery. No live supplier data, batch expiry tracking, validated forecasts, or measured savings.",
    }
