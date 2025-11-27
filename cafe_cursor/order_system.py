"""Order system for Cafe Cursor."""

from datetime import datetime
from typing import Dict, List, Optional

from .database import CafeDatabase
from .menu import CafeMenu
from .models import Order


class CafeOrderSystem:
    """Shared state for menu and placed orders."""

    def __init__(self, db_path: str = "cafe_cursor.db") -> None:
        self.db = CafeDatabase(db_path)
        self.menu = CafeMenu(db=self.db)
        self.orders: Dict[int, Order] = self.db.load_orders()

    def refresh_orders(self) -> None:
        """Reload cached orders from the database."""
        self.orders = self.db.load_orders()

    def list_orders(self, refresh: bool = True) -> List[Order]:
        """Return all orders sorted by id."""
        if refresh:
            self.refresh_orders()
        return [self.orders[order_id] for order_id in sorted(self.orders)]

    def create_order(self, snapshot: Dict[int, int]) -> Order:
        """Persist an order and return it."""
        order = self.db.create_order(snapshot)
        self.orders[order.order_id] = order
        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        order = self.db.fetch_order(order_id)
        if order:
            self.orders[order_id] = order
        return order

    def mark_ready(self, order_id: int) -> Optional[Order]:
        """Set the ready timestamp for an order."""
        order = self.get_order(order_id)
        if not order:
            return None
        ready_at = datetime.now()
        self.db.update_ready_time(order_id, ready_at)
        order.ready_at = ready_at
        self.orders[order_id] = order
        return order

    def refresh_menu(self) -> None:
        """Reload menu items from the database."""
        self.menu.items = self.db.load_menu_items()

    def add_menu_item(self, item_id: int, name: str) -> bool:
        """Add a menu item and refresh the menu. Returns True if successful."""
        if self.db.add_menu_item(item_id, name):
            self.refresh_menu()
            return True
        return False

    def remove_menu_item(self, item_id: int) -> bool:
        """Remove a menu item and refresh the menu. Returns True if successful."""
        if self.db.remove_menu_item(item_id):
            self.refresh_menu()
            return True
        return False

