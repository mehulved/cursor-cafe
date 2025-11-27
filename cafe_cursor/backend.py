"""Backend application for staff."""

from typing import List, Optional

from .constants import CAFE_LOGO
from .io import IOInterface, ConsoleIO
from .menu import summarize_order_items
from .order_system import CafeOrderSystem


class CafeBackendApp:
    """Restricted command interface for staff/backoffice."""

    def __init__(self, system: Optional[CafeOrderSystem] = None, io: Optional[IOInterface] = None) -> None:
        self.system = system or CafeOrderSystem()
        self.menu = self.system.menu
        self.io = io or ConsoleIO()

    def run(self) -> None:
        """Backend REPL loop."""
        self.io.write("\nCafe Cursor Backend Console")
        self._print_help()

        while True:
            try:
                raw_input = self.io.readline("\nbknd> ").strip()
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

            if command == "list":
                self._handle_list()
            elif command == "status":
                self._handle_status(args)
            elif command == "ready":
                self._handle_ready(args)
            elif command == "menu-list":
                self._handle_menu_list()
            elif command == "menu-add":
                self._handle_menu_add(args)
            elif command == "menu-remove":
                self._handle_menu_remove(args)
            elif command in {"help", "?"}:
                self._print_help()
            elif command in {"exit", "quit"}:
                self.io.write("See you next time. ☕")
                break
            else:
                self.io.write("Unknown backend command. Type `help` for options.")

    def _handle_list(self) -> None:
        orders = self.system.list_orders()
        if not orders:
            self.io.write("\nNo orders found.")
            return

        self.io.write("\nCurrent Orders:")
        for order in orders:
            status = "READY" if order.ready_at else "PREP"
            placed = order.placed_at.strftime("%Y-%m-%d %H:%M:%S")
            ready = order.ready_at.strftime("%Y-%m-%d %H:%M:%S") if order.ready_at else "-"
            summary = summarize_order_items(self.menu, order.items)
            self.io.write(f"- {order.order_id} [{status}] placed {placed} ready {ready}")
            self.io.write(f"    {summary}")

    def _handle_status(self, args: List[str]) -> None:
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

        placed = order.placed_at.strftime("%Y-%m-%d %H:%M:%S")
        ready = order.ready_at.strftime("%Y-%m-%d %H:%M:%S") if order.ready_at else "-"
        self.io.write(f"Order {order_id}: {order.status()}")
        self.io.write(f"  Placed: {placed}")
        self.io.write(f"  Ready:  {ready}")
        self.io.write(f"  Items:  {summarize_order_items(self.menu, order.items)}")

    def _handle_ready(self, args: List[str]) -> None:
        if not args:
            self.io.write("Usage: ready <order id>")
            return

        try:
            order_id = int(args[0])
        except ValueError:
            self.io.write("Order id must be an integer.")
            return

        order = self.system.mark_ready(order_id)
        if not order:
            self.io.write(f"No order found with id {order_id}.")
            return

        ready_at = order.ready_at.strftime("%Y-%m-%d %H:%M:%S") if order.ready_at else "unknown"
        self.io.write(f"Order {order_id} marked ready at {ready_at}.")

    def _handle_menu_list(self) -> None:
        """Display all menu items."""
        items = self.menu.all_items()
        if not items:
            self.io.write("\nNo menu items found.")
            return

        self.io.write("\nMenu Items:")
        for item in items:
            self.io.write(f"  {item.identifier:2d}. {item.name}")

    def _handle_menu_add(self, args: List[str]) -> None:
        """Add a new menu item."""
        if len(args) < 2:
            self.io.write("Usage: menu-add <item id> <name>")
            self.io.write("Example: menu-add 14 'New Coffee'")
            return

        try:
            item_id = int(args[0])
        except ValueError:
            self.io.write("Item id must be an integer.")
            return

        name = " ".join(args[1:])
        if self.system.add_menu_item(item_id, name):
            self.io.write(f"Menu item {item_id} '{name}' added successfully.")
        else:
            self.io.write(f"Failed to add menu item. Item id {item_id} may already exist.")

    def _handle_menu_remove(self, args: List[str]) -> None:
        """Remove a menu item."""
        if not args:
            self.io.write("Usage: menu-remove <item id>")
            return

        try:
            item_id = int(args[0])
        except ValueError:
            self.io.write("Item id must be an integer.")
            return

        item = self.menu.get_item(item_id)
        if not item:
            self.io.write(f"Menu item {item_id} not found.")
            return

        if self.system.remove_menu_item(item_id):
            self.io.write(f"Menu item {item_id} '{item.name}' removed successfully.")
        else:
            self.io.write(f"Failed to remove menu item {item_id}.")

    def _print_help(self) -> None:
        self.io.write(f"\n{CAFE_LOGO}")
        self.io.write("Backend Commands:")
        self.io.write("  list                    Show all orders and status")
        self.io.write("  status <order id>       Show details for one order")
        self.io.write("  ready <order id>        Mark order as ready")
        self.io.write("  menu-list               Show all menu items")
        self.io.write("  menu-add <id> <name>    Add a new menu item")
        self.io.write("  menu-remove <id>       Remove a menu item")
        self.io.write("  help                    Show this message")
        self.io.write("  exit                    Quit the console")

