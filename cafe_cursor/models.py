"""Data models for Cafe Cursor."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass(frozen=True)
class MenuItem:
    """Represents a single menu entry."""

    identifier: int
    name: str


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

