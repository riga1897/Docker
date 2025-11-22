"""
Сервисные функции для работы с пользователями и платежами.

Этот модуль содержит:
- Функции для интеграции с Stripe API (платежи)
- Функции для управления пользователями (блокировка неактивных)
"""

import os
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, cast

import stripe
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

if TYPE_CHECKING:
    from lms.models import Course, Lesson
    from users.models import Payment, User

stripe.api_key = settings.STRIPE_SECRET_KEY


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
    amount_in_cents = int(amount * 100)

    product = stripe.Product.create(name=name)
    price = stripe.Price.create(
        product=product.id,
        unit_amount=amount_in_cents,
        currency="rub",
    )

    return product.id, price.id


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
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    if not session.url:
        raise ValueError("Stripe не вернул URL платежной сессии")

    return session.id, session.url


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
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":
        return "paid"
    elif session.payment_status == "unpaid":
        if session.status == "expired":
            return "expired"
        return "unpaid"
    else:
        return "canceled"


def get_stripe_success_url() -> str:
    """
    Получает URL для успешной оплаты.

    Returns:
        str: URL для редиректа после успешной оплаты
    """
    domain = os.getenv("REPLIT_DEV_DOMAIN", "localhost:8000")
    if "localhost" in domain:
        return f"http://{domain}/api/payments/success/"
    return f"https://{domain}/api/payments/success/"


def get_stripe_cancel_url() -> str:
    """
    Получает URL для отмены оплаты.

    Returns:
        str: URL для редиректа при отмене оплаты
    """
    domain = os.getenv("REPLIT_DEV_DOMAIN", "localhost:8000")
    if "localhost" in domain:
        return f"http://{domain}/api/payments/cancel/"
    return f"https://{domain}/api/payments/cancel/"


def get_inactive_users(days: int | None = None) -> QuerySet["User"]:
    """
    Получает пользователей, которые не заходили более N дней.

    Args:
        days: Количество дней неактивности (если None, берётся из .env)

    Returns:
        QuerySet пользователей, которые не заходили более N дней
    """
    from users.models import User

    days_value = days if days is not None else settings.INACTIVE_USER_DAYS
    cutoff_date = timezone.now() - timedelta(days=days_value)

    queryset = User.objects.filter(
        last_login__lt=cutoff_date,
        is_active=True,
    )

    return cast(QuerySet[User], queryset)


def block_inactive_users(days: int | None = None) -> int:
    """
    Блокирует пользователей, неактивных более N дней.

    Устанавливает is_active=False для пользователей, у которых
    last_login старше N дней.

    Args:
        days: Количество дней неактивности (если None, берётся из .env)

    Returns:
        Количество заблокированных пользователей
    """
    inactive_users = get_inactive_users(days)
    blocked_count = inactive_users.update(is_active=False)

    return blocked_count


def prepare_stripe_payment_data(
    amount: Decimal,
    course: "Course | None" = None,
    lesson: "Lesson | None" = None,
) -> dict[str, str]:
    """
    Подготавливает данные для Stripe платежа (создаёт продукт, цену, сессию).

    Вспомогательная функция для инициации Stripe платежей.
    Возвращает stripe_session_id и payment_link для сохранения в Payment модель.

    Args:
        amount: Сумма платежа
        course: Оплачиваемый курс (опционально)
        lesson: Оплачиваемый урок (опционально)

    Returns:
        dict с Stripe данными:
        {
            'stripe_session_id': ID Stripe checkout сессии,
            'payment_link': URL для оплаты,
        }

    Raises:
        stripe.error.StripeError: При ошибке взаимодействия со Stripe API
    """
    if course:
        product_name = f"Курс: {course.title}"
    elif lesson:
        product_name = f"Урок: {lesson.title}"
    else:
        product_name = "Платёж"

    _product_id, price_id = create_stripe_product_and_price(product_name, amount)

    success_url = get_stripe_success_url()
    cancel_url = get_stripe_cancel_url()

    session_id, payment_url = create_stripe_checkout_session(price_id, success_url, cancel_url)

    return {
        "stripe_session_id": session_id,
        "payment_link": payment_url,
    }


def refresh_payment_status(payment_id: int) -> dict[str, str]:
    """
    Проверяет актуальный статус платежа в Stripe.

    Args:
        payment_id: ID платежа в БД

    Returns:
        dict с информацией о статусе:
        {
            'payment_status': 'paid'|'unpaid'|'expired'|'canceled',
            'message': 'Платёж успешно завершён',
        }

    Raises:
        Payment.DoesNotExist: Если платёж не найден
        ValueError: Если платёж не был создан через Stripe
        stripe.error.StripeError: При ошибке взаимодействия со Stripe API
    """
    from users.models import Payment

    payment = Payment.objects.get(id=payment_id)

    if payment.payment_method != "stripe" or not payment.stripe_session_id:
        raise ValueError("Платёж не был создан через Stripe")

    payment_status = check_stripe_payment_status(payment.stripe_session_id)

    status_messages = {
        "paid": "Платёж успешно завершён",
        "unpaid": "Платёж ожидает оплаты",
        "expired": "Срок действия платёжной ссылки истёк",
        "canceled": "Платёж был отменён",
    }

    return {
        "payment_status": payment_status,
        "message": status_messages.get(payment_status, "Неизвестный статус"),
    }


def list_user_payments(user: "User") -> QuerySet["Payment"]:
    """
    Получает все платежи пользователя с оптимизацией запросов.

    Args:
        user: Пользователь

    Returns:
        QuerySet платежей пользователя с предзагруженными связями
    """
    from users.models import Payment

    queryset = Payment.objects.select_related("owner", "course", "lesson").filter(owner=user).order_by("-payment_date")

    return cast(QuerySet["Payment"], queryset)
