"""
Factory Pattern - OrderFactory
Creates different types of orders without exposing creation logic.
"""

import uuid
from abc import ABC, abstractmethod
from src.models import Order, Client, OrderItem, TrainingService


class OrderFactory(ABC):
    """Abstract factory for creating orders."""

    @abstractmethod
    def create_order(self, client: Client) -> Order:
        pass


class StandardOrderFactory(OrderFactory):
    """Creates a standard single-session order."""

    def create_order(self, client: Client) -> Order:
        order_id = f"STD-{uuid.uuid4().hex[:8].upper()}"
        return Order(order_id=order_id, client=client)


class BulkOrderFactory(OrderFactory):
    """
    Creates a bulk order with a discount applied.
    Overrides item prices by wrapping with discounted services.
    """

    DISCOUNT = 0.15  # 15% discount

    def create_order(self, client: Client) -> Order:
        order_id = f"BULK-{uuid.uuid4().hex[:8].upper()}"
        order = Order(order_id=order_id, client=client)
        order.order_type = "bulk"
        return order

    def apply_discount(self, service: TrainingService) -> TrainingService:
        """Returns a new service with discounted price."""
        discounted_price = round(service.price * (1 - self.DISCOUNT), 2)
        return TrainingService(
            name=service.name,
            price=discounted_price,
            duration_minutes=service.duration_minutes,
            category=service.category,
        )


class PremiumOrderFactory(OrderFactory):
    """Creates a premium order with priority scheduling."""

    def create_order(self, client: Client) -> Order:
        order_id = f"PREM-{uuid.uuid4().hex[:8].upper()}"
        order = Order(order_id=order_id, client=client)
        order.order_type = "premium"
        return order


class OrderFactoryProvider:
    """
    Provider that selects the correct factory based on type string.
    OCP: adding a new type only requires registering a new factory.
    """

    _registry: dict = {
        "standard": StandardOrderFactory,
        "bulk": BulkOrderFactory,
        "premium": PremiumOrderFactory,
    }

    @classmethod
    def get_factory(cls, order_type: str) -> OrderFactory:
        factory_cls = cls._registry.get(order_type.lower())
        if factory_cls is None:
            raise ValueError(f"Unknown order type: '{order_type}'. "
                             f"Available: {list(cls._registry.keys())}")
        return factory_cls()

    @classmethod
    def register(cls, order_type: str, factory_cls: type) -> None:
        """Allows registering custom factories (OCP)."""
        cls._registry[order_type] = factory_cls
