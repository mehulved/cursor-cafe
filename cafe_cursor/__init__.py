"""
Cafe Cursor - Lightweight terminal ordering app
"""

__version__ = "1.0.0"

# Export main classes for backward compatibility
from .models import MenuItem, Order
from .database import CafeDatabase
from .menu import CafeMenu, summarize_order_items
from .cart import ShoppingCart
from .order_system import CafeOrderSystem
from .io import IOInterface, ConsoleIO, SocketIO
from .frontend import CafeOrderApp
from .backend import CafeBackendApp

__all__ = [
    "MenuItem",
    "Order",
    "CafeDatabase",
    "CafeMenu",
    "summarize_order_items",
    "ShoppingCart",
    "CafeOrderSystem",
    "IOInterface",
    "ConsoleIO",
    "SocketIO",
    "CafeOrderApp",
    "CafeBackendApp",
]

