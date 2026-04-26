"""
Observer Pattern - Gym Staff Notifiers
Decouples order management from notification logic.
"""

from src.models import IObserver


class TrainerNotifier(IObserver):
    """Notifies the training staff about new confirmed orders."""

    def __init__(self):
        self.notifications: list = []

    def update(self, event: str, data: dict) -> None:
        if event == "order_confirmed":
            msg = (
                f"[TRAINER] New session booked! "
                f"Client: {data.get('client')} | "
                f"Services: {', '.join(data.get('items', []))} | "
                f"Total: {data.get('total', 0):.2f} UAH"
            )
            self.notifications.append({"event": event, "message": msg, "data": data})
            print(msg)

    @property
    def last_notification(self) -> dict | None:
        return self.notifications[-1] if self.notifications else None


class ReceptionNotifier(IObserver):
    """Notifies the reception desk about order status changes."""

    def __init__(self):
        self.notifications: list = []

    def update(self, event: str, data: dict) -> None:
        if event == "order_confirmed":
            msg = (
                f"[RECEPTION] Order #{data.get('order_id')} confirmed for "
                f"{data.get('client')}. Amount due: {data.get('total', 0):.2f} UAH"
            )
        elif event == "order_cancelled":
            msg = f"[RECEPTION] Order #{data.get('order_id')} has been CANCELLED."
        else:
            msg = f"[RECEPTION] Event '{event}' received: {data}"

        self.notifications.append({"event": event, "message": msg, "data": data})
        print(msg)

    def count(self) -> int:
        return len(self.notifications)


class EmailNotifier(IObserver):
    """Simulates sending email notifications to clients."""

    def __init__(self):
        self.sent_emails: list = []

    def update(self, event: str, data: dict) -> None:
        if event in ("order_confirmed", "order_cancelled"):
            email = {
                "to": data.get("client", "unknown"),
                "subject": f"Gym Booking - {event.replace('_', ' ').title()}",
                "body": str(data),
                "event": event,
            }
            self.sent_emails.append(email)
            print(f"[EMAIL] Sent '{email['subject']}' to {email['to']}")

    def count(self) -> int:
        return len(self.sent_emails)
