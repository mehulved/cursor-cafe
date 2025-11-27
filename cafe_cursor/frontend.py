"""Frontend application for customers."""

from typing import List, Optional

from .constants import CAFE_LOGO
from .io import IOInterface, ConsoleIO
from .order_system import CafeOrderSystem
from .cart import ShoppingCart


class CafeOrderApp:
    """Command-style terminal interface for Cafe Cursor."""

    def __init__(self, system: Optional[CafeOrderSystem] = None, io: Optional[IOInterface] = None) -> None:
        self.system = system or CafeOrderSystem()
        self.menu = self.system.menu
        self.cart = ShoppingCart()
        self.io = io or ConsoleIO()

    def run(self) -> None:
        """Main REPL loop."""
        self.io.write("\nWelcome to Cafe Cursor!")
        self._print_help()

        while True:
            try:
                raw_input = self.io.readline("\ncmd> ").strip()
            except EOFError:
                self.io.write("\nGoodbye!")
                break
            except KeyboardInterrupt:
                self.io.write("\n\nGoodbye!")
                break

            if not raw_input:
                continue

            parts = raw_input.split()
            command = parts[0].lower()
            args = parts[1:]

            if command == "menu":
                self.menu.display(self.io.write)
            elif command == "add":
                self._handle_add(args)
            elif command == "cart":
                self.cart.display(self.menu, self.io.write)
            elif command == "order":
                self._handle_order()
            elif command == "status":
                self._handle_status(args)
            elif command in {"help", "?"}:
                self._print_help()
            elif command in {"exit", "quit"}:
                self.io.write("See you next time. ☕")
                break
            else:
                self.io.write("Unknown command. Type `help` for options.")

    def _handle_add(self, args: List[str]) -> None:
        """Parse and add menu items to the cart."""
        if not args:
            self.io.write("Usage: add <item #> [quantity]")
            return

        try:
            item_id = int(args[0])
        except ValueError:
            self.io.write("Item number must be numeric.")
            return

        item = self.menu.get_item(item_id)
        if not item:
            self.io.write(f"Item #{item_id} is not on the menu.")
            return

        quantity = 1
        if len(args) >= 2:
            try:
                quantity = int(args[1])
            except ValueError:
                self.io.write("Quantity must be numeric.")
                return

        try:
            self.cart.add(item_id, quantity)
        except ValueError as exc:
            self.io.write(str(exc))
            return

        plural = "s" if quantity > 1 else ""
        self.io.write(f"Added {quantity} {item.name}{plural} to cart.")

    def _handle_order(self) -> None:
        """Create an order from the cart."""
        if self.cart.is_empty():
            self.io.write("Cart is empty. Add items first via `add <item #>`.")
            return

        order = self.system.create_order(self.cart.snapshot())
        self.cart.clear()

        self.io.write("\n" + "=" * 48)
        self.io.write("ORDER CONFIRMED")
        self.io.write(f"Order ID: {order.order_id}")
        self.io.write(f"Use `status {order.order_id}` anytime to check progress.")
        self.io.write("We'll ping you when everything is ready!")
        self.io.write("=" * 48)

    def _handle_status(self, args: List[str]) -> None:
        """Report status for a known order id."""
        if not args:
            self.io.write("Usage: status <order id>")
            return

        try:
            order_id = int(args[0])
        except ValueError:
            self.io.write("Order id must be an integer.")
            return
        order = self.system.get_order(order_id)
        if not order:
            self.io.write(f"No order found with id {order_id}.")
            return

        self.io.write(f"{order_id}: {order.status()}")

    def _print_help(self) -> None:
        """Show supported commands."""
        self.io.write(f"\n{CAFE_LOGO}")
        self.io.write("Commands:")
        self.io.write("  menu                    Show Cafe Cursor offerings")
        self.io.write("  add <item #> [qty]      Add menu item to cart")
        self.io.write("  cart                    Review current cart")
        self.io.write("  order                   Place the current cart")
        self.io.write("  status <order id>       Check order status (integers only)")
        self.io.write("  help                    Show this message")
        self.io.write("  exit                    Quit the app")

