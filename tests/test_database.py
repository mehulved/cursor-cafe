"""Tests for database layer."""

import os
import tempfile
import unittest
from datetime import datetime

from cafe_cursor.database import CafeDatabase


class TestCafeDatabase(unittest.TestCase):
    """Test CafeDatabase class."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = CafeDatabase(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_database_creates_schema(self):
        items = self.db.load_menu_items()
        self.assertIsInstance(items, dict)

    def test_load_menu_items(self):
        items = self.db.load_menu_items()
        self.assertGreater(len(items), 0)
        self.assertIn(1, items)
        self.assertEqual(items[1].name, "Black (Hot)")

    def test_add_menu_item(self):
        success = self.db.add_menu_item(99, "Test Item")
        self.assertTrue(success)
        items = self.db.load_menu_items()
        self.assertIn(99, items)
        self.assertEqual(items[99].name, "Test Item")

    def test_add_menu_item_duplicate_id(self):
        self.db.add_menu_item(99, "Test Item")
        success = self.db.add_menu_item(99, "Another Item")
        self.assertFalse(success)

    def test_remove_menu_item(self):
        self.db.add_menu_item(99, "Test Item")
        success = self.db.remove_menu_item(99)
        self.assertTrue(success)
        items = self.db.load_menu_items()
        self.assertNotIn(99, items)

    def test_remove_menu_item_not_exists(self):
        success = self.db.remove_menu_item(999)
        self.assertFalse(success)

    def test_create_order(self):
        items = {1: 2, 3: 1}
        order = self.db.create_order(items)
        self.assertIsNotNone(order)
        self.assertEqual(order.items, items)
        self.assertIsNotNone(order.placed_at)
        self.assertIsNone(order.ready_at)

    def test_load_orders(self):
        order1 = self.db.create_order({1: 1})
        order2 = self.db.create_order({2: 2})
        orders = self.db.load_orders()
        self.assertEqual(len(orders), 2)
        self.assertIn(order1.order_id, orders)
        self.assertIn(order2.order_id, orders)

    def test_fetch_order(self):
        order = self.db.create_order({1: 1})
        fetched = self.db.fetch_order(order.order_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.order_id, order.order_id)
        self.assertEqual(fetched.items, order.items)

    def test_fetch_order_not_exists(self):
        fetched = self.db.fetch_order(999)
        self.assertIsNone(fetched)

    def test_update_ready_time(self):
        order = self.db.create_order({1: 1})
        ready_at = datetime.now()
        self.db.update_ready_time(order.order_id, ready_at)
        fetched = self.db.fetch_order(order.order_id)
        self.assertIsNotNone(fetched.ready_at)
        self.assertEqual(fetched.ready_at.isoformat(), ready_at.isoformat())

