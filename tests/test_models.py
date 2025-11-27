"""Tests for data models."""

import unittest
from datetime import datetime, timedelta

from cafe_cursor.models import MenuItem, Order


class TestMenuItem(unittest.TestCase):
    """Test MenuItem dataclass."""

    def test_menu_item_creation(self):
        item = MenuItem(1, "Test Item")
        self.assertEqual(item.identifier, 1)
        self.assertEqual(item.name, "Test Item")

    def test_menu_item_immutable(self):
        item = MenuItem(1, "Test Item")
        with self.assertRaises(Exception):
            item.identifier = 2


class TestOrder(unittest.TestCase):
    """Test Order dataclass."""

    def test_order_creation(self):
        items = {1: 2, 3: 1}
        placed_at = datetime.now()
        order = Order(order_id=1, items=items, placed_at=placed_at)
        self.assertEqual(order.order_id, 1)
        self.assertEqual(order.items, items)
        self.assertEqual(order.placed_at, placed_at)
        self.assertIsNone(order.ready_at)

    def test_order_status_recent(self):
        placed_at = datetime.now() - timedelta(minutes=1)
        order = Order(order_id=1, items={1: 1}, placed_at=placed_at)
        status = order.status()
        self.assertIn("Barista received", status)

    def test_order_status_preparing(self):
        placed_at = datetime.now() - timedelta(minutes=3)
        order = Order(order_id=1, items={1: 1}, placed_at=placed_at)
        status = order.status()
        self.assertIn("prepared", status)

    def test_order_status_almost_ready(self):
        placed_at = datetime.now() - timedelta(minutes=6)
        order = Order(order_id=1, items={1: 1}, placed_at=placed_at)
        status = order.status()
        self.assertIn("Almost ready", status)

    def test_order_status_ready(self):
        placed_at = datetime.now() - timedelta(minutes=10)
        ready_at = datetime.now() - timedelta(minutes=5)
        order = Order(
            order_id=1, items={1: 1}, placed_at=placed_at, ready_at=ready_at
        )
        status = order.status()
        self.assertEqual(status, "Ready for pickup!")

