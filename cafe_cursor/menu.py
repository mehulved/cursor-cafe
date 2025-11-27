"""Menu management for Cafe Cursor."""

from typing import Callable, Dict, List, Optional

from .database import CafeDatabase
from .models import MenuItem


class CafeMenu:
    """Stores and renders the Cafe Cursor menu."""

    def __init__(self, db: Optional[CafeDatabase] = None) -> None:
        self.db = db
        self.items: Dict[int, MenuItem] = {}
        if self.db:
            self.items = self.db.load_menu_items()
        else:
            # Fallback to hardcoded menu if no database provided
            self.items = {
                1: MenuItem(1, "Black (Hot)"),
                2: MenuItem(2, "Black (Cold)"),
                3: MenuItem(3, "White (Hot)"),
                4: MenuItem(4, "White (Cold)"),
                5: MenuItem(5, "Mocha (Hot)"),
                6: MenuItem(6, "Mocha (Cold)"),
                7: MenuItem(7, "Hot Chocolate"),
                8: MenuItem(8, "Cold Chocolate"),
                9: MenuItem(9, "Espresso Tonic"),
                10: MenuItem(10, "Strawberry Latte"),
                11: MenuItem(11, "Vanilla Latte"),
                12: MenuItem(12, "Chocolate Cookies"),
                13: MenuItem(13, "Strawberry Cookies"),
            }

    def display(self, write: Callable[[str], None] = print) -> None:
        """Print the menu as a simple numbered list."""
        write("\n" + "=" * 48)
        write("            CAFE CURSOR MENU")
        write("=" * 48)

        for item_id in sorted(self.items):
            item = self.items[item_id]
            write(f"  {item.identifier:2d}. {item.name}")

        write("\nUse `add <item #>` to place things in your cart.")
        write("=" * 48)

    def get_item(self, identifier: int) -> Optional[MenuItem]:
        """Return a menu item by identifier."""
        return self.items.get(identifier)

    def all_items(self) -> List[MenuItem]:
        """Expose items as a list (sorted by id)."""
        return [self.items[item_id] for item_id in sorted(self.items)]


def summarize_order_items(menu: CafeMenu, items: Dict[int, int]) -> str:
    """Create a human readable items summary for an order."""
    parts: List[str] = []
    for item_id, qty in items.items():
        menu_item = menu.get_item(item_id)
        name = menu_item.name if menu_item else f"Item {item_id}"
        parts.append(f"{name} x{qty}")
    return ", ".join(parts) if parts else "No items"

