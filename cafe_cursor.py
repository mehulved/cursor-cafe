#!/usr/bin/env python3
"""
Cafe Cursor - Lightweight terminal ordering app

Usage highlights:
    menu                     -> show available drinks/snacks
    add <item #> [quantity]  -> add menu item to cart
    order                    -> place current cart as order
    status <order id>        -> check order progress
    help                     -> list all supported commands
    exit                     -> quit the app
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CAFE_LOGO = r"""
                                                                                                                
                                                                                                                
  ,----..                                         ,----..                                                       
 /   /   \              .--.,                    /   /   \                                                      
|   :     :           ,--.'  \                  |   :     :         ,--,  __  ,-.              ,---.    __  ,-. 
.   |  ;. /           |  | /\/                  .   |  ;. /       ,'_ /|,' ,'/ /|  .--.--.    '   ,'\ ,' ,'/ /| 
.   ; /--`   ,--.--.  :  : :     ,---.          .   ; /--`   .--. |  | :'  | |' | /  /    '  /   /   |'  | |' | 
;   | ;     /       \ :  | |-,  /     \         ;   | ;    ,'_ /| :  . ||  |   ,'|  :  /`./ .   ; ,. :|  |   ,' 
|   : |    .--.  .-. ||  : :/| /    /  |        |   : |    |  ' | |  . .'  :  /  |  :  ;_   '   | |: :'  :  /   
.   | '___  \__\/: . .|  |  .'.    ' / |        .   | '___ |  | ' |  | ||  | '    \  \    `.'   | .; :|  | '    
'   ; : .'| ," .--.; |'  : '  '   ;   /|        '   ; : .'|:  | : ;  ; |;  : |     `----.   \   :    |;  : |    
'   | '/  :/  /  ,.  ||  | |  '   |  / |        '   | '/  :'  :  `--'   \  , ;    /  /`--'  /\   \  / |  , ;    
|   :    /;  :   .'   \  : \  |   :    |        |   :    / :  ,      .-./---'    '--'.     /  `----'   ---'     
 \   \ .' |  ,     .-./  |,'   \   \  /          \   \ .'   `--`----'              `--'---'                     
  `---`    `--`---'   `--'      `----'            `---`                                                         
                                                                                                                
"""


@dataclass(frozen=True)
class MenuItem:
    """Represents a single menu entry."""

    identifier: int
    name: str


class CafeMenu:
    """Stores and renders the Cafe Cursor menu."""

    def __init__(self) -> None:
        self.items: Dict[int, MenuItem] = {
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

    def display(self) -> None:
        """Print the menu as a simple numbered list."""
        print("\n" + "=" * 48)
        print("            CAFE CURSOR MENU")
        print("=" * 48)

        for item_id in sorted(self.items):
            item = self.items[item_id]
            print(f"  {item.identifier:2d}. {item.name}")

        print("\nUse `add <item #>` to place things in your cart.")
        print("=" * 48)

    def get_item(self, identifier: int) -> Optional[MenuItem]:
        """Return a menu item by identifier."""
        return self.items.get(identifier)

    def all_items(self) -> List[MenuItem]:
        """Expose items as a list (sorted by id)."""
        return [self.items[item_id] for item_id in sorted(self.items)]


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

    def display(self, menu: CafeMenu) -> None:
        """Render cart contents."""
        print(f"\n{CAFE_LOGO}")
        if not self.items:
            print("\nCart is empty. Use `add <item #>` to begin.")
            return

        print("\n--- Cart ---")
        for item_id, quantity in self.items.items():
            menu_item = menu.get_item(item_id)
            if not menu_item:
                continue  # Should never happen
            print(f"{menu_item.name} x{quantity}")
        print("------------")


@dataclass
class Order:
    """Represents a placed order."""

    order_id: int
    items: Dict[int, int]
    placed_at: datetime

    def status(self) -> str:
        """Derive a friendly status message from elapsed time."""
        elapsed = datetime.now() - self.placed_at
        if elapsed < timedelta(minutes=2):
            return "Barista received your order."
        if elapsed < timedelta(minutes=5):
            return "Drinks are being prepared."
        return "Ready for pickup!"


class CafeOrderApp:
    """Command-style terminal interface for Cafe Cursor."""

    def __init__(self) -> None:
        self.menu = CafeMenu()
        self.cart = ShoppingCart()
        self.orders: Dict[int, Order] = {}
        self.order_sequence = 1

    def run(self) -> None:
        """Main REPL loop."""
        print("\nWelcome to Cafe Cursor!")
        self._print_help()

        while True:
            try:
                raw_input = input("\ncmd> ").strip()
            except EOFError:
                print("\nGoodbye!")
                break
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break

            if not raw_input:
                continue

            parts = raw_input.split()
            command = parts[0].lower()
            args = parts[1:]

            if command == "menu":
                self.menu.display()
            elif command == "add":
                self._handle_add(args)
            elif command == "cart":
                self.cart.display(self.menu)
            elif command == "order":
                self._handle_order()
            elif command == "status":
                self._handle_status(args)
            elif command in {"help", "?"}:
                self._print_help()
            elif command in {"exit", "quit"}:
                print("See you next time. ☕")
                break
            else:
                print("Unknown command. Type `help` for options.")

    def _handle_add(self, args: List[str]) -> None:
        """Parse and add menu items to the cart."""
        if not args:
            print("Usage: add <item #> [quantity]")
            return

        try:
            item_id = int(args[0])
        except ValueError:
            print("Item number must be numeric.")
            return

        item = self.menu.get_item(item_id)
        if not item:
            print(f"Item #{item_id} is not on the menu.")
            return

        quantity = 1
        if len(args) >= 2:
            try:
                quantity = int(args[1])
            except ValueError:
                print("Quantity must be numeric.")
                return

        try:
            self.cart.add(item_id, quantity)
        except ValueError as exc:
            print(str(exc))
            return

        plural = "s" if quantity > 1 else ""
        print(f"Added {quantity} {item.name}{plural} to cart.")

    def _handle_order(self) -> None:
        """Create an order from the cart."""
        if self.cart.is_empty():
            print("Cart is empty. Add items first via `add <item #>`.")
            return

        order_id = self.order_sequence
        self.order_sequence += 1

        order = Order(order_id=order_id, items=self.cart.snapshot(), placed_at=datetime.now())
        self.orders[order_id] = order
        self.cart.clear()

        print("\n" + "=" * 48)
        print("ORDER CONFIRMED")
        print(f"Order ID: {order_id}")
        print("Use `status {order_id}` anytime to check progress.")
        print("We'll ping you when everything is ready!")
        print("=" * 48)

    def _handle_status(self, args: List[str]) -> None:
        """Report status for a known order id."""
        if not args:
            print("Usage: status <order id>")
            return

        try:
            order_id = int(args[0])
        except ValueError:
            print("Order id must be an integer.")
            return
        order = self.orders.get(order_id)
        if not order:
            print(f"No order found with id {order_id}.")
            return

        print(f"{order_id}: {order.status()}")

    def _print_help(self) -> None:
        """Show supported commands."""
        print(f"\n{CAFE_LOGO}")
        print("Commands:")
        print("  menu                    Show Cafe Cursor offerings")
        print("  add <item #> [qty]      Add menu item to cart")
        print("  cart                    Review current cart")
        print("  order                   Place the current cart")
        print("  status <order id>       Check order status (integers only)")
        print("  help                    Show this message")
        print("  exit                    Quit the app")


def main() -> None:
    app = CafeOrderApp()
    app.run()


if __name__ == "__main__":
    main()

