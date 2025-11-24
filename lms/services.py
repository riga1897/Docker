"""
Сервисные функции для LMS приложения.

Этот модуль содержит бизнес-логику для:
- Email рассылки подписчикам при обновлении курсов
- Получение списка подписчиков
- Проверка 4-часового окна для уведомлений

Следует паттерну Service Layer с простыми функциями (как в users/services.py).
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from django.core.mail import send_mail
from django.utils import timezone

if TYPE_CHECKING:
    from lms.models import Course, Subscription
    from users.models import User


def get_course_subscribers(course: "Course") -> list[int]:
    """
    Получает список ID подписчиков курса.

    Args:
        course: Курс, для которого нужно получить подписчиков

    Returns:
        Список ID пользователей, подписанных на курс
    """
    from lms.models import Subscription

    return list(Subscription.objects.filter(course=course).values_list("user", flat=True))


def should_send_notification(course: "Course") -> bool:
    """
    Проверяет, прошло ли достаточно времени с последнего уведомления.

    Дополнительное задание: уведомление отправляется только если
    курс не обновлялся более заданного количества часов (настраивается через .env).

    Args:
        course: Курс для проверки

    Returns:
        True если можно отправлять уведомление, False иначе
    """
    from django.conf import settings

    if course.last_notification_sent is None:
        return True

    time_since_last = timezone.now() - course.last_notification_sent
    cooldown_hours = timedelta(hours=settings.EMAIL_NOTIFICATION_COOLDOWN_HOURS)

    return time_since_last >= cooldown_hours


def send_course_update_email(course_id: int) -> int:
    """
    Отправляет email уведомления подписчикам об обновлении курса.

    Проверяет настроенное окно ожидания перед отправкой (из .env).
    Обновляет поле last_notification_sent после успешной отправки.

    Args:
        course_id: ID курса, который был обновлен

    Returns:
        Количество отправленных писем

    Raises:
        Course.DoesNotExist: Если курс не найден
    """
    from lms.models import Course

    course = Course.objects.get(id=course_id)

    # Проверяем 4-часовое окно
    if not should_send_notification(course):
        return 0

    # Получаем подписчиков с email адресами
    from users.models import User

    subscriber_ids = get_course_subscribers(course)
    subscribers = User.objects.filter(id__in=subscriber_ids, email__isnull=False)  # type: ignore[misc]

    if not subscribers.exists():
        return 0

    # Формируем email
    subject = f"Обновление курса: {course.title}"
    message = f"""
Здравствуйте!

Курс "{course.title}" был обновлен.

Описание: {course.description}

Заходите на платформу, чтобы ознакомиться с новыми материалами!

---
Это автоматическое уведомление от LMS.
"""

    recipient_list = [user.email for user in subscribers if user.email]

    # Отправляем письма
    sent_count = 0
    for recipient_email in recipient_list:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,  # Используется DEFAULT_FROM_EMAIL из settings
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            sent_count += 1
        except Exception:
            # В production нужно логировать ошибку
            continue

    # Обновляем время последнего уведомления
    if sent_count > 0:
        course.last_notification_sent = timezone.now()
        course.save(update_fields=["last_notification_sent"])

    return sent_count


def subscribe_user_to_course(user: "User", course: "Course") -> "Subscription":
    """
    Подписывает пользователя на курс.

    Создаёт новую подписку если её ещё нет. Если подписка уже существует,
    не создаёт дубликат (idempotent operation).

    Args:
        user: Пользователь
        course: Курс

    Returns:
        Subscription объект (созданный или существующий)
    """
    from lms.models import Subscription

    subscription, created = Subscription.objects.get_or_create(user=user, course=course)

    return subscription


def unsubscribe_user_from_course(user: "User", course: "Course") -> bool:
    """
    Отписывает пользователя от курса.

    Удаляет подписку если она существует. Если подписки нет,
    ничего не делает (idempotent operation).

    Args:
        user: Пользователь
        course: Курс

    Returns:
        True если подписка была удалена, False если подписки не было
    """
    from lms.models import Subscription

    deleted_count, _ = Subscription.objects.filter(user=user, course=course).delete()

    return deleted_count > 0


def toggle_subscription(user: "User", course: "Course") -> tuple[bool, str]:
    """
    Toggle подписки на курс.

    Если подписка существует - удаляет, если нет - создаёт.

    Args:
        user: Пользователь
        course: Курс

    Returns:
        tuple: (is_subscribed, message)
        - is_subscribed: True если подписан, False если отписан
        - message: Сообщение о действии
    """
    from lms.constants import SubscriptionMessages
    from lms.models import Subscription

    subscription_exists = Subscription.objects.filter(user=user, course=course).exists()

    if subscription_exists:
        unsubscribe_user_from_course(user, course)
        return False, SubscriptionMessages.REMOVED
    else:
        subscribe_user_to_course(user, course)
        return True, SubscriptionMessages.ADDED


def calculate_lessons_count(course: "Course") -> int:
    """
    Вычисляет количество уроков в курсе.

    Args:
        course: Курс

    Returns:
        Количество уроков в курсе
    """
    return course.lessons.count()  # type: ignore[attr-defined,no-any-return]


def check_user_subscription(course: "Course", user: "User | None") -> bool:
    """
    Проверяет, подписан ли пользователь на курс.

    Args:
        course: Курс
        user: Пользователь (может быть None для неаутентифицированных)

    Returns:
        True если пользователь аутентифицирован и подписан на курс,
        False в противном случае
    """
    if user is None or not user.is_authenticated:
        return False

    from lms.models import Subscription

    return Subscription.objects.filter(user=user, course=course).exists()
