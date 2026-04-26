"""
Tests – Part 2: TDD functional tests (≥10 unit tests)
Covers adding services, creating orders, associating with clients, notifications.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import TrainingService, Client, Order, OrderItem, ServiceMenu
from src.repository import OrderDatabase
from src.notifiers import TrainerNotifier, ReceptionNotifier, EmailNotifier
from src.order_builders import OrderFactoryProvider
from src.order_service import OrderService


@pytest.fixture(autouse=True)
def reset_db():
    OrderDatabase.reset()
    yield
    OrderDatabase.reset()


@pytest.fixture
def menu():
    m = ServiceMenu()
    m.add_service(TrainingService("Yoga", 200, 60, "yoga"))
    m.add_service(TrainingService("Boxing", 300, 60, "cardio"))
    m.add_service(TrainingService("Pilates", 250, 50, "strength"))
    return m


@pytest.fixture
def client():
    return Client("C100", "Dmytro Bondar", "dmytro@gym.com", "premium")


@pytest.fixture
def service():
    return OrderService()


# ── Adding services ───────────────────────────────────────────────────────────

class TestAddServiceToMenu:
    def test_add_yoga_to_menu(self):
        menu = ServiceMenu()
        yoga = TrainingService("Yoga", 200, 60, "yoga")
        menu.add_service(yoga)
        assert menu.contains_service(yoga)

    def test_add_multiple_services(self):
        menu = ServiceMenu()
        for name, price, cat in [("Yoga", 200, "yoga"), ("Boxing", 300, "cardio")]:
            menu.add_service(TrainingService(name, price, 60, cat))
        assert len(menu.services) == 2

    def test_menu_empty_initially(self):
        menu = ServiceMenu()
        assert menu.is_empty()

    def test_add_service_to_empty_menu(self):
        menu = ServiceMenu()
        service = TrainingService("CrossFit", 350, 60, "strength")
        menu.add_service(service)
        assert not menu.is_empty()


# ── Creating orders ───────────────────────────────────────────────────────────

class TestCreateOrder:
    def test_create_standard_order(self, client, service):
        order = service.create_order(client, "standard")
        assert order.order_id.startswith("STD-")
        assert order.client == client
        assert order.status == "pending"

    def test_create_bulk_order(self, client, service):
        order = service.create_order(client, "bulk")
        assert order.order_id.startswith("BULK-")

    def test_create_premium_order(self, client, service):
        order = service.create_order(client, "premium")
        assert order.order_id.startswith("PREM-")

    def test_unknown_order_type_raises(self, client, service):
        with pytest.raises(ValueError):
            service.create_order(client, "unknown_type")

    def test_order_saved_to_db(self, client, service):
        order = service.create_order(client, "standard")
        db = OrderDatabase()
        assert db.find_by_id(order.order_id) is not None

    def test_associate_order_with_client(self, client, service):
        order = service.create_order(client)
        assert order.client.client_id == "C100"

    def test_get_client_orders(self, client, service):
        service.create_order(client)
        service.create_order(client)
        orders = service.get_client_orders("C100")
        assert len(orders) == 2


# ── Confirm / cancel ──────────────────────────────────────────────────────────

class TestOrderLifecycle:
    def test_confirm_order(self, client, service, menu):
        order = service.create_order(client)
        svc = menu.find_by_name("Yoga")
        service.add_service_to_order(order, svc)
        service.confirm_order(order)
        assert order.status == "confirmed"

    def test_cancel_order(self, client, service):
        order = service.create_order(client)
        service.cancel_order(order)
        assert order.status == "cancelled"

    def test_confirm_empty_order_raises(self, client, service):
        order = service.create_order(client)
        with pytest.raises(ValueError):
            service.confirm_order(order)

    def test_add_service_with_bulk_discount(self, client, service, menu):
        order = service.create_order(client, "bulk")
        yoga = menu.find_by_name("Yoga")  # price 200
        service.add_service_to_order(order, yoga, bulk_discount=True)
        # 15% off → 170.0
        assert order.total == pytest.approx(170.0, rel=1e-3)


# ── Notifications via Observer ────────────────────────────────────────────────

class TestKitchenNotification:
    def test_trainer_notified_on_confirm(self, client, service, menu):
        trainer = TrainerNotifier()
        order = service.create_order(client, observers=[trainer])
        order.add_item(OrderItem(menu.find_by_name("Boxing")))
        service.confirm_order(order)
        assert len(trainer.notifications) == 1
        assert trainer.last_notification["event"] == "order_confirmed"

    def test_reception_notified_on_cancel(self, client, service):
        reception = ReceptionNotifier()
        order = service.create_order(client, observers=[reception])
        service.cancel_order(order)
        assert reception.count() == 1

    def test_multiple_observers(self, client, service, menu):
        trainer = TrainerNotifier()
        reception = ReceptionNotifier()
        email = EmailNotifier()
        order = service.create_order(client, observers=[trainer, reception, email])
        order.add_item(OrderItem(menu.find_by_name("Yoga")))
        service.confirm_order(order)
        assert len(trainer.notifications) == 1
        assert reception.count() == 1
        assert email.count() == 1

    def test_no_notification_before_confirm(self, client, service):
        trainer = TrainerNotifier()
        service.create_order(client, observers=[trainer])
        assert len(trainer.notifications) == 0

    def test_unsubscribe_observer(self, client, service, menu):
        trainer = TrainerNotifier()
        order = service.create_order(client, observers=[trainer])
        order.unsubscribe(trainer)
        order.add_item(OrderItem(menu.find_by_name("Yoga")))
        service.confirm_order(order)
        assert len(trainer.notifications) == 0
