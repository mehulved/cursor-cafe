"""Tests for shopping cart."""

import unittest
from io import StringIO

from cafe_cursor.cart import ShoppingCart
from cafe_cursor.menu import CafeMenu


class TestShoppingCart(unittest.TestCase):
    """Test ShoppingCart class."""

    def setUp(self):
        self.cart = ShoppingCart()
        self.menu = CafeMenu(db=None)

    def test_cart_starts_empty(self):
        self.assertTrue(self.cart.is_empty())

    def test_add_item(self):
        self.cart.add(1, 2)
        self.assertFalse(self.cart.is_empty())
        self.assertEqual(self.cart.items[1], 2)

    def test_add_item_accumulates(self):
        self.cart.add(1, 2)
        self.cart.add(1, 3)
        self.assertEqual(self.cart.items[1], 5)

    def test_add_item_invalid_quantity(self):
        with self.assertRaises(ValueError):
            self.cart.add(1, -1)

    def test_snapshot(self):
        self.cart.add(1, 2)
        snapshot = self.cart.snapshot()
        self.assertEqual(snapshot, {1: 2})
        self.cart.add(2, 1)
        self.assertEqual(snapshot, {1: 2})

    def test_clear(self):
        self.cart.add(1, 2)
        self.cart.clear()
        self.assertTrue(self.cart.is_empty())

    def test_display_empty(self):
        output = StringIO()
        self.cart.display(self.menu, write=output.write)
        result = output.getvalue()
        self.assertIn("empty", result.lower())

    def test_display_with_items(self):
        self.cart.add(1, 2)
        self.cart.add(2, 1)
        output = StringIO()
        self.cart.display(self.menu, write=output.write)
        result = output.getvalue()
        self.assertIn("Black (Hot)", result)
        self.assertIn("x2", result)

