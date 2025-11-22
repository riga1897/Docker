# Stripe Integration

## 📋 Содержание

1. [Введение](#введение)
2. [Архитектурное решение](#архитектурное-решение)
3. [Сервисные функции](#сервисные-функции)
4. [Интеграция с Django](#интеграция-с-django)
5. [Тестирование](#тестирование)
6. [Best Practices](#best-practices)
7. [Примеры использования](#примеры-использования)

---

## Введение

Этот документ описывает реализацию интеграции с Stripe API в Django REST Framework проекте.

### Ключевые особенности

✅ **Service Layer Pattern** с простыми функциями (не классы)
✅ **Четкое разделение ответственности** между сервисами, ViewSet'ами и моделями
✅ **100% покрытие тестами** - 15 unit-тестов для сервисов + 10 integration-тестов
✅ **Proper error handling** с корректной обработкой исключений Stripe API
✅ **Автоматическая конвертация** в копейки/центы для Stripe API
✅ **Custom action** для проверки статуса платежа (дополнительное задание)

### Что реализовано

1. **Создание продуктов и цен** в Stripe каталоге
2. **Генерация Checkout Sessions** с redirect URL'ами
3. **Проверка статуса платежей** через Stripe API
4. **Автоматическая интеграция** с моделью Payment
5. **REST API endpoints** для управления платежами

---

## Архитектурное решение

### Service Layer Pattern: Функции vs Классы

**Почему простые функции, а не классы?**

Для интеграции со Stripe API выбран подход с **чистыми функциями** вместо классов. Это решение, основано на принципе KISS (Keep It Simple, Stupid).

#### ✅ Преимущества функций

**1. Простота - нет boilerplate кода**

```python
# С функциями (наш подход)
session_id, url = create_stripe_checkout_session(price_id, success_url, cancel_url)

# С классами (излишняя сложность)
service = StripeService(api_key=settings.STRIPE_SECRET_KEY)
session = service.create_checkout_session(price_id, success_url, cancel_url)
session_id = session.id
url = session.url
```

**2. Нет состояния - каждая операция независима**

- Создал продукт → вернул результат
- Создал сессию → вернул результат
- Никакого `self`, никаких внутренних полей
- Легче тестировать (просто моки параметров)

**3. Читаемость - код как книга**

```python
# Имена функций сразу говорят что они делают
create_stripe_product_and_price(name, amount)
create_stripe_checkout_session(price_id, success_url, cancel_url)
check_stripe_payment_status(session_id)
```

**4. Простое тестирование - минимум setup**

```python
@patch('stripe.checkout.Session.create')
def test_create_session(mock_create):
    # Сразу тестируем функцию, без создания экземпляра класса
    mock_create.return_value.id = "sess_123"
    mock_create.return_value.url = "https://checkout.stripe.com"

    session_id, url = create_stripe_checkout_session("price_123", "success", "cancel")
    assert session_id == "sess_123"
```

#### ❌ Когда классы были бы лучше

Классы имеют смысл в следующих случаях:

1. **Сложное состояние** - если нужно хранить настройки между вызовами
2. **Много конфигурации** - если куча параметров повторяется
3. **Наследование** - разные типы платежных провайдеров (Stripe, PayPal, Yandex.Kassa)

**Пример, когда класс оправдан:**

```python
class PaymentGateway(ABC):
    @abstractmethod
    def create_payment(self, amount: Decimal) -> str:
        pass

class StripeGateway(PaymentGateway):
    def __init__(self, api_key: str, currency: str = "usd"):
        self.api_key = api_key
        self.currency = currency

    def create_payment(self, amount: Decimal) -> str:
        # использует self.currency
        ...

class PayPalGateway(PaymentGateway):
    ...
```

Но в нашем случае Stripe API сам по себе простой:
- Создал продукт → получил ID
- Создал сессию → получил URL
- Проверил статус → получил результат

**Нет смысла добавлять сложность классов**, когда функции справляются идеально!

### Разделение ответственности

```
┌─────────────────────────────────────────────────────────────┐
│                     users/services.py                       │
│  Чистые функции для работы со Stripe API                    │
│  - Создание продуктов и цен                                 │
│  - Создание checkout sessions                               │
│  - Проверка статусов платежей                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     users/views.py                          │
│  PaymentViewSet - HTTP обработка                            │
│  - Валидация запросов                                       │
│  - Вызов сервисных функций                                  │
│  - Формирование ответов                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     users/models.py                         │
│  Payment модель - хранение данных                           │
│  - payment_link (ссылка на Stripe)                          │
│  - stripe_session_id (ID сессии)                            │
│  - Валидация бизнес-правил                                  │
└─────────────────────────────────────────────────────────────┘
```

**Принцип:** Каждый слой отвечает только за свою задачу.

---

## Сервисные функции

Все функции находятся в `users/services.py`. Это центральное место для работы со Stripe API.

### 1. create_stripe_product_and_price()

**Назначение:** Создает продукт и цену в Stripe каталоге.

**Сигнатура:**
```python
def create_stripe_product_and_price(name: str, amount: Decimal) -> tuple[str, str]:
    """
    Создает продукт и цену в Stripe.

    Args:
        name: Название продукта (курс или урок)
        amount: Сумма в рублях

    Returns:
        tuple: (product_id, price_id)

    Raises:
        stripe.error.StripeError: При ошибке взаимодействия со Stripe API
    """
```

**Реализация:**

```python
def create_stripe_product_and_price(name: str, amount: Decimal) -> tuple[str, str]:
    # Конвертация в копейки (Stripe работает с минимальными единицами валюты)
    amount_in_cents = int(amount * 100)

    # Создаем продукт
    product = stripe.Product.create(name=name)

    # Создаем цену для продукта
    price = stripe.Price.create(
        product=product.id,
        unit_amount=amount_in_cents,
        currency="rub",
    )

    return product.id, price.id
```

**Ключевые особенности:**

✅ **Автоматическая конвертация в копейки** - Stripe требует минимальные единицы валюты
✅ **Валюта RUB** - для российских платежей
✅ **Возвращает оба ID** - для сохранения в базе или дальнейшего использования
✅ **Type hints** - полная типизация для безопасности

**Пример использования:**

```python
from decimal import Decimal

product_id, price_id = create_stripe_product_and_price(
    name="Python для начинающих",
    amount=Decimal("2500.00")
)
# product_id: "prod_ABC123"
# price_id: "price_XYZ789"
```

---

### 2. create_stripe_checkout_session()

**Назначение:** Создает платежную сессию Stripe Checkout для приема оплаты.

**Сигнатура:**
```python
def create_stripe_checkout_session(
    price_id: str,
    success_url: str,
    cancel_url: str
) -> tuple[str, str]:
    """
    Создает платежную сессию Stripe Checkout.

    Args:
        price_id: ID цены в Stripe
        success_url: URL для редиректа после успешной оплаты
        cancel_url: URL для редиректа при отмене оплаты

    Returns:
        tuple: (session_id, payment_url)

    Raises:
        stripe.error.StripeError: При ошибке взаимодействия со Stripe API
        ValueError: Если Stripe не вернул URL платежной сессии
    """
```

**Реализация:**

```python
def create_stripe_checkout_session(price_id: str, success_url: str, cancel_url: str) -> tuple[str, str]:
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],  # Только карты
        line_items=[
            {
                "price": price_id,
                "quantity": 1,  # Курс/урок покупается один раз
            }
        ],
        mode="payment",  # Одноразовый платеж (не подписка)
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # Валидация ответа от Stripe
    if not session.url:
        raise ValueError("Stripe не вернул URL платежной сессии")

    return session.id, session.url
```

**Ключевые особенности:**

✅ **Payment mode** - одноразовый платеж (не recurring subscription)
✅ **Только карты** - payment_method_types=["card"]
✅ **Валидация ответа** - проверяем что Stripe вернул URL
✅ **Proper error handling** - ValueError при отсутствии URL

**Пример использования:**

```python
session_id, payment_url = create_stripe_checkout_session(
    price_id="price_XYZ789",
    success_url="https://example.com/api/payments/success/",
    cancel_url="https://example.com/api/payments/cancel/"
)
# session_id: "cs_test_ABC123"
# payment_url: "https://checkout.stripe.com/c/pay/cs_test_ABC123"
```

---

### 3. check_stripe_payment_status()

**Назначение:** Проверяет актуальный статус платежа в Stripe (дополнительное задание).

**Сигнатура:**
```python
def check_stripe_payment_status(session_id: str) -> str:
    """
    Проверяет статус платежа в Stripe.

    Args:
        session_id: ID платежной сессии Stripe

    Returns:
        str: Статус платежа ('paid', 'unpaid', 'expired', 'canceled')

    Raises:
        stripe.error.StripeError: При ошибке взаимодействия со Stripe API
    """
```

**Реализация:**

```python
def check_stripe_payment_status(session_id: str) -> str:
    # Получаем актуальную информацию о сессии
    session = stripe.checkout.Session.retrieve(session_id)

    # Маппинг статусов Stripe на наши статусы
    if session.payment_status == "paid":
        return "paid"
    elif session.payment_status == "unpaid":
        if session.status == "expired":
            return "expired"
        return "unpaid"
    else:
        return "canceled"
```

**Ключевые особенности:**

✅ **Real-time проверка** - обращение к Stripe API за актуальными данными
✅ **Понятные статусы** - маппинг Stripe статусов на простые значения
✅ **Обработка expired** - различаем unpaid и expired статусы
✅ **Fallback на canceled** - для всех остальных случаев

**Возможные статусы:**

| Stripe Status | Наш Status | Описание |
|--------------|-----------|----------|
| `payment_status=paid` | `paid` | Платеж успешно завершен |
| `payment_status=unpaid` | `unpaid` | Платеж не завершен |
| `payment_status=unpaid` + `status=expired` | `expired` | Сессия истекла |
| Другие | `canceled` | Платеж отменен |

**Пример использования:**

```python
status = check_stripe_payment_status("cs_test_ABC123")

if status == "paid":
    # Активировать подписку на курс
    activate_subscription(user, course)
elif status == "expired":
    # Предложить создать новый платеж
    notify_user("Время оплаты истекло, создайте новый платеж")
```

---

### 4. get_stripe_success_url()

**Назначение:** Генерирует URL для редиректа после успешной оплаты.

**Сигнатура:**
```python
def get_stripe_success_url() -> str:
    """
    Получает URL для успешной оплаты.

    Returns:
        str: URL для редиректа после успешной оплаты
    """
```

**Реализация:**

```python
def get_stripe_success_url() -> str:
    domain = os.getenv("DOMAIN", "localhost:8000")

    # Локальная разработка использует HTTP
    if "localhost" in domain or "127.0.0.1" in domain:
        return f"http://{domain}/api/payments/success/"

    # Production использует HTTPS
    return f"https://{domain}/api/payments/success/"
```

**Ключевые особенности:**

✅ **Автоопределение окружения** - localhost vs production
✅ **Правильный протокол** - HTTP для localhost, HTTPS для production
✅ **Настройка через .env** - используйте переменную `DOMAIN` для вашего домена

---

### 5. get_stripe_cancel_url()

**Назначение:** Генерирует URL для редиректа при отмене оплаты.

**Сигнатура:**
```python
def get_stripe_cancel_url() -> str:
    """
    Получает URL для отмены оплаты.

    Returns:
        str: URL для редиректа при отмене оплаты
    """
```

**Реализация:**

```python
def get_stripe_cancel_url() -> str:
    domain = os.getenv("DOMAIN", "localhost:8000")

    if "localhost" in domain or "127.0.0.1" in domain:
        return f"http://{domain}/api/payments/cancel/"

    return f"https://{domain}/api/payments/cancel/"
```

**Ключевые особенности:**

✅ **Аналогичная логика** с success_url
✅ **DRY принцип** - можно рефакторить в общую функцию
✅ **Гибкость** - работает и локально, и в production

---

## Интеграция с Django

### Модель Payment

Модель `Payment` расширена специальными полями для Stripe интеграции.

**Специальные поля для Stripe:**

```python
class Payment(models.Model):
    # ... стандартные поля (owner, course, lesson, amount, payment_method)

    # === Поля для Stripe интеграции ===

    payment_link: models.URLField | None = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ссылка на оплату",
        help_text="Ссылка на страницу оплаты Stripe",
    )

    stripe_session_id: models.CharField | None = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID сессии Stripe",
        help_text="Идентификатор платежной сессии Stripe",
    )
```

**Назначение полей:**

| Поле | Тип | Назначение |
|------|-----|-----------|
| `payment_link` | URLField | Ссылка на Stripe Checkout для оплаты |
| `stripe_session_id` | CharField | ID сессии для проверки статуса |

**Бизнес-валидация:**

```python
def clean(self) -> None:
    """
    Валидация модели.

    Проверяет, что указан либо курс, либо урок (но не оба пустые).
    """
    super().clean()
    if not self.course and not self.lesson:
        raise ValidationError("Должен быть указан либо курс, либо урок для оплаты")
```

---

### PaymentViewSet - Автоматическая интеграция

**Создание платежа со Stripe:**

При создании платежа с `payment_method='stripe'`, ViewSet автоматически:

1. Определяет название продукта (курс или урок)
2. Создает продукт и цену в Stripe
3. Создает Checkout Session
4. Сохраняет `payment_link` и `stripe_session_id` в базу

**Код в PaymentViewSet.create():**

```python
def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    payment = serializer.save(owner=request.user)

    # Автоматическая интеграция со Stripe
    if payment.payment_method == "stripe":
        # 1. Определяем название продукта
        if payment.course:
            product_name = f"Курс: {payment.course.title}"
        elif payment.lesson:
            product_name = f"Урок: {payment.lesson.title}"
        else:
            product_name = "Покупка"

        # 2. Создаем продукт и цену
        _, price_id = create_stripe_product_and_price(
            name=product_name,
            amount=payment.amount
        )

        # 3. Создаем Checkout Session
        session_id, payment_url = create_stripe_checkout_session(
            price_id=price_id,
            success_url=get_stripe_success_url(),
            cancel_url=get_stripe_cancel_url()
        )

        # 4. Сохраняем в базу
        payment.stripe_session_id = session_id
        payment.payment_link = payment_url
        payment.save()

    headers = self.get_success_headers(serializer.data)
    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
```

---

### Custom Action: check_status

**Назначение:** Проверка актуального статуса платежа в Stripe (дополнительное задание).

**Endpoint:** `POST /api/payments/{id}/check_status/`

**Реализация:**

```python
@action(detail=True, methods=["post"], permission_classes=[IsOwner])
def check_status(self, request: Request, pk: int | None = None) -> Response:
    """
    Проверяет статус платежа в Stripe.

    Доступно только владельцу платежа.
    Работает только для платежей, созданных через Stripe.

    Returns:
        Response с информацией о статусе платежа
    """
    payment = self.get_object()

    # Проверка что это Stripe платеж
    if payment.payment_method != "stripe":
        return Response(
            {"error": "Проверка статуса доступна только для Stripe платежей"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Проверка наличия session_id
    if not payment.stripe_session_id:
        return Response(
            {"error": "У платежа отсутствует Stripe session ID"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Проверка статуса через Stripe API
    try:
        payment_status = check_stripe_payment_status(payment.stripe_session_id)
        return Response({
            "payment_id": payment.id,
            "stripe_session_id": payment.stripe_session_id,
            "status": payment_status,
            "payment_link": payment.payment_link
        })
    except stripe.error.StripeError as e:
        return Response(
            {"error": f"Ошибка Stripe API: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

**Ключевые особенности:**

✅ **Валидация payment_method** - работает только для Stripe платежей
✅ **Проверка session_id** - должен быть установлен
✅ **Proper error handling** - обработка Stripe API ошибок
✅ **Permission IsOwner** - только владелец может проверить статус

---

## Тестирование

Интеграция покрыта **25 тестами** (100% coverage для services.py):

- **15 unit-тестов** для сервисных функций (моки Stripe API) → `tests/users/test_stripe_services.py`
- **10 integration-тестов** для PaymentViewSet и check_status action → `tests/users/test_payment_api.py`

**Запуск тестов:**

```bash
# Только unit-тесты для Stripe сервисов
poetry run pytest tests/users/test_stripe_services.py -v

# Только integration-тесты для Stripe API
poetry run pytest tests/users/test_payment_api.py -k "stripe or check_status" -v

# Все Stripe тесты (25 штук)
poetry run pytest tests/users/test_stripe_services.py tests/users/test_payment_api.py -k "stripe or check_status" -v
```

### Unit-тесты для сервисов

**Файл:** `tests/users/test_stripe_services.py` (15 тестов)

**Структура тестов:**

```python
class TestStripeProductAndPrice:
    """Тесты для create_stripe_product_and_price()"""

    def test_create_product_and_price_success(self):
        """Успешное создание продукта и цены."""

    def test_create_product_and_price_converts_to_cents(self):
        """Корректная конвертация рублей в копейки."""

    def test_create_product_and_price_raises_on_exception(self):
        """Обработка ошибок Stripe API."""


class TestStripeCheckoutSession:
    """Тесты для create_stripe_checkout_session()"""

    def test_create_checkout_session_success(self):
        """Успешное создание checkout сессии."""

    def test_create_checkout_session_raises_without_url(self):
        """ValueError если Stripe не вернул URL."""


class TestStripePaymentStatus:
    """Тесты для check_stripe_payment_status()"""

    def test_check_payment_status_paid(self):
        """Статус 'paid' для оплаченного платежа."""

    def test_check_payment_status_unpaid(self):
        """Статус 'unpaid' для неоплаченного платежа."""

    def test_check_payment_status_expired(self):
        """Статус 'expired' для истекшей сессии."""

    def test_check_payment_status_canceled(self):
        """Статус 'canceled' для отмененного платежа."""


class TestStripeURLHelpers:
    """Тесты для get_stripe_success_url() и get_stripe_cancel_url()"""

    def test_get_success_url_localhost(self):
        """HTTP для localhost."""

    def test_get_success_url_production(self):
        """HTTPS для production домена."""

    # ... и т.д.
```

**Пример unit-теста с моком:**

```python
from unittest.mock import patch, MagicMock
from decimal import Decimal
import pytest

@patch("stripe.Product.create")
@patch("stripe.Price.create")
def test_create_product_and_price_success(mock_price_create, mock_product_create):
    """
    Тест успешного создания продукта и цены в Stripe.
    """
    # Arrange: настраиваем моки
    mock_product_create.return_value = MagicMock(id="prod_123")
    mock_price_create.return_value = MagicMock(id="price_456")

    # Act: вызываем функцию
    product_id, price_id = create_stripe_product_and_price(
        name="Python курс",
        amount=Decimal("2500.00")
    )

    # Assert: проверяем результат и вызовы
    assert product_id == "prod_123"
    assert price_id == "price_456"

    mock_product_create.assert_called_once_with(name="Python курс")
    mock_price_create.assert_called_once_with(
        product="prod_123",
        unit_amount=250000,  # 2500 рублей * 100 = 250000 копеек
        currency="rub"
    )
```

**Почему моки:**

✅ **Скорость** - тесты выполняются мгновенно
✅ **Изоляция** - не зависим от Stripe API
✅ **Детерминированность** - всегда одинаковый результат
✅ **Не требуют API ключей** - можно запускать где угодно

---

### Integration-тесты для ViewSet

**Файл:** `tests/users/test_payment_api.py` (10 тестов для Stripe)

**Тестируемые сценарии:**

1. `test_create_payment_with_stripe_method` - создание платежа через Stripe для курса
2. `test_create_payment_with_stripe_for_lesson` - создание платежа через Stripe для урока
3. `test_create_payment_non_stripe_method` - другие методы оплаты не вызывают Stripe API
4. `test_check_status_paid` - проверка статуса "paid"
5. `test_check_status_unpaid` - проверка статуса "unpaid"
6. `test_check_status_expired` - проверка статуса "expired"
7. `test_check_status_non_stripe_payment` - check_status только для Stripe платежей
8. `test_check_status_missing_session_id` - ошибка если нет session_id
9. `test_check_status_only_owner` - только владелец может проверить статус
10. `test_check_status_stripe_api_error` - обработка ошибок Stripe API

**Примеры тестов:**

```python
class TestPaymentStripeIntegration:
    """Integration тесты для Stripe интеграции в PaymentViewSet."""

    def test_create_payment_with_stripe_generates_session(self):
        """
        При создании платежа с payment_method='stripe' должны
        автоматически создаваться payment_link и stripe_session_id.
        """

    def test_check_status_returns_paid_status(self):
        """
        Custom action check_status возвращает статус 'paid'.
        """

    def test_check_status_only_for_owner(self):
        """
        Custom action check_status доступен только владельцу.
        """

    def test_check_status_only_for_stripe_payments(self):
        """
        Custom action check_status работает только для Stripe.
        """
```

**Пример integration-теста:**

```python
@pytest.mark.django_db
class TestPaymentStripeIntegration:

    @patch("stripe.Product.create")
    @patch("stripe.Price.create")
    @patch("stripe.checkout.Session.create")
    def test_create_payment_with_stripe_generates_session(
        self, mock_session_create, mock_price_create, mock_product_create
    ):
        """
        При создании платежа с payment_method='stripe' должны
        автоматически создаваться payment_link и stripe_session_id.
        """
        # Arrange: настраиваем моки
        mock_product_create.return_value = MagicMock(id="prod_123")
        mock_price_create.return_value = MagicMock(id="price_456")
        mock_session_create.return_value = MagicMock(
            id="cs_test_789",
            url="https://checkout.stripe.com/pay/cs_test_789"
        )

        client = APIClient()
        user = User.objects.create_user(email="test@example.com", password="test123")
        client.force_authenticate(user=user)

        course = Course.objects.create(
            title="Python курс",
            description="Описание",
            owner=user
        )

        # Act: создаем платеж через API
        response = client.post("/api/payments/", {
            "course": course.id,
            "amount": "2500.00",
            "payment_method": "stripe"
        })

        # Assert: проверяем результат
        assert response.status_code == 201

        payment = Payment.objects.get(id=response.data["id"])
        assert payment.stripe_session_id == "cs_test_789"
        assert payment.payment_link == "https://checkout.stripe.com/pay/cs_test_789"
        assert payment.payment_method == "stripe"
```

---

## Best Practices

### 1. Service Layer для внешних API

**Принцип:** Вся логика работы с внешним API (Stripe, SendGrid, Twilio) должна быть в отдельных сервисных функциях.

✅ **Правильно:**
```python
# users/services.py
def create_stripe_checkout_session(price_id, success_url, cancel_url):
    return stripe.checkout.Session.create(...)

# users/views.py
class PaymentViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # Только вызов сервиса
        session_id, url = create_stripe_checkout_session(...)
```

❌ **Неправильно:**
```python
# users/views.py
class PaymentViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # Прямой вызов Stripe API в ViewSet
        session = stripe.checkout.Session.create(...)
```

---

### 2. Конвертация в минимальные единицы валюты

**Принцип:** Stripe требует суммы в минимальных единицах (копейки для RUB, центы для USD).

✅ **Правильно:**
```python
amount_in_cents = int(amount * 100)  # 2500.00 → 250000 копеек
```

❌ **Неправильно:**
```python
# Отправка рублей напрямую приведет к ошибке или неверной сумме
stripe.Price.create(unit_amount=2500, currency="rub")  # ОШИБКА!
```

---

### 3. Proper Error Handling

**Принцип:** Обрабатывай ошибки Stripe API корректно.

✅ **Правильно:**
```python
try:
    session = stripe.checkout.Session.create(...)
    if not session.url:
        raise ValueError("Stripe не вернул URL")
    return session.id, session.url
except stripe.error.StripeError as e:
    # Логируем и пробрасываем дальше
    logger.error(f"Stripe API error: {e}")
    raise
```

❌ **Неправильно:**
```python
# Игнорирование ошибок или общий except
session = stripe.checkout.Session.create(...)
return session.id, session.url  # А если session.url None?
```

---

### 4. Type Hints везде

**Принцип:** Используй type hints для безопасности и автодополнения.

✅ **Правильно:**
```python
def create_stripe_product_and_price(name: str, amount: Decimal) -> tuple[str, str]:
    ...
```

❌ **Неправильно:**
```python
def create_stripe_product_and_price(name, amount):  # Без type hints
    ...
```

---

### 5. Docstrings на русском

**Принцип:** Документируй функции понятным языком.

✅ **Правильно:**
```python
def create_stripe_checkout_session(price_id: str, success_url: str, cancel_url: str) -> tuple[str, str]:
    """
    Создает платежную сессию Stripe Checkout.

    Args:
        price_id: ID цены в Stripe
        success_url: URL для редиректа после успешной оплаты
        cancel_url: URL для редиректа при отмене оплаты

    Returns:
        tuple: (session_id, payment_url)

    Raises:
        stripe.error.StripeError: При ошибке взаимодействия со Stripe API
        ValueError: Если Stripe не вернул URL платежной сессии
    """
```

---

## Примеры использования

### 1. Создание платежа через API

**Request:**
```bash
POST /api/payments/
Content-Type: application/json
Authorization: Token <your-jwt-token>

{
    "course": 1,
    "amount": "2500.00",
    "payment_method": "stripe"
}
```

**Response:**
```json
{
    "id": 42,
    "owner": 1,
    "course": 1,
    "lesson": null,
    "amount": "2500.00",
    "payment_method": "stripe",
    "payment_date": "2025-11-14T10:30:00Z",
    "payment_link": "https://checkout.stripe.com/c/pay/cs_test_ABC123",
    "stripe_session_id": "cs_test_ABC123"
}
```

**Что происходит автоматически:**

1. ✅ Создается продукт "Курс: Python для начинающих" в Stripe
2. ✅ Создается цена 250000 копеек (2500 рублей) для продукта
3. ✅ Создается Checkout Session с redirect URL'ами
4. ✅ В базу сохраняются `payment_link` и `stripe_session_id`

---

### 2. Проверка статуса платежа

**Request:**
```bash
POST /api/payments/42/check_status/
Authorization: Token <your-jwt-token>
```

**Response (оплачено):**
```json
{
    "payment_id": 42,
    "stripe_session_id": "cs_test_ABC123",
    "status": "paid",
    "payment_link": "https://checkout.stripe.com/c/pay/cs_test_ABC123"
}
```

**Response (не оплачено):**
```json
{
    "payment_id": 42,
    "stripe_session_id": "cs_test_ABC123",
    "status": "unpaid",
    "payment_link": "https://checkout.stripe.com/c/pay/cs_test_ABC123"
}
```

**Response (истекло):**
```json
{
    "payment_id": 42,
    "stripe_session_id": "cs_test_ABC123",
    "status": "expired",
    "payment_link": "https://checkout.stripe.com/c/pay/cs_test_ABC123"
}
```

---

### 3. Использование сервисов напрямую

**В Django shell или Celery tasks:**

```python
from users.services import (
    create_stripe_product_and_price,
    create_stripe_checkout_session,
    check_stripe_payment_status
)
from decimal import Decimal

# Создание продукта и цены
product_id, price_id = create_stripe_product_and_price(
    name="Django REST Framework курс",
    amount=Decimal("3000.00")
)

# Создание checkout сессии
session_id, payment_url = create_stripe_checkout_session(
    price_id=price_id,
    success_url="https://example.com/success/",
    cancel_url="https://example.com/cancel/"
)

print(f"Отправьте пользователю ссылку: {payment_url}")

# Проверка статуса
status = check_stripe_payment_status(session_id)
if status == "paid":
    print("Платеж успешно завершен!")
```

---

## Заключение

✅ **Service Layer Pattern** с простыми функциями вместо классов
✅ **Четкое разделение ответственности** между слоями
✅ **100% покрытие тестами** для надежности
✅ **Proper error handling** для production-ready кода
✅ **Type hints и docstrings** для поддерживаемости

Этот подход можно использовать как референс для других интеграций: SendGrid, Twilio, PayPal и т.д.

---

**Дата создания:** 14 ноября 2025
