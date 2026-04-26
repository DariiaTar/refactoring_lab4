"""
Singleton Pattern - OrderDatabase
Ensures only one instance of the order storage exists app-wide.
"""

import threading
from typing import List, Optional
from src.models import Order, IOrderRepository


class OrderDatabase(IOrderRepository):
    """
    Singleton order database.
    Thread-safe implementation using a lock.
    """

    _instance: Optional["OrderDatabase"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "OrderDatabase":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._orders: List[Order] = []
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """For testing purposes only — resets the singleton."""
        with cls._lock:
            cls._instance = None

    def save(self, order: Order) -> None:
        if not any(o.order_id == order.order_id for o in self._orders):
            self._orders.append(order)

    def get_all(self) -> List[Order]:
        return list(self._orders)

    def find_by_client(self, client_id: str) -> List[Order]:
        return [o for o in self._orders if o.client.client_id == client_id]

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return next((o for o in self._orders if o.order_id == order_id), None)

    def delete(self, order_id: str) -> bool:
        before = len(self._orders)
        self._orders = [o for o in self._orders if o.order_id != order_id]
        return len(self._orders) < before

    def clear(self) -> None:
        self._orders.clear()

    def count(self) -> int:
        return len(self._orders)
