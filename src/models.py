"""
Fitness Gym System - Core Models
Implements SOLID principles:
- SRP: each class has one responsibility
- OCP: open for extension via interfaces
- DIP: depends on abstractions
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


# ─── Abstractions (DIP) ───────────────────────────────────────────────────────

class INotifier(ABC):
    """Interface for notification systems."""
    @abstractmethod
    def notify(self, message: str) -> None:
        pass


class IOrderRepository(ABC):
    """Interface for order storage (DIP)."""
    @abstractmethod
    def save(self, order: "Order") -> None:
        pass

    @abstractmethod
    def get_all(self) -> List["Order"]:
        pass

    @abstractmethod
    def find_by_client(self, client_id: str) -> List["Order"]:
        pass


class IObserver(ABC):
    """Observer interface for the Observer pattern."""
    @abstractmethod
    def update(self, event: str, data: dict) -> None:
        pass


class ISubject(ABC):
    """Subject interface for the Observer pattern."""
    @abstractmethod
    def subscribe(self, observer: IObserver) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, observer: IObserver) -> None:
        pass

    @abstractmethod
    def notify_observers(self, event: str, data: dict) -> None:
        pass


# ─── Domain Models ────────────────────────────────────────────────────────────

@dataclass
class TrainingService:
    """Represents a single service/class offered by the gym."""
    name: str
    price: float
    duration_minutes: int
    category: str  # e.g. "cardio", "strength", "yoga"

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be positive")


@dataclass
class Client:
    """Represents a gym member."""
    client_id: str
    name: str
    email: str
    membership_type: str = "standard"  # standard, premium, vip

    def __post_init__(self):
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email address")


@dataclass
class OrderItem:
    """A single item inside an order."""
    service: TrainingService
    quantity: int = 1

    @property
    def subtotal(self) -> float:
        return self.service.price * self.quantity


class Order(ISubject):
    """
    Represents a client's booking/order.
    Implements ISubject for the Observer pattern.
    """

    def __init__(self, order_id: str, client: Client):
        self.order_id = order_id
        self.client = client
        self.items: List[OrderItem] = []
        self.status: str = "pending"
        self.created_at: datetime = datetime.now()
        self._observers: List[IObserver] = []

    def subscribe(self, observer: IObserver) -> None:
        self._observers.append(observer)

    def unsubscribe(self, observer: IObserver) -> None:
        self._observers.remove(observer)

    def notify_observers(self, event: str, data: dict) -> None:
        for observer in self._observers:
            observer.update(event, data)

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    def remove_item(self, service_name: str) -> bool:
        before = len(self.items)
        self.items = [i for i in self.items if i.service.name != service_name]
        return len(self.items) < before

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def confirm(self) -> None:
        self.status = "confirmed"
        self.notify_observers("order_confirmed", {
            "order_id": self.order_id,
            "client": self.client.name,
            "total": self.total,
            "items": [i.service.name for i in self.items],
        })

    def cancel(self) -> None:
        self.status = "cancelled"
        self.notify_observers("order_cancelled", {"order_id": self.order_id})

    def __repr__(self):
        return f"Order(id={self.order_id}, client={self.client.name}, status={self.status})"


class ServiceMenu:
    """
    Manages available training services.
    SRP: only responsible for the catalog of services.
    """

    def __init__(self):
        self._services: List[TrainingService] = []

    def add_service(self, service: TrainingService) -> None:
        if self.contains_service(service):
            raise ValueError(f"Service '{service.name}' already exists in menu")
        self._services.append(service)

    def remove_service(self, name: str) -> bool:
        before = len(self._services)
        self._services = [s for s in self._services if s.name != name]
        return len(self._services) < before

    def contains_service(self, service: TrainingService) -> bool:
        return any(s.name == service.name for s in self._services)

    def find_by_category(self, category: str) -> List[TrainingService]:
        return [s for s in self._services if s.category == category]

    def find_by_name(self, name: str) -> Optional[TrainingService]:
        return next((s for s in self._services if s.name == name), None)

    @property
    def services(self) -> List[TrainingService]:
        return list(self._services)

    def is_empty(self) -> bool:
        return len(self._services) == 0
