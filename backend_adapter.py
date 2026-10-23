"""ONLY file to edit when Member 1's final backend uses different function names.

Agent and frontend use InventoryBackend's public methods, not SQLite directly.
"""
import backend


class InventoryBackend:
    def initialize(self) -> None:
        backend.initialize_database()

    def get_inventory(self) -> list[dict]:
        return backend.get_inventory()

    def add_product(self, name: str, supplier: str, stock_quantity: int,
                    reorder_level: int, sales_last_7_days: int,
                    unit_cost: float, selling_price: float,
                    supplier_lead_days: int = 3,
                    shelf_life_days: int | None = None) -> dict:
        return backend.add_product(
            name=name, supplier=supplier, stock_quantity=stock_quantity,
            reorder_level=reorder_level, sales_last_7_days=sales_last_7_days,
            unit_cost=unit_cost, selling_price=selling_price,
            supplier_lead_days=supplier_lead_days,
            shelf_life_days=shelf_life_days,
        )

    def get_low_stock(self) -> list[dict]:
        return backend.get_low_stock_products()

    def recommend_restock(self, max_budget: float | None = None) -> dict:
        return backend.recommend_restock(max_budget=max_budget)

    def recommend_smart_restock(self, max_budget: float, delay_days: int = 0,
                                planning_days: int = 7) -> dict:
        return backend.recommend_smart_restock(max_budget, delay_days, planning_days)

    def prepare_smart_order(self, max_budget: float, delay_days: int = 0,
                            planning_days: int = 7) -> dict:
        return backend.prepare_smart_order(max_budget, delay_days, planning_days)

    def create_draft(self, items: list[dict], max_budget: float | None = None) -> dict:
        return backend.create_purchase_order_draft(items=items, max_budget=max_budget)

    def get_order(self, order_id: int) -> dict | None:
        return backend.get_purchase_order(order_id)

    def get_orders(self) -> list[dict]:
        return backend.get_purchase_orders()

    def approve_order(self, order_id: int, *, confirmed: bool = False) -> dict:
        return backend.approve_purchase_order(order_id, confirmed=confirmed)
