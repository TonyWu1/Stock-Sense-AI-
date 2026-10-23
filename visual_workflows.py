"""Pure Streamlit presentation + owner-controlled visual order cart.

No database writes happen until the owner explicitly requests a local draft.
Prices, stock and suppliers always come from InventoryBackend's SQLite rows.
"""
from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from io import StringIO


# Emoji-based illustrations are offline-safe; no third-party product imagery or fake SKUs.
def product_symbol(name: str) -> tuple[str, str]:
    n = name.casefold()
    for words, emoji, tint in [
        (("milk", "dairy"), "🥛", "aqua"),
        (("egg",), "🥚", "amber"),
        (("bread", "loaf", "biscuit"), "🍞", "amber"),
        (("banana", "fruit"), "🍌", "amber"),
        (("rice", "sugar", "flour"), "🍚", "lavender"),
        (("bean",), "🫘", "lavender"),
        (("olive", "oil"), "🫒", "green"),
        (("pasta",), "🍝", "amber"),
        (("cheese",), "🧀", "amber"),
        (("coffee",), "☕", "amber"),
        (("juice", "orange"), "🍊", "aqua"),
        (("water",), "💧", "aqua"),
        (("chicken", "meat"), "🍗", "pink"),
        (("soap", "clean"), "🧼", "aqua"),
        (("cola", "soda", "drink", "pepsi"), "🥤", "pink"),
    ]:
        if any(word in n for word in words):
            return emoji, tint
    return "📦", "lavender"


def cents(amount) -> int:
    return int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _inventory_status(p: dict) -> tuple[str, str]:
    qty = int(p["stock_quantity"])
    level = int(p["reorder_level"])
    if qty <= 0:
        return "Out of stock", "danger"
    if qty <= level:
        return "Low stock", "warning"
    return "Healthy", "healthy"


def _card_html(p: dict, *, compact: bool = False) -> str:
    title = escape(str(p["name"]))
    supplier = escape(str(p["supplier"]))
    emoji, tint = product_symbol(str(p["name"]))
    badge, badge_css = _inventory_status(p)
    qty = int(p["stock_quantity"])
    threshold = int(p["reorder_level"])
    amount = cents(p["unit_cost"]) / 100
    return (
        f'<div class="v-product {"v-compact" if compact else ""}">'
        f'<div class="v-product-art v-art-{tint}"><span role="img" aria-label="Product illustration">{emoji}</span>'
        f'<div class="v-stock-pill v-{badge_css}">{escape(badge)}</div></div>'
        f'<div class="v-product-name" title="{title}">{title}</div>'
        f'<div class="v-product-supplier" title="{supplier}">{supplier}</div>'
        f'<div class="v-product-meta"><span>On hand <b>{qty}</b></span>'
        f'<span>Reorder <b>{threshold}</b></span></div>'
        f'<div class="v-product-price">${amount:,.2f}<small> / unit</small></div>'
        f'</div>'
    )


def add_to_cart(st, product_id: int, count: int = 1) -> None:
    """Used by both the catalog and purchase builder."""
    cart = st.session_state.setdefault("ss_visual_cart_v2", {})
    current = int(cart.get(product_id, 0))
    updated = min(500, current + count)
    cart[product_id] = updated
    # Update quantity control before it is instantiated on the next run.
    st.session_state[f"ss_visual_qty_{product_id}"] = updated


