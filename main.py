"""
Fitness Gym System — Demo
Run: python main.py
"""

from src.models import TrainingService, Client, OrderItem, ServiceMenu
from src.repository import OrderDatabase
from src.notifiers import TrainerNotifier, ReceptionNotifier, EmailNotifier
from src.order_service import OrderService


def main():
    print("=" * 60)
    print("   FITNESS GYM MANAGEMENT SYSTEM — DEMO")
    print("=" * 60)

    # ── Setup menu ───────────────────────────────────────────────
    menu = ServiceMenu()
    menu.add_service(TrainingService("Yoga", 200, 60, "yoga"))
    menu.add_service(TrainingService("Boxing", 300, 60, "cardio"))
    menu.add_service(TrainingService("Pilates", 250, 50, "strength"))
    menu.add_service(TrainingService("CrossFit", 350, 60, "strength"))
    print(f"\nMenu loaded: {len(menu.services)} services available.")

    # ── Create clients ───────────────────────────────────────────
    client1 = Client("C001", "Oleksiy Kravchenko", "oleksiy@gmail.com", "premium")
    client2 = Client("C002", "Maria Tkachuk", "maria@gmail.com", "standard")

    # ── Set up observers ─────────────────────────────────────────
    trainer = TrainerNotifier()
    reception = ReceptionNotifier()
    email = EmailNotifier()

    # ── Order service ────────────────────────────────────────────
    svc = OrderService()

    print("\n--- Standard Order ---")
    order1 = svc.create_order(client1, "standard", observers=[trainer, reception, email])
    svc.add_service_to_order(order1, menu.find_by_name("Yoga"))
    svc.add_service_to_order(order1, menu.find_by_name("Pilates"))
    svc.confirm_order(order1)
    print(f"Order total: {order1.total:.2f} UAH")

    print("\n--- Bulk Order with Discount ---")
    order2 = svc.create_order(client2, "bulk", observers=[trainer, reception])
    boxing = menu.find_by_name("Boxing")
    svc.add_service_to_order(order2, boxing, quantity=3, bulk_discount=True)
    svc.confirm_order(order2)
    print(f"Order total (after 15% discount): {order2.total:.2f} UAH")

    # ── Singleton check ──────────────────────────────────────────
    db1 = OrderDatabase()
    db2 = OrderDatabase()
    print(f"\nSingleton check — same instance: {db1 is db2}")
    print(f"Total orders in DB: {db1.count()}")

    print("\n" + "=" * 60)
    print("Demo complete.")


if __name__ == "__main__":
    main()
