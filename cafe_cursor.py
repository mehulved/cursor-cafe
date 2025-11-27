#!/usr/bin/env python3
"""
Cafe Cursor - Lightweight terminal ordering app

Usage highlights:
  Frontend (guests):
    menu                     -> show available drinks/snacks
    add <item #> [quantity]  -> add menu item to cart
    order                    -> place current cart as order
    status <order id>        -> check order progress
  Backend (baristas):
    list                     -> show all orders with status
    status <order id>        -> check a specific order
    ready <order id>         -> mark an order as ready
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


def summarize_order_items(menu: CafeMenu, items: Dict[int, int]) -> str:
    """Create a human readable items summary for an order."""
    parts: List[str] = []
    for item_id, qty in items.items():
        menu_item = menu.get_item(item_id)
        name = menu_item.name if menu_item else f"Item {item_id}"
        parts.append(f"{name} x{qty}")
    return ", ".join(parts) if parts else "No items"


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
            self.io.write(f"- #{order.order_id:03d} [{status}] placed {placed} ready {ready}")
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

    def _print_help(self) -> None:
        self.io.write(f"\n{CAFE_LOGO}")
        self.io.write("Backend Commands:")
        self.io.write("  list                    Show all orders and status")
        self.io.write("  status <order id>       Show details for one order")
        self.io.write("  ready <order id>        Mark order as ready")
        self.io.write("  help                    Show this message")
        self.io.write("  exit                    Quit the console")


class ThreadedCafeServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def serve_app_over_tcp(
    app_cls, system: CafeOrderSystem, host: str, port: int, label: str
) -> None:
    """Start a telnet-friendly TCP server for the provided app."""

    class CafeRequestHandler(socketserver.BaseRequestHandler):
        def handle(self_inner) -> None:
            io = SocketIO(self_inner.request)
            app = app_cls(system=system, io=io)
            try:
                app.run()
            finally:
                io.close()

    with ThreadedCafeServer((host, port), CafeRequestHandler) as server:
        print(f"{label} listening on {host}:{port}")
        server.serve_forever()


def serve_frontend_over_tcp(system: CafeOrderSystem, host: str, port: int) -> None:
    serve_app_over_tcp(CafeOrderApp, system, host, port, "Cafe Cursor frontend server")


def serve_backend_over_tcp(system: CafeOrderSystem, host: str, port: int) -> None:
    serve_app_over_tcp(CafeBackendApp, system, host, port, "Cafe Cursor backend server")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cafe Cursor ordering app")
    parser.add_argument(
        "--serve",
        "--serve-frontend",
        action="store_true",
        dest="serve_frontend",
        help="Start the guest (frontend) TCP server",
        default=False,
    )
    parser.add_argument("--serve-backend", action="store_true", help="Start the staff/backend TCP server")
    parser.add_argument("--backend", action="store_true", help="Run the backend console locally")
    parser.add_argument("--frontend-host", default="0.0.0.0", help="Bind address for the frontend TCP server")
    parser.add_argument("--frontend-port", type=int, default=5555, help="Port for the frontend TCP server")
    parser.add_argument("--backend-host", default="127.0.0.1", help="Bind address for the backend TCP server")
    parser.add_argument("--backend-port", type=int, default=6000, help="Port for the backend TCP server")
    parser.add_argument("--db-path", default="cafe_cursor.db", help="SQLite database path")
    args = parser.parse_args()

    system = CafeOrderSystem(db_path=args.db_path)

    if args.serve_frontend and args.serve_backend:
        parser.error("Choose either --serve/--serve-frontend or --serve-backend per process.")

    if args.serve_frontend:
        serve_frontend_over_tcp(system, args.frontend_host, args.frontend_port)
    elif args.serve_backend:
        serve_backend_over_tcp(system, args.backend_host, args.backend_port)
    else:
        app_cls = CafeBackendApp if args.backend else CafeOrderApp
        app = app_cls(system=system)
        app.run()


if __name__ == "__main__":
    main()

