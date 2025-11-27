#!/usr/bin/env python3
"""
Unit tests for Cafe Cursor application.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import Mock, patch

import cafe_cursor


class TestMenuItem(unittest.TestCase):
    """Test MenuItem dataclass."""

    def test_menu_item_creation(self):
        item = cafe_cursor.MenuItem(1, "Test Item")
        self.assertEqual(item.identifier, 1)
        self.assertEqual(item.name, "Test Item")

    def test_menu_item_immutable(self):
        item = cafe_cursor.MenuItem(1, "Test Item")
        with self.assertRaises(Exception):
            item.identifier = 2


class TestCafeMenu(unittest.TestCase):
    """Test CafeMenu class."""

    def setUp(self):
        """Set up test fixtures."""
        self.menu = cafe_cursor.CafeMenu(db=None)

    def test_menu_has_default_items(self):
        """Test that menu has default items when no database."""
        self.assertGreater(len(self.menu.items), 0)
        self.assertIn(1, self.menu.items)
        self.assertEqual(self.menu.items[1].name, "Black (Hot)")

    def test_get_item_exists(self):
        """Test getting an existing menu item."""
        item = self.menu.get_item(1)
        self.assertIsNotNone(item)
        self.assertEqual(item.identifier, 1)

    def test_get_item_not_exists(self):
        """Test getting a non-existent menu item."""
        item = self.menu.get_item(999)
        self.assertIsNone(item)

    def test_all_items(self):
        """Test getting all items as a list."""
        items = self.menu.all_items()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        # Check items are sorted by id
        ids = [item.identifier for item in items]
        self.assertEqual(ids, sorted(ids))

    def test_display(self):
        """Test menu display output."""
        output = StringIO()
        self.menu.display(write=output.write)
        result = output.getvalue()
        self.assertIn("CAFE CURSOR MENU", result)
        self.assertIn("Black (Hot)", result)


class TestShoppingCart(unittest.TestCase):
    """Test ShoppingCart class."""

    def setUp(self):
        """Set up test fixtures."""
        self.cart = cafe_cursor.ShoppingCart()
        self.menu = cafe_cursor.CafeMenu(db=None)

    def test_cart_starts_empty(self):
        """Test that cart starts empty."""
        self.assertTrue(self.cart.is_empty())

    def test_add_item(self):
        """Test adding items to cart."""
        self.cart.add(1, 2)
        self.assertFalse(self.cart.is_empty())
        self.assertEqual(self.cart.items[1], 2)

    def test_add_item_accumulates(self):
        """Test that adding same item accumulates quantity."""
        self.cart.add(1, 2)
        self.cart.add(1, 3)
        self.assertEqual(self.cart.items[1], 5)

    def test_add_item_invalid_quantity(self):
        """Test that negative quantity raises error."""
        with self.assertRaises(ValueError):
            self.cart.add(1, -1)

    def test_snapshot(self):
        """Test cart snapshot returns a copy."""
        self.cart.add(1, 2)
        snapshot = self.cart.snapshot()
        self.assertEqual(snapshot, {1: 2})
        # Modify original, snapshot should be unchanged
        self.cart.add(2, 1)
        self.assertEqual(snapshot, {1: 2})

    def test_clear(self):
        """Test clearing the cart."""
        self.cart.add(1, 2)
        self.cart.clear()
        self.assertTrue(self.cart.is_empty())

    def test_display_empty(self):
        """Test displaying empty cart."""
        output = StringIO()
        self.cart.display(self.menu, write=output.write)
        result = output.getvalue()
        self.assertIn("empty", result.lower())

    def test_display_with_items(self):
        """Test displaying cart with items."""
        self.cart.add(1, 2)
        self.cart.add(2, 1)
        output = StringIO()
        self.cart.display(self.menu, write=output.write)
        result = output.getvalue()
        self.assertIn("Black (Hot)", result)
        self.assertIn("x2", result)


class TestOrder(unittest.TestCase):
    """Test Order dataclass."""

    def test_order_creation(self):
        """Test creating an order."""
        items = {1: 2, 3: 1}
        placed_at = datetime.now()
        order = cafe_cursor.Order(order_id=1, items=items, placed_at=placed_at)
        self.assertEqual(order.order_id, 1)
        self.assertEqual(order.items, items)
        self.assertEqual(order.placed_at, placed_at)
        self.assertIsNone(order.ready_at)

    def test_order_status_recent(self):
        """Test order status for recently placed order."""
        placed_at = datetime.now() - timedelta(minutes=1)
        order = cafe_cursor.Order(order_id=1, items={1: 1}, placed_at=placed_at)
        status = order.status()
        self.assertIn("Barista received", status)

    def test_order_status_preparing(self):
        """Test order status for order being prepared."""
        placed_at = datetime.now() - timedelta(minutes=3)
        order = cafe_cursor.Order(order_id=1, items={1: 1}, placed_at=placed_at)
        status = order.status()
        self.assertIn("prepared", status)

    def test_order_status_almost_ready(self):
        """Test order status for order almost ready."""
        placed_at = datetime.now() - timedelta(minutes=6)
        order = cafe_cursor.Order(order_id=1, items={1: 1}, placed_at=placed_at)
        status = order.status()
        self.assertIn("Almost ready", status)

    def test_order_status_ready(self):
        """Test order status when marked ready."""
        placed_at = datetime.now() - timedelta(minutes=10)
        ready_at = datetime.now() - timedelta(minutes=5)
        order = cafe_cursor.Order(
            order_id=1, items={1: 1}, placed_at=placed_at, ready_at=ready_at
        )
        status = order.status()
        self.assertEqual(status, "Ready for pickup!")


class TestCafeDatabase(unittest.TestCase):
    """Test CafeDatabase class."""

    def setUp(self):
        """Set up test fixtures with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = cafe_cursor.CafeDatabase(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_database_creates_schema(self):
        """Test that database creates tables on init."""
        # Schema creation happens in __init__, so just verify we can query
        items = self.db.load_menu_items()
        self.assertIsInstance(items, dict)

    def test_load_menu_items(self):
        """Test loading menu items from database."""
        items = self.db.load_menu_items()
        self.assertGreater(len(items), 0)
        self.assertIn(1, items)
        self.assertEqual(items[1].name, "Black (Hot)")

    def test_add_menu_item(self):
        """Test adding a menu item."""
        success = self.db.add_menu_item(99, "Test Item")
        self.assertTrue(success)
        items = self.db.load_menu_items()
        self.assertIn(99, items)
        self.assertEqual(items[99].name, "Test Item")

    def test_add_menu_item_duplicate_id(self):
        """Test that adding duplicate ID fails."""
        self.db.add_menu_item(99, "Test Item")
        success = self.db.add_menu_item(99, "Another Item")
        self.assertFalse(success)

    def test_remove_menu_item(self):
        """Test removing a menu item."""
        self.db.add_menu_item(99, "Test Item")
        success = self.db.remove_menu_item(99)
        self.assertTrue(success)
        items = self.db.load_menu_items()
        self.assertNotIn(99, items)

    def test_remove_menu_item_not_exists(self):
        """Test removing non-existent menu item."""
        success = self.db.remove_menu_item(999)
        self.assertFalse(success)

    def test_create_order(self):
        """Test creating an order."""
        items = {1: 2, 3: 1}
        order = self.db.create_order(items)
        self.assertIsNotNone(order)
        self.assertEqual(order.items, items)
        self.assertIsNotNone(order.placed_at)
        self.assertIsNone(order.ready_at)

    def test_load_orders(self):
        """Test loading orders from database."""
        order1 = self.db.create_order({1: 1})
        order2 = self.db.create_order({2: 2})
        orders = self.db.load_orders()
        self.assertEqual(len(orders), 2)
        self.assertIn(order1.order_id, orders)
        self.assertIn(order2.order_id, orders)

    def test_fetch_order(self):
        """Test fetching a specific order."""
        order = self.db.create_order({1: 1})
        fetched = self.db.fetch_order(order.order_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.order_id, order.order_id)
        self.assertEqual(fetched.items, order.items)

    def test_fetch_order_not_exists(self):
        """Test fetching non-existent order."""
        fetched = self.db.fetch_order(999)
        self.assertIsNone(fetched)

    def test_update_ready_time(self):
        """Test updating order ready time."""
        order = self.db.create_order({1: 1})
        ready_at = datetime.now()
        self.db.update_ready_time(order.order_id, ready_at)
        fetched = self.db.fetch_order(order.order_id)
        self.assertIsNotNone(fetched.ready_at)
        self.assertEqual(fetched.ready_at.isoformat(), ready_at.isoformat())


class TestCafeOrderSystem(unittest.TestCase):
    """Test CafeOrderSystem class."""

    def setUp(self):
        """Set up test fixtures with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.system = cafe_cursor.CafeOrderSystem(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_system_initializes(self):
        """Test that system initializes with menu and database."""
        self.assertIsNotNone(self.system.menu)
        self.assertIsNotNone(self.system.db)
        self.assertIsInstance(self.system.orders, dict)

    def test_create_order(self):
        """Test creating an order through system."""
        items = {1: 2}
        order = self.system.create_order(items)
        self.assertIsNotNone(order)
        self.assertIn(order.order_id, self.system.orders)

    def test_get_order(self):
        """Test getting an order."""
        order = self.system.create_order({1: 1})
        fetched = self.system.get_order(order.order_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.order_id, order.order_id)

    def test_get_order_not_exists(self):
        """Test getting non-existent order."""
        fetched = self.system.get_order(999)
        self.assertIsNone(fetched)

    def test_list_orders(self):
        """Test listing all orders."""
        self.system.create_order({1: 1})
        self.system.create_order({2: 2})
        orders = self.system.list_orders()
        self.assertEqual(len(orders), 2)

    def test_mark_ready(self):
        """Test marking an order as ready."""
        order = self.system.create_order({1: 1})
        updated = self.system.mark_ready(order.order_id)
        self.assertIsNotNone(updated)
        self.assertIsNotNone(updated.ready_at)

    def test_mark_ready_not_exists(self):
        """Test marking non-existent order as ready."""
        updated = self.system.mark_ready(999)
        self.assertIsNone(updated)

    def test_refresh_menu(self):
        """Test refreshing menu from database."""
        self.system.db.add_menu_item(99, "Test Item")
        self.system.refresh_menu()
        self.assertIn(99, self.system.menu.items)

    def test_add_menu_item(self):
        """Test adding menu item through system."""
        success = self.system.add_menu_item(99, "Test Item")
        self.assertTrue(success)
        self.assertIn(99, self.system.menu.items)

    def test_remove_menu_item(self):
        """Test removing menu item through system."""
        self.system.add_menu_item(99, "Test Item")
        success = self.system.remove_menu_item(99)
        self.assertTrue(success)
        self.assertNotIn(99, self.system.menu.items)


class TestSummarizeOrderItems(unittest.TestCase):
    """Test summarize_order_items function."""

    def test_summarize_single_item(self):
        """Test summarizing single item."""
        menu = cafe_cursor.CafeMenu(db=None)
        items = {1: 2}
        summary = cafe_cursor.summarize_order_items(menu, items)
        self.assertIn("Black (Hot)", summary)
        self.assertIn("x2", summary)

    def test_summarize_multiple_items(self):
        """Test summarizing multiple items."""
        menu = cafe_cursor.CafeMenu(db=None)
        items = {1: 1, 2: 2}
        summary = cafe_cursor.summarize_order_items(menu, items)
        self.assertIn("Black (Hot)", summary)
        self.assertIn("Black (Cold)", summary)

    def test_summarize_empty(self):
        """Test summarizing empty order."""
        menu = cafe_cursor.CafeMenu(db=None)
        items = {}
        summary = cafe_cursor.summarize_order_items(menu, items)
        self.assertEqual(summary, "No items")


class TestIOInterfaces(unittest.TestCase):
    """Test IO interface classes."""

    def test_console_io_write(self):
        """Test ConsoleIO write method."""
        io = cafe_cursor.ConsoleIO()
        with patch("builtins.print") as mock_print:
            io.write("test message")
            mock_print.assert_called_once_with("test message")

    def test_console_io_readline(self):
        """Test ConsoleIO readline method."""
        io = cafe_cursor.ConsoleIO()
        with patch("builtins.input", return_value="test input"):
            result = io.readline("prompt> ")
            self.assertEqual(result, "test input")


if __name__ == "__main__":
    unittest.main()

