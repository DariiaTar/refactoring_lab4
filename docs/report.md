# Лабораторна робота №4
## Система управління фітнес-залом



## Частина 1 — Проектування за принципами SOLID

### 1.1 UML-діаграма класів

![UML-діаграма](docs/uml.png)

### 1.2 Опис предметної області

Система управління фітнес-залом дозволяє:
- керувати каталогом тренувальних послуг (`ServiceMenu`)
- реєструвати клієнтів (`Client`, `Admin`)
- створювати бронювання різних типів (`Order`, `OrderItem`)
- оповіщати персонал про нові замовлення (`TrainerNotifier`, `ReceptionNotifier`, `EmailNotifier`)

### 1.3 Ключові класи

| Клас | Відповідальність |
|------|-----------------|
| `TrainingService` | Одна тренувальна послуга (назва, ціна, тривалість, категорія) |
| `ServiceMenu` | Каталог доступних послуг залу |
| `Client` | Клієнт з ідентифікатором, email та типом членства |
| `Order` | Бронювання клієнта, реалізує `ISubject` |
| `OrderItem` | Рядок замовлення: послуга + кількість |
| `OrderDatabase` | Singleton-сховище всіх замовлень |
| `TrainerNotifier` | Оповіщає тренерський склад |
| `ReceptionNotifier` | Оповіщає рецепцію |
| `EmailNotifier` | Надсилає email-сповіщення клієнту |
| `OrderService` | Бізнес-логіка: оркеструє створення та підтвердження |

### 1.4 Принципи SOLID

#### SRP — Single Responsibility Principle
Кожен клас має рівно одну зону відповідальності:
- `TrainingService` — тільки дані про послугу
- `ServiceMenu` — тільки каталог послуг
- `OrderDatabase` — тільки зберігання замовлень
- `OrderService` — тільки бізнес-оркестрація

#### OCP — Open/Closed Principle
`OrderFactoryProvider` використовує реєстр фабрик. Додавання нового типу замовлення не потребує зміни існуючого коду — достатньо викликати `register()`:

```python
OrderFactoryProvider.register("trial", TrialOrderFactory)
```

#### LSP — Liskov Substitution Principle
Усі реалізації `IObserver` (`TrainerNotifier`, `ReceptionNotifier`, `EmailNotifier`) взаємозамінні: `Order` працює з будь-яким спостерігачем через інтерфейс.

#### ISP — Interface Segregation Principle
Інтерфейси вузькі та зосереджені:
- `IObserver` — лише `update(event, data)`
- `ISubject` — лише `subscribe`, `unsubscribe`, `notify_observers`
- `IOrderRepository` — лише `save`, `get_all`, `find_by_client`

#### DIP — Dependency Inversion Principle
`OrderService` залежить від абстракції `IOrderRepository`, а не від конкретного `OrderDatabase`:

```python
class OrderService:
    def __init__(self, repository: IOrderRepository | None = None):
        self._repo = repository or OrderDatabase()
```

### 1.5 Структура файлів

```
fitness_gym/
├── src/
│   ├── models.py          # TrainingService, Client, Order, ServiceMenu + інтерфейси
│   ├── repository.py      # OrderDatabase (Singleton, thread-safe)
│   ├── order_builders.py  # OrderFactory + Standard/Bulk/Premium + Provider
│   ├── notifiers.py       # TrainerNotifier, ReceptionNotifier, EmailNotifier
│   └── order_service.py   # OrderService (бізнес-логіка)
├── tests/
│   ├── test_part1_basic.py      # 20 тестів — базові об'єкти
│   ├── test_part2_tdd.py        # 20 тестів — TDD функціонал
│   └── test_part3_patterns.py   # 21 тест  — шаблони проектування
├── docs/
│   ├── uml_diagram.png
│   └── report.md
├── main.py
├── pytest.ini
└── requirements.txt
```

---

## Частина 2 — Розробка за методологією TDD

### 2.1 Цикл TDD


**Приклад: додавання послуги до меню**

```python
# RED — тест написано ДО реалізації
def test_add_service_to_menu():
    menu = ServiceMenu()
    service = TrainingService("Yoga", 200, 60, "yoga")
    menu.add_service(service)
    assert menu.contains_service(service)   # падає — метод ще не існує

# GREEN — мінімальна реалізація
def add_service(self, service: TrainingService) -> None:
    if self.contains_service(service):
        raise ValueError(f"Service '{service.name}' already exists")
    self._services.append(service)

# REFACTOR — додано валідацію, типізацію, docstring
```

**Приклад: сповіщення тренера**

```python
# RED
def test_trainer_notified_on_confirm():
    trainer = TrainerNotifier()
    order = service.create_order(client, observers=[trainer])
    order.add_item(OrderItem(menu.find_by_name("Boxing")))
    service.confirm_order(order)
    assert len(trainer.notifications) == 1   # падає

# GREEN — реалізовано Order.confirm() та notify_observers()
```

### 2.2 Покриті функціональні сценарії

| Сценарій | Тест |
|----------|------|
| Додавання послуги до меню | `test_add_yoga_to_menu` |
| Блокування дублікатів | `test_duplicate_service_raises` |
| Пошук за категорією | `test_find_by_category` |
| Створення замовлення кожного типу | `test_create_standard/bulk/premium_order` |
| Збереження замовлення в БД | `test_order_saved_to_db` |
| Асоціювання замовлення з клієнтом | `test_associate_order_with_client` |
| Підтвердження замовлення | `test_confirm_order` |
| Помилка при підтвердженні порожнього | `test_confirm_empty_order_raises` |
| Знижка 15% для bulk | `test_add_service_with_bulk_discount` |
| Сповіщення тренера | `test_trainer_notified_on_confirm` |
| Сповіщення рецепції при скасуванні | `test_reception_notified_on_cancel` |
| Кілька спостерігачів одночасно | `test_multiple_observers` |
| Відписка спостерігача | `test_unsubscribe_observer` |

