"""
Tests – Part 1: Object creation and basic interactions (≥10 unit tests)
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import TrainingService, Client, Order, OrderItem, ServiceMenu
from src.repository import OrderDatabase


@pytest.fixture(autouse=True)
def reset_db():
    """Reset singleton before each test."""
    OrderDatabase.reset()
    yield
    OrderDatabase.reset()


# ── TrainingService ──────────────────────────────────────────────────────────

class TestTrainingService:
    def test_create_service(self):
        service = TrainingService("Yoga", 200.0, 60, "yoga")
        assert service.name == "Yoga"
        assert service.price == 200.0
        assert service.duration_minutes == 60
        assert service.category == "yoga"

    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            TrainingService("Yoga", -10, 60, "yoga")

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError):
            TrainingService("Yoga", 100, 0, "yoga")


# ── Client ───────────────────────────────────────────────────────────────────

class TestClient:
    def test_create_client(self):
        client = Client("C001", "Ivan Petrenko", "ivan@example.com", "premium")
        assert client.client_id == "C001"
        assert client.name == "Ivan Petrenko"
        assert client.membership_type == "premium"

    def test_default_membership(self):
        client = Client("C002", "Olha Koval", "olha@gym.com")
        assert client.membership_type == "standard"

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError):
            Client("C003", "Bad User", "notanemail")


# ── ServiceMenu ──────────────────────────────────────────────────────────────

class TestServiceMenu:
    def test_add_service_to_menu(self):
        menu = ServiceMenu()
        service = TrainingService("Pilates", 250, 50, "strength")
        menu.add_service(service)
        assert menu.contains_service(service)

    def test_menu_starts_empty(self):
        menu = ServiceMenu()
        assert menu.is_empty()

    def test_duplicate_service_raises(self):
        menu = ServiceMenu()
        service = TrainingService("Boxing", 300, 60, "cardio")
        menu.add_service(service)
        with pytest.raises(ValueError):
            menu.add_service(service)

    def test_remove_service(self):
        menu = ServiceMenu()
        service = TrainingService("Swimming", 180, 45, "cardio")
        menu.add_service(service)
        removed = menu.remove_service("Swimming")
        assert removed is True
        assert not menu.contains_service(service)

    def test_find_by_category(self):
        menu = ServiceMenu()
        menu.add_service(TrainingService("Running", 100, 30, "cardio"))
        menu.add_service(TrainingService("Cycling", 120, 45, "cardio"))
        menu.add_service(TrainingService("Yoga", 200, 60, "yoga"))
        cardio = menu.find_by_category("cardio")
        assert len(cardio) == 2

    def test_find_by_name(self):
        menu = ServiceMenu()
        service = TrainingService("CrossFit", 350, 60, "strength")
        menu.add_service(service)
        found = menu.find_by_name("CrossFit")
        assert found is not None
        assert found.name == "CrossFit"

    def test_find_nonexistent_returns_none(self):
        menu = ServiceMenu()
        assert menu.find_by_name("Ghost") is None


# ── Order ────────────────────────────────────────────────────────────────────

class TestOrder:
    def _make_order(self):
        client = Client("C010", "Test User", "test@gym.com")
        return Order("ORD-001", client)

    def test_create_order(self):
        order = self._make_order()
        assert order.order_id == "ORD-001"
        assert order.status == "pending"
        assert order.total == 0.0

    def test_add_item_to_order(self):
        order = self._make_order()
        service = TrainingService("Yoga", 200, 60, "yoga")
        order.add_item(OrderItem(service))
        assert len(order.items) == 1
        assert order.total == 200.0

    def test_order_total_multiple_items(self):
        order = self._make_order()
        order.add_item(OrderItem(TrainingService("Yoga", 200, 60, "yoga"), quantity=2))
        order.add_item(OrderItem(TrainingService("Boxing", 300, 60, "cardio")))
        assert order.total == 700.0

    def test_confirm_order_changes_status(self):
        order = self._make_order()
        order.add_item(OrderItem(TrainingService("Yoga", 200, 60, "yoga")))
        order.confirm()
        assert order.status == "confirmed"

    def test_cancel_order(self):
        order = self._make_order()
        order.cancel()
        assert order.status == "cancelled"

    def test_remove_item(self):
        order = self._make_order()
        order.add_item(OrderItem(TrainingService("Yoga", 200, 60, "yoga")))
        removed = order.remove_item("Yoga")
        assert removed is True
        assert len(order.items) == 0


# ── OrderItem subtotal ───────────────────────────────────────────────────────

class TestOrderItem:
    def test_subtotal(self):
        service = TrainingService("Pilates", 250, 50, "strength")
        item = OrderItem(service, quantity=3)
        assert item.subtotal == 750.0
