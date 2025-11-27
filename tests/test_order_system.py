"""Tests for order system."""

import os
import tempfile
import unittest

from cafe_cursor.order_system import CafeOrderSystem


class TestCafeOrderSystem(unittest.TestCase):
    """Test CafeOrderSystem class."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.system = CafeOrderSystem(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_system_initializes(self):
        self.assertIsNotNone(self.system.menu)
        self.assertIsNotNone(self.system.db)
        self.assertIsInstance(self.system.orders, dict)

    def test_create_order(self):
        items = {1: 2}
        order = self.system.create_order(items)
        self.assertIsNotNone(order)
        self.assertIn(order.order_id, self.system.orders)

    def test_get_order(self):
        order = self.system.create_order({1: 1})
        fetched = self.system.get_order(order.order_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.order_id, order.order_id)

    def test_get_order_not_exists(self):
        fetched = self.system.get_order(999)
        self.assertIsNone(fetched)

    def test_list_orders(self):
        self.system.create_order({1: 1})
        self.system.create_order({2: 2})
        orders = self.system.list_orders()
        self.assertEqual(len(orders), 2)

    def test_mark_ready(self):
        order = self.system.create_order({1: 1})
        updated = self.system.mark_ready(order.order_id)
        self.assertIsNotNone(updated)
        self.assertIsNotNone(updated.ready_at)

    def test_mark_ready_not_exists(self):
        updated = self.system.mark_ready(999)
        self.assertIsNone(updated)

    def test_refresh_menu(self):
        self.system.db.add_menu_item(99, "Test Item")
        self.system.refresh_menu()
        self.assertIn(99, self.system.menu.items)

    def test_add_menu_item(self):
        success = self.system.add_menu_item(99, "Test Item")
        self.assertTrue(success)
        self.assertIn(99, self.system.menu.items)

    def test_remove_menu_item(self):
        self.system.add_menu_item(99, "Test Item")
        success = self.system.remove_menu_item(99)
        self.assertTrue(success)
        self.assertNotIn(99, self.system.menu.items)