---

## Частина 3 — Шаблони проектування

### 3.1 Singleton — `OrderDatabase`

Гарантує єдиний екземпляр сховища замовлень у всьому додатку. Реалізований потокобезпечно через `threading.Lock`.

```python
class OrderDatabase(IOrderRepository):
    _instance: Optional["OrderDatabase"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "OrderDatabase":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._orders: List[Order] = []
        return cls._instance
```

**Перевірені сценарії:**
- `test_same_instance_returned` — два виклики `OrderDatabase()` повертають один об'єкт
- `test_data_shared_between_instances` — дані спільні між «різними» змінними
- `test_count_consistent` — лічильник однаковий з будь-якого посилання
- `test_no_duplicate_saves` — повторне збереження одного замовлення ігнорується
- `test_delete_from_db` — видалення за ID

### 3.2 Factory — `OrderFactory`

Абстрактна фабрика `OrderFactory` має три конкретні реалізації. `OrderFactoryProvider` — реєстр, що підтримує OCP.

```python
class OrderFactoryProvider:
    _registry = {
        "standard": StandardOrderFactory,
        "bulk":     BulkOrderFactory,
        "premium":  PremiumOrderFactory,
    }

    @classmethod
    def get_factory(cls, order_type: str) -> OrderFactory:
        factory_cls = cls._registry.get(order_type.lower())
        if factory_cls is None:
            raise ValueError(f"Unknown order type: '{order_type}'")
        return factory_cls()

    @classmethod
    def register(cls, order_type: str, factory_cls: type) -> None:
        cls._registry[order_type] = factory_cls   # OCP: відкрите для розширення
```

| Тип | Префікс ID | Особливість |
|-----|-----------|-------------|
| `standard` | `STD-` | Звичайне бронювання |
| `bulk` | `BULK-` | Знижка 15% на всі послуги |
| `premium` | `PREM-` | Пріоритетне розкладання |

**Перевірені сценарії:**
- Коректний префікс для кожного типу
- `ValueError` для невідомого типу
- Унікальність 20 згенерованих ID
- Правильний розрахунок знижки (200 × 0.85 = 170.0)
- Реєстрація та використання кастомної фабрики

### 3.3 Observer — `Notifiers`

`Order` реалізує `ISubject`; `TrainerNotifier`, `ReceptionNotifier`, `EmailNotifier` реалізують `IObserver`. Сповіщення відбувається при `order.confirm()` або `order.cancel()`.

```python
class Order(ISubject):
    def confirm(self) -> None:
        self.status = "confirmed"
        self.notify_observers("order_confirmed", {
            "order_id": self.order_id,
            "client":   self.client.name,
            "total":    self.total,
            "items":    [i.service.name for i in self.items],
        })

class TrainerNotifier(IObserver):
    def update(self, event: str, data: dict) -> None:
        if event == "order_confirmed":
            msg = f"[TRAINER] New session: {data['client']} | {data['items']}"
            self.notifications.append({"event": event, "message": msg})
```

**Перевірені сценарії:**
- Тренер отримує `order_confirmed`
- Рецепція отримує `order_cancelled`
- Email реагує на обидві події
- Три спостерігачі — кожен отримав по одному сповіщенню
- Після `unsubscribe` — сповіщень немає
- Повідомлення містить `order_id`

---

## Журнал тестування

### Підсумок

| Параметр | Значення |
|----------|----------|
| Всього тестів | **61** |
| Пройдено (PASSED) | **61** |
| Провалено (FAILED) | **0** |
| Пропущено (SKIPPED) | **0** |
| Тривалість | **0.29 с** |
| Python | 3.12.3 |
| pytest | 9.0.3 |
| Частина 1 (базові) | 20 тестів |
| Частина 2 (TDD) | 20 тестів |
| Частина 3 (патерни) | 21 тест |


### Консольний вивід pytest

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /fitness_gym
configfile: pytest.ini
collected 61 items

tests/test_part1_basic.py::TestTrainingService::test_create_service PASSED
tests/test_part1_basic.py::TestTrainingService::test_negative_price_raises PASSED
tests/test_part1_basic.py::TestTrainingService::test_zero_duration_raises PASSED
...
tests/test_part3_patterns.py::TestObserverPattern::test_notification_contains_order_id PASSED

============================== 61 passed in 0.29s ==============================
```

---

## Висновки

В ході виконання лабораторної роботи розроблено повноцінну систему управління фітнес-залом на мові Python. Досягнуті такі результати:

1. **SOLID-архітектура** — кожен клас має єдину відповідальність; система відкрита для розширення (новий тип замовлення = один рядок `register()`); всі залежності введені через інтерфейси.

2. **TDD-розробка** — для кожної функціональності спочатку писався тест (Red), потім мінімальна реалізація (Green), після чого виконувався рефакторинг (Refactor).

3. **Шаблони проектування:**
   - **Singleton** (`OrderDatabase`) — потокобезпечний єдиний реєстр замовлень
   - **Factory** (`OrderFactoryProvider`) — три типи замовлень з можливістю реєстрації нових без зміни коду
   - **Observer** (`Order` + `TrainerNotifier` / `ReceptionNotifier` / `EmailNotifier`) — відокремлена система сповіщень персоналу

4. **Тестове покриття** — 61 модульний тест, усі пройдено (0 помилок, 0.29 с)
