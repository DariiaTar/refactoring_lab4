"""
OrderService - Orchestrates order creation, booking, and notification.
SRP: handles order workflow only; delegates storage and notification.
DIP: depends on IOrderRepository abstraction.
"""

from src.models import Client, Order, OrderItem, TrainingService, IObserver, IOrderRepository
from src.order_builders import OrderFactoryProvider
from src.repository import OrderDatabase


class OrderService:
    """
    High-level service for managing gym orders.
    Uses Factory to create orders and Observer to propagate events.
    """

    def __init__(self, repository: IOrderRepository | None = None):
        self._repo = repository or OrderDatabase()

    def create_order(
        self,
        client: Client,
        order_type: str = "standard",
        observers: list[IObserver] | None = None,
    ) -> Order:
        factory = OrderFactoryProvider.get_factory(order_type)
        order = factory.create_order(client)

        if observers:
            for obs in observers:
                order.subscribe(obs)

        self._repo.save(order)
        return order

    def add_service_to_order(
        self,
        order: Order,
        service: TrainingService,
        quantity: int = 1,
        bulk_discount: bool = False,
    ) -> None:
        if bulk_discount:
            from src.order_builders import BulkOrderFactory
            service = BulkOrderFactory().apply_discount(service)
        order.add_item(OrderItem(service=service, quantity=quantity))

    def confirm_order(self, order: Order) -> None:
        if not order.items:
            raise ValueError("Cannot confirm an empty order")
        order.confirm()

    def cancel_order(self, order: Order) -> None:
        order.cancel()

    def get_client_orders(self, client_id: str) -> list[Order]:
        return self._repo.find_by_client(client_id)

    def get_all_orders(self) -> list[Order]:
        return self._repo.get_all()
