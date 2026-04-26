"""
Tests – Part 3: Design Pattern tests (≥10 unit tests)
Singleton, Factory, Observer pattern verification.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import TrainingService, Client, Order, OrderItem
from src.repository import OrderDatabase
from src.order_builders import (
    OrderFactoryProvider, StandardOrderFactory,
    BulkOrderFactory, PremiumOrderFactory, OrderFactory
)
from src.notifiers import TrainerNotifier, ReceptionNotifier, EmailNotifier
from src.order_service import OrderService


@pytest.fixture(autouse=True)
def reset_db():
    OrderDatabase.reset()
    yield
    OrderDatabase.reset()


@pytest.fixture
def client():
    return Client("P001", "Anna Sydorenko", "anna@gym.com", "vip")


# ═══════════════════════════════════════════════════════════════
# SINGLETON PATTERN TESTS
# ═══════════════════════════════════════════════════════════════

class TestSingletonPattern:
    def test_same_instance_returned(self):
        db1 = OrderDatabase()
        db2 = OrderDatabase()
        assert db1 is db2

    def test_data_shared_between_instances(self, client):
        db1 = OrderDatabase()
        order = Order("SING-001", client)
        db1.save(order)

        db2 = OrderDatabase()
        assert db2.find_by_id("SING-001") is not None

    def test_count_consistent(self, client):
        db = OrderDatabase()
        db.save(Order("X-001", client))
        db.save(Order("X-002", client))
        assert OrderDatabase().count() == 2

    def test_reset_clears_instance(self):
        db1 = OrderDatabase()
        OrderDatabase.reset()
        db2 = OrderDatabase()
        assert db1 is not db2  # new instance after reset

    def test_no_duplicate_saves(self, client):
        db = OrderDatabase()
        order = Order("DUP-001", client)
        db.save(order)
        db.save(order)  # second save should be ignored
        assert db.count() == 1

    def test_delete_from_db(self, client):
        db = OrderDatabase()
        order = Order("DEL-001", client)
        db.save(order)
        db.delete("DEL-001")
        assert db.find_by_id("DEL-001") is None


# ═══════════════════════════════════════════════════════════════
# FACTORY PATTERN TESTS
# ═══════════════════════════════════════════════════════════════

class TestFactoryPattern:
    def test_standard_factory_creates_std_order(self, client):
        factory = StandardOrderFactory()
        order = factory.create_order(client)
        assert order.order_id.startswith("STD-")

    def test_bulk_factory_creates_bulk_order(self, client):
        factory = BulkOrderFactory()
        order = factory.create_order(client)
        assert order.order_id.startswith("BULK-")

    def test_premium_factory_creates_premium_order(self, client):
        factory = PremiumOrderFactory()
        order = factory.create_order(client)
        assert order.order_id.startswith("PREM-")

    def test_provider_returns_correct_factory(self):
        f = OrderFactoryProvider.get_factory("standard")
        assert isinstance(f, StandardOrderFactory)

        f = OrderFactoryProvider.get_factory("bulk")
        assert isinstance(f, BulkOrderFactory)

        f = OrderFactoryProvider.get_factory("premium")
        assert isinstance(f, PremiumOrderFactory)

    def test_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            OrderFactoryProvider.get_factory("mystery")

    def test_bulk_discount_applied(self):
        factory = BulkOrderFactory()
        yoga = TrainingService("Yoga", 200, 60, "yoga")
        discounted = factory.apply_discount(yoga)
        assert discounted.price == pytest.approx(170.0, rel=1e-3)

    def test_factory_produces_unique_ids(self, client):
        factory = StandardOrderFactory()
        ids = {factory.create_order(client).order_id for _ in range(20)}
        assert len(ids) == 20  # all unique

    def test_register_custom_factory(self, client):
        class TrialOrderFactory(OrderFactory):
            def create_order(self, c):
                return Order(f"TRIAL-{id(c)}", c)

        OrderFactoryProvider.register("trial", TrialOrderFactory)
        factory = OrderFactoryProvider.get_factory("trial")
        order = factory.create_order(client)
        assert order.order_id.startswith("TRIAL-")


# ═══════════════════════════════════════════════════════════════
# OBSERVER PATTERN TESTS
# ═══════════════════════════════════════════════════════════════

class TestObserverPattern:
    def _make_order_with_item(self, client):
        order = Order("OBS-001", client)
        order.add_item(OrderItem(TrainingService("Yoga", 200, 60, "yoga")))
        return order

    def test_trainer_receives_confirmed_event(self, client):
        trainer = TrainerNotifier()
        order = self._make_order_with_item(client)
        order.subscribe(trainer)
        order.confirm()
        assert len(trainer.notifications) == 1
        assert "Anna Sydorenko" in trainer.last_notification["message"]

    def test_reception_receives_cancelled_event(self, client):
        reception = ReceptionNotifier()
        order = Order("OBS-002", client)
        order.subscribe(reception)
        order.cancel()
        assert reception.count() == 1

    def test_email_receives_both_events(self, client):
        email = EmailNotifier()
        order = self._make_order_with_item(client)
        order.subscribe(email)
        order.confirm()
        order.cancel()
        assert email.count() == 2

    def test_observer_not_called_without_subscribe(self, client):
        trainer = TrainerNotifier()
        order = self._make_order_with_item(client)
        order.confirm()  # trainer NOT subscribed
        assert len(trainer.notifications) == 0

    def test_multiple_observers_all_notified(self, client):
        trainer = TrainerNotifier()
        reception = ReceptionNotifier()
        email = EmailNotifier()
        order = self._make_order_with_item(client)
        for obs in [trainer, reception, email]:
            order.subscribe(obs)
        order.confirm()
        assert len(trainer.notifications) == 1
        assert reception.count() == 1
        assert email.count() == 1

    def test_unsubscribe_stops_notifications(self, client):
        trainer = TrainerNotifier()
        order = self._make_order_with_item(client)
        order.subscribe(trainer)
        order.unsubscribe(trainer)
        order.confirm()
        assert len(trainer.notifications) == 0

    def test_notification_contains_order_id(self, client):
        reception = ReceptionNotifier()
        order = self._make_order_with_item(client)
        order.subscribe(reception)
        order.confirm()
        msg = reception.notifications[-1]["message"]
        assert "OBS-001" in msg
