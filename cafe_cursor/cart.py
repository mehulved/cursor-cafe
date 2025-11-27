"""Shopping cart for Cafe Cursor."""

from collections import defaultdict
from typing import Callable, Dict

from .constants import CAFE_LOGO
from .menu import CafeMenu


class ShoppingCart:
    """Simple in-memory cart keyed by menu item identifier."""

    def __init__(self) -> None:
        self.items: Dict[int, int] = defaultdict(int)

    def add(self, item_id: int, quantity: int = 1) -> None:
        """Add quantity of item to cart."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        self.items[item_id] += quantity

    def is_empty(self) -> bool:
        return not self.items

    def clear(self) -> None:
        self.items.clear()

    def snapshot(self) -> Dict[int, int]:
        """Return a shallow copy for order storage."""
        return dict(self.items)

    def display(self, menu: CafeMenu, write: Callable[[str], None] = print) -> None:
        """Render cart contents."""
        write(f"\n{CAFE_LOGO}")
        if not self.items:
            write("\nCart is empty. Use `add <item #>` to begin.")
            return

        write("\n--- Cart ---")
        for item_id, quantity in self.items.items():
            menu_item = menu.get_item(item_id)
            if not menu_item:
                continue  # Should never happen
            write(f"{menu_item.name} x{quantity}")
        write("------------")

