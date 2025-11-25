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

import argparse
import json
import socketserver
import sqlite3
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

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


@dataclass
class Order:
    """Represents a placed order."""

    order_id: int
    items: Dict[int, int]
    placed_at: datetime
    ready_at: Optional[datetime] = None

    def status(self) -> str:
        """Derive a friendly status message from elapsed time."""
        if self.ready_at:
            return "Ready for pickup!"

        elapsed = datetime.now() - self.placed_at
        if elapsed < timedelta(minutes=2):
            return "Barista received your order."
        if elapsed < timedelta(minutes=5):
            return "Drinks are being prepared."
        return "Almost ready..."


class CafeDatabase:
    """Lightweight SQLite wrapper for persisting orders."""

    def __init__(self, path: str = "cafe_cursor.db") -> None:
        self.path = path
        self._lock = threading.Lock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    items TEXT NOT NULL,
                    placed_at TEXT NOT NULL,
                    ready_at TEXT
                )
                """
            )
            conn.commit()

    def load_orders(self) -> Dict[int, Order]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id, items, placed_at, ready_at FROM orders ORDER BY id").fetchall()
        return {row[0]: self._row_to_order(row) for row in rows}

    def fetch_order(self, order_id: int) -> Optional[Order]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, items, placed_at, ready_at FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_order(row)

    def create_order(self, items: Dict[int, int]) -> Order:
        """Persist a new order and return it."""
        snapshot = dict(items)
        placed_at = datetime.now()
        payload = json.dumps(snapshot)

        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    "INSERT INTO orders (items, placed_at, ready_at) VALUES (?, ?, ?)",
                    (payload, placed_at.isoformat(), None),
                )
                conn.commit()
                order_id = cursor.lastrowid

        return Order(order_id=order_id, items=snapshot, placed_at=placed_at)

    def update_ready_time(self, order_id: int, ready_at: datetime) -> None:
        """Mark an order as ready. (Not yet used externally.)"""
        with self._connect() as conn:
            conn.execute(
                "UPDATE orders SET ready_at = ? WHERE id = ?",
                (ready_at.isoformat(), order_id),
            )
            conn.commit()

    def _row_to_order(self, row: sqlite3.Row) -> Order:
        order_id, items_blob, placed_at_str, ready_at_str = row
        items_dict = {int(k): int(v) for k, v in json.loads(items_blob).items()}
        placed_at = datetime.fromisoformat(placed_at_str)
        ready_at = datetime.fromisoformat(ready_at_str) if ready_at_str else None
        return Order(order_id=order_id, items=items_dict, placed_at=placed_at, ready_at=ready_at)


class CafeOrderSystem:
    """Shared state for menu and placed orders."""

    def __init__(self, db_path: str = "cafe_cursor.db") -> None:
        self.menu = CafeMenu()
        self.db = CafeDatabase(db_path)
        self.orders: Dict[int, Order] = self.db.load_orders()

    def create_order(self, snapshot: Dict[int, int]) -> Order:
        """Persist an order and return it."""
        order = self.db.create_order(snapshot)
        self.orders[order.order_id] = order
        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        order = self.orders.get(order_id)
        if order:
            return order
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


class IOInterface:
    """Basic IO contract for CLI or socket-based sessions."""

    def write(self, message: str) -> None:  # pragma: no cover - simple wrapper
        raise NotImplementedError

    def readline(self, prompt: str = "") -> str:  # pragma: no cover - simple wrapper
        raise NotImplementedError


class ConsoleIO(IOInterface):
    """Console implementation using input/print."""

    def write(self, message: str) -> None:
        print(message)

    def readline(self, prompt: str = "") -> str:
        return input(prompt)


class SocketIO(IOInterface):
    """Socket implementation compatible with telnet clients."""

    def __init__(self, connection):
        self.connection = connection
        self.rfile = connection.makefile("rb")
        self.wfile = connection.makefile("wb")

    def write(self, message: str) -> None:
        if not message.endswith("\n"):
            message += "\n"
        data = message.replace("\n", "\r\n").encode("utf-8")
        self.wfile.write(data)
        self.wfile.flush()

    def readline(self, prompt: str = "") -> str:
        if prompt:
            self.write(prompt)
        line = self.rfile.readline()
        if not line:
            raise EOFError
        return line.decode("utf-8").rstrip("\r\n")

    def close(self) -> None:
        try:
            self.rfile.close()
            self.wfile.close()
        finally:
            self.connection.close()


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
            elif command == "ready":
                self._handle_ready(args)
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

    def _handle_ready(self, args: List[str]) -> None:
        """Mark an order as ready (records ready timestamp)."""
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

        self.io.write(f"Order {order_id} marked ready at {order.ready_at.isoformat(timespec='seconds')}.")

    def _print_help(self) -> None:
        """Show supported commands."""
        self.io.write(f"\n{CAFE_LOGO}")
        self.io.write("Commands:")
        self.io.write("  menu                    Show Cafe Cursor offerings")
        self.io.write("  add <item #> [qty]      Add menu item to cart")
        self.io.write("  cart                    Review current cart")
        self.io.write("  order                   Place the current cart")
        self.io.write("  status <order id>       Check order status (integers only)")
        self.io.write("  ready <order id>        Mark an order as ready (timestamps it)")
        self.io.write("  help                    Show this message")
        self.io.write("  exit                    Quit the app")


class ThreadedCafeServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def serve_over_tcp(system: CafeOrderSystem, host: str, port: int) -> None:
    """Start a telnet-friendly TCP server."""

    class CafeRequestHandler(socketserver.BaseRequestHandler):
        def handle(self_inner) -> None:
            io = SocketIO(self_inner.request)
            app = CafeOrderApp(system=system, io=io)
            try:
                app.run()
            finally:
                io.close()

    with ThreadedCafeServer((host, port), CafeRequestHandler) as server:
        print(f"Cafe Cursor server listening on {host}:{port}")
        server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cafe Cursor ordering app")
    parser.add_argument("--serve", action="store_true", help="Start a TCP server instead of local CLI")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address for the TCP server")
    parser.add_argument("--port", type=int, default=5555, help="Port for the TCP server")
    parser.add_argument("--db-path", default="cafe_cursor.db", help="SQLite database path")
    args = parser.parse_args()

    system = CafeOrderSystem(db_path=args.db_path)
    if args.serve:
        serve_over_tcp(system, args.host, args.port)
    else:
        app = CafeOrderApp(system=system)
        app.run()


if __name__ == "__main__":
    main()