def render_inventory_gallery(st, products: list[dict], go_to_page) -> None:
    """Gallery reflects the same active Inventory filters (never invented products)."""
    st.markdown(
        '<div class="v-section-head"><div><span class="v-eyebrow">VISUAL CATALOG</span>'
        '<h2>Shop your inventory visually</h2>'
        '<p>Every tile is an actual SQLite product. Add items to your purchasing cart.</p>'
        '</div><span class="v-mini-chip">Local catalog</span></div>',
        unsafe_allow_html=True,
    )
    if not products:
        st.info("No products match the filters above.")
        return
    # No external images: colored illustrations and product details remain available offline.
    page_size = 8
    page_count = max(1, (len(products) + page_size - 1) // page_size)
    page_no = st.selectbox("Gallery page", list(range(1, page_count + 1)),
                           format_func=lambda n: f"Page {n} of {page_count}",
                           key="ss_inventory_gallery_page_v2") if page_count > 1 else 1
    slice_rows = products[(page_no - 1) * page_size:page_no * page_size]
    for start in range(0, len(slice_rows), 4):
        columns = st.columns(4, gap="small")
        for col, p in zip(columns, slice_rows[start:start+4]):
            with col:
                with st.container(border=True):
                    st.markdown(_card_html(p), unsafe_allow_html=True)
                    if st.button("＋ Add to order", key=f"ss_catalog_add_{p['product_id']}",
                                 width="stretch"):
                        add_to_cart(st, int(p["product_id"]))
                        go_to_page("Purchase Orders")
                        st.rerun()
    st.caption("Product tiles are illustrations, not real product photos. Purchase costs are taken from SQLite.")


def cart_lines(cart: dict, products_by_id: dict[int, dict]) -> tuple[list[dict], int]:
    lines = []
    total_cents = 0
    for pid in sorted(cart):
        if pid not in products_by_id:
            continue
        qty = int(cart[pid])
        if qty <= 0:
            continue
        p = products_by_id[pid]
        cost_cents = cents(p["unit_cost"])
        line_cents = qty * cost_cents
        total_cents += line_cents
        lines.append({
            "product_id": pid, "Product": p["name"], "Supplier": p["supplier"],
            "Qty": qty, "Unit cost": cost_cents / 100,
            "Line cost": line_cents / 100,
        })
    return lines, total_cents


def draft_overlaps(orders: list[dict], selected_ids: set[int]) -> list[dict]:
    overlaps = []
    for order in orders:
        if str(order.get("status", "")).lower() != "draft":
            continue
        shared = [item for item in order.get("items", [])
                  if item.get("product_id") in selected_ids]
        if shared:
            overlaps.append({"order_id": order["order_id"], "items": shared})
    return overlaps


def _supplier_csv(lines: list[dict]) -> str:
    fields = ["Supplier", "Product", "Qty", "Unit cost", "Line cost"]
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for line in sorted(lines, key=lambda r: (r["Supplier"], r["Product"])):
        writer.writerow({field: line[field] for field in fields})
    return buf.getvalue()


def render_visual_purchase_builder(st, backend, orders: list[dict]) -> None:
    """Real catalog -> interactive cart -> budget validation -> explicitly saved draft.

    All state is local to a browser session until create_draft() is called.
    No direct SQL, no supplier action, no order approval from this screen.
    """
    products = backend.get_inventory()
    by_id = {int(p["product_id"]): p for p in products}
    cart = st.session_state.setdefault("ss_visual_cart_v2", {})
    for key in list(cart):
        if key not in by_id or cart[key] <= 0:
            cart.pop(key, None)

    notice = st.session_state.pop("ss_visual_saved_notice_v2", None)
    if notice:
        st.success(notice)

    st.markdown(
        '<div class="v-builder-hero"><div class="v-eyebrow">BUSINESS OWNER WORKSPACE</div>'
        '<h2>Visual Purchase Builder</h2>'
        '<p>Choose products, set quantities, compare suppliers, and save a local draft — '
        'without sending a purchase to anyone.</p></div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.75, 1], gap="medium")
    with left:
        st.markdown('<div class="v-section-head"><div><h3>Product catalog</h3>'
                    '<p>Click Add on any item to build a cart from your SQLite stock.</p>'
                    '</div><span class="v-mini-chip">Real catalog data</span></div>',
                    unsafe_allow_html=True)
        search_col, supplier_col = st.columns([1.25, 1], gap="small")
        with search_col:
            search = st.text_input("Search products", placeholder="Search milk, oil, coffee…",
                                   key="ss_visual_search_v2").strip().casefold()
        with supplier_col:
            suppliers = sorted({str(p["supplier"]) for p in products}, key=str.casefold)
            chosen_supplier = st.selectbox("Supplier", ["All suppliers", *suppliers],
                                           key="ss_visual_supplier_v2")
        catalog = [p for p in products if
                   (not search or search in str(p["name"]).casefold() or
                    search in str(p["supplier"]).casefold()) and
                   (chosen_supplier == "All suppliers" or p["supplier"] == chosen_supplier)]
        catalog.sort(key=lambda p: (int(p["stock_quantity"]) > int(p["reorder_level"]),
                                    int(p["stock_quantity"]) / max(1, int(p["reorder_level"])),
                                    str(p["name"]).casefold()))
        if not catalog:
            st.info("No matching products. Try changing the search or supplier.")
        else:
            page_size = 6
            page_count = max(1, (len(catalog) + page_size - 1) // page_size)
            page_no = st.selectbox("Catalog page", list(range(1, page_count+1)),
                                   format_func=lambda n:f"Page {n} of {page_count}",
                                   key="ss_visual_page_v2") if page_count > 1 else 1
            current = catalog[(page_no-1)*page_size:page_no*page_size]
            for i in range(0, len(current), 3):
                columns = st.columns(3, gap="small")
                for col, product in zip(columns, current[i:i+3]):
                    with col:
                        with st.container(border=True):
                            st.markdown(_card_html(product, compact=True), unsafe_allow_html=True)
                            pid = int(product["product_id"])
                            if st.button("＋ Add to cart", key=f"ss_visual_add_{pid}",
                                         width="stretch"):
                                add_to_cart(st, pid)
                                st.rerun()

    with right:
        st.markdown('<div class="v-cart-header"><div><span class="v-eyebrow">LIVE ORDER CART</span>'
                    '<h3>Order summary</h3></div>'
                    f'<span class="v-cart-count">{len(cart)} product(s)</span></div>',
                    unsafe_allow_html=True)
        if not cart:
            st.markdown('<div class="v-cart-empty">🛒<br><strong>Nothing in your cart yet</strong>'
                        '<p>Add a product on the left to start planning your next order.</p></div>',
                        unsafe_allow_html=True)
        else:
            for pid in list(sorted(cart)):
                if pid not in by_id:
                    continue
                p = by_id[pid]
                emoji, _ = product_symbol(str(p["name"]))
                st.markdown(
                    f'<div class="v-cart-product"><span class="v-cart-emoji">{emoji}</span>'
                    f'<span><b>{escape(str(p["name"]))}</b><small>'
                    f'${cents(p["unit_cost"])/100:,.2f} / unit</small></span></div>',
                    unsafe_allow_html=True,
                )
                qty_col, remove_col = st.columns([2.3, 1], gap="small")
                with qty_col:
                    key = f"ss_visual_qty_{pid}"
                    if key not in st.session_state:
                        st.session_state[key] = int(cart[pid])
                    requested = st.number_input(f"Quantity · {p['name']}", min_value=1,
                                                max_value=500, step=1, key=key)
                    cart[pid] = int(requested)
                with remove_col:
                    st.markdown('<div class="v-remove-spacer"></div>', unsafe_allow_html=True)
                    if st.button("Remove", key=f"ss_visual_remove_{pid}", width="stretch"):
                        cart.pop(pid, None)
                        st.rerun()
        lines, total = cart_lines(cart, by_id)
        st.markdown('<div class="v-cart-total"><span>Estimated total</span>'
                    f'<strong>${total/100:,.2f}</strong></div>', unsafe_allow_html=True)
        budget = st.number_input("Maximum budget (USD)", min_value=0.0,
                                 max_value=1000000.0, value=150.0, step=10.0,
                                 format="%.2f", key="ss_visual_budget_v2")
        cap = cents(budget)
        remaining = cap - total
        used_pct = round(100*total/cap) if cap else (100 if total else 0)
        st.markdown(
            f'<div class="v-budget-top"><span>Budget used · {used_pct}%</span>'
            f'<span>${remaining/100:,.2f} remaining</span></div>'
            '<div class="v-budget-track"><div class="v-budget-fill" '
            f'style="width:{min(100,max(0,used_pct))}%;background:'
            f'{"#ff6b89" if remaining < 0 else "linear-gradient(90deg,#2ad4d0,#267be5)"}'
            '"></div></div>', unsafe_allow_html=True,
        )
        if remaining < 0:
            st.error(f"Order is ${-remaining/100:,.2f} over budget. Reduce quantities first.")
        suppliers = {}
        for line in lines:
            suppliers.setdefault(line["Supplier"], {"lines": 0, "cents": 0})
            suppliers[line["Supplier"]]["lines"] += 1
            suppliers[line["Supplier"]]["cents"] += cents(line["Line cost"])
        if suppliers:
            st.markdown('<div class="v-eyebrow v-space-top">SUPPLIER BREAKDOWN</div>',
                        unsafe_allow_html=True)
            for name, details in sorted(suppliers.items()):
                st.markdown(
                    f'<div class="v-supplier-row"><span>{escape(str(name))}</span>'
                    f'<small>{details["lines"]} line(s) · ${details["cents"]/100:,.2f}</small></div>',
                    unsafe_allow_html=True,
                )
            st.download_button("↓ Supplier buying list (CSV)", _supplier_csv(lines),
                               "stocksense_supplier_buying_list.csv", "text/csv",
                               key="ss_visual_supplier_export_v2", width="stretch")

        overlap = draft_overlaps(orders, {line["product_id"] for line in lines})
        if overlap:
            overlapping_ids = ", ".join(f"#{order['order_id']}" for order in overlap[:8])
            st.warning(f"Duplicate-purchase warning: your cart overlaps pending draft(s) {overlapping_ids}.")
            overlap_ack = st.checkbox("I reviewed those drafts and still want a separate order.",
                                      key="ss_visual_overlap_ack_v2")
        else:
            overlap_ack = True
        confirmation = st.checkbox("I reviewed this cart and want to SAVE A LOCAL DRAFT only.",
                                   key="ss_visual_save_ack_v2")
        st.caption("Local draft only. No supplier connection, payment, inventory receipt, or automatic approval.")
        if st.button("Save as local draft", type="primary", width="stretch",
                     disabled=not(bool(lines) and remaining >= 0 and overlap_ack and confirmation),
                     key="ss_visual_save_btn_v2"):
            try:
                saved = backend.create_draft(
                    [{"product_id": line["product_id"], "quantity": line["Qty"]}
                     for line in lines], max_budget=float(budget),
                )
                if saved.get("status") != "draft" or cents(saved["total_cost"]) > cap:
                    st.error("Unexpected database result. Check order history before trying again.")
                else:
                    st.session_state["ss_visual_cart_v2"] = {}
                    st.session_state["ss_visual_saved_notice_v2"] = (
                        f"Saved local draft #{saved['order_id']} for ${saved['total_cost']:.2f}. "
                        "Review and explicitly approve it in order history below."
                    )
                    st.rerun()
            except (ValueError, PermissionError, TypeError) as exc:
                st.error(f"Order not saved: {exc}")
            except Exception:
                st.error("The draft couldn't be saved. Check saved order history before retrying.")

        if cart:
            if st.button("Clear cart", key="ss_visual_clear_v2", width="stretch"):
                st.session_state["ss_visual_cart_v2"] = {}
                st.rerun()

    st.caption("Product illustrations are category icons. Catalog, quantities, prices, supplier groups, and saved drafts come from SQLite.")
