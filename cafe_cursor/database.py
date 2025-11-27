"""Database layer for Cafe Cursor."""

import json
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Optional

from .models import MenuItem, Order


class CafeDatabase:
    """Lightweight SQLite wrapper for persisting orders and menu items."""

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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.commit()
            self._initialize_default_menu()

    def _initialize_default_menu(self) -> None:
        """Populate menu with default items if empty."""
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
            if count == 0:
                default_items = [
                    (1, "Black (Hot)"),
                    (2, "Black (Cold)"),
                    (3, "White (Hot)"),
                    (4, "White (Cold)"),
                    (5, "Mocha (Hot)"),
                    (6, "Mocha (Cold)"),
                    (7, "Hot Chocolate"),
                    (8, "Cold Chocolate"),
                    (9, "Espresso Tonic"),
                    (10, "Strawberry Latte"),
                    (11, "Vanilla Latte"),
                    (12, "Chocolate Cookies"),
                    (13, "Strawberry Cookies"),
                ]
                conn.executemany(
                    "INSERT INTO menu_items (id, name) VALUES (?, ?)",
                    default_items,
                )
                conn.commit()

    # Menu item operations
    def load_menu_items(self) -> Dict[int, MenuItem]:
        """Load all menu items from the database."""
        with self._connect() as conn:
            rows = conn.execute("SELECT id, name FROM menu_items ORDER BY id").fetchall()
        return {row[0]: MenuItem(row[0], row[1]) for row in rows}

    def add_menu_item(self, item_id: int, name: str) -> bool:
        """Add a new menu item. Returns True if successful, False if id already exists."""
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO menu_items (id, name) VALUES (?, ?)",
                    (item_id, name),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_menu_item(self, item_id: int) -> bool:
        """Remove a menu item. Returns True if successful, False if not found."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Order operations
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
        """Mark an order as ready."""
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

