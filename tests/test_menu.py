"""Tests for menu management."""

import unittest
from io import StringIO

from cafe_cursor.menu import CafeMenu, summarize_order_items


class TestCafeMenu(unittest.TestCase):
    """Test CafeMenu class."""

    def setUp(self):
        self.menu = CafeMenu(db=None)

    def test_menu_has_default_items(self):
        self.assertGreater(len(self.menu.items), 0)
        self.assertIn(1, self.menu.items)
        self.assertEqual(self.menu.items[1].name, "Black (Hot)")

    def test_get_item_exists(self):
        item = self.menu.get_item(1)
        self.assertIsNotNone(item)
        self.assertEqual(item.identifier, 1)

    def test_get_item_not_exists(self):
        item = self.menu.get_item(999)
        self.assertIsNone(item)

    def test_all_items(self):
        items = self.menu.all_items()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        ids = [item.identifier for item in items]
        self.assertEqual(ids, sorted(ids))

    def test_display(self):
        output = StringIO()
        self.menu.display(write=output.write)
        result = output.getvalue()
        self.assertIn("CAFE CURSOR MENU", result)
        self.assertIn("Black (Hot)", result)


class TestSummarizeOrderItems(unittest.TestCase):
    """Test summarize_order_items function."""

    def test_summarize_single_item(self):
        menu = CafeMenu(db=None)
        items = {1: 2}
        summary = summarize_order_items(menu, items)
        self.assertIn("Black (Hot)", summary)
        self.assertIn("x2", summary)

    def test_summarize_multiple_items(self):
        menu = CafeMenu(db=None)
        items = {1: 1, 2: 2}
        summary = summarize_order_items(menu, items)
        self.assertIn("Black (Hot)", summary)
        self.assertIn("Black (Cold)", summary)

    def test_summarize_empty(self):
        menu = CafeMenu(db=None)
        items = {}
        summary = summarize_order_items(menu, items)
        self.assertEqual(summary, "No items")

