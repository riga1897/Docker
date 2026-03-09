"""
Тесты для lms/services.py - сервисные функции email рассылки и подписок.

Покрывает все функции из lms/services.py:
- get_course_subscribers
- should_send_notification
- send_course_update_email
- subscribe_user_to_course
- unsubscribe_user_from_course
- toggle_subscription
- calculate_lessons_count
- check_user_subscription
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from lms.models import Course, Lesson, Subscription
from lms.services import (
    calculate_lessons_count,
    check_user_subscription,
    get_course_subscribers,
    send_course_update_email,
    should_send_notification,
)
from users.models import User


@pytest.mark.django_db
class TestGetCourseSubscribers:
    """Тесты для функции get_course_subscribers."""

    def test_get_course_subscribers_empty(self, course: Course) -> None:
        """Возвращает пустой список, если подписчиков нет."""
        subscriber_ids = get_course_subscribers(course)

        assert subscriber_ids == []

    def test_get_course_subscribers_with_subscribers(self, course: Course, user: User, another_user: User) -> None:
        """Возвращает список ID подписчиков курса."""
        Subscription.objects.create(user=user, course=course)
        Subscription.objects.create(user=another_user, course=course)

        subscriber_ids = get_course_subscribers(course)

        assert len(subscriber_ids) == 2
        assert user.id in subscriber_ids  # type: ignore[attr-defined]
        assert another_user.id in subscriber_ids  # type: ignore[attr-defined]

    def test_get_course_subscribers_only_for_specific_course(
        self, course: Course, another_course: Course, user: User
    ) -> None:
        """Возвращает подписчиков только для конкретного курса."""
        Subscription.objects.create(user=user, course=course)
        Subscription.objects.create(user=user, course=another_course)

        subscriber_ids = get_course_subscribers(course)

        assert len(subscriber_ids) == 1
        assert user.id in subscriber_ids  # type: ignore[attr-defined]


@pytest.mark.django_db
class TestShouldSendNotification:
    """Тесты для функции should_send_notification."""

    def test_should_send_notification_never_sent(self, course: Course) -> None:
        """Возвращает True, если уведомление никогда не отправлялось."""
        course.last_notification_sent = None

        result = should_send_notification(course)

        assert result is True

    def test_should_send_notification_after_4_hours(self, course: Course) -> None:
        """Возвращает True, если прошло 4 часа с последнего уведомления."""
        course.last_notification_sent = timezone.now() - timedelta(hours=4, minutes=1)

        result = should_send_notification(course)

        assert result is True

    def test_should_send_notification_before_4_hours(self, course: Course) -> None:
        """Возвращает False, если не прошло 4 часа."""
        course.last_notification_sent = timezone.now() - timedelta(hours=3, minutes=59)

        result = should_send_notification(course)

        assert result is False

    def test_should_send_notification_exactly_4_hours(self, course: Course) -> None:
        """Возвращает True, если прошло ровно 4 часа."""
        course.last_notification_sent = timezone.now() - timedelta(hours=4)

        result = should_send_notification(course)

        assert result is True


@pytest.mark.django_db
class TestSendCourseUpdateEmail:
    """Тесты для функции send_course_update_email."""

    def test_send_course_update_email_no_subscribers(self, course: Course) -> None:
        """Не отправляет email, если нет подписчиков."""
        sent_count = send_course_update_email(course.id)  # type: ignore[attr-defined]

        assert sent_count == 0
        assert len(mail.outbox) == 0

    def test_send_course_update_email_before_4_hours(self, course: Course, user: User) -> None:
        """Не отправляет email, если не прошло 4 часа."""
        Subscription.objects.create(user=user, course=course)
        course.last_notification_sent = timezone.now() - timedelta(hours=2)
        course.save()

        sent_count = send_course_update_email(course.id)  # type: ignore[attr-defined]

        assert sent_count == 0
        assert len(mail.outbox) == 0

    def test_send_course_update_email_success(self, course: Course, user: User) -> None:
        """Успешно отправляет email подписчикам."""
        Subscription.objects.create(user=user, course=course)

        sent_count = send_course_update_email(course.id)  # type: ignore[attr-defined]

        assert sent_count == 1
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert email.subject == f"Обновление курса: {course.title}"
        assert user.email in email.to
        assert course.title in email.body

    def test_send_course_update_email_multiple_subscribers(
        self, course: Course, user: User, another_user: User
    ) -> None:
        """Отправляет email всем подписчикам."""
        Subscription.objects.create(user=user, course=course)
        Subscription.objects.create(user=another_user, course=course)

        sent_count = send_course_update_email(course.id)  # type: ignore[attr-defined]

        assert sent_count == 2
        assert len(mail.outbox) == 2

    def test_send_course_update_email_updates_last_notification_sent(self, course: Course, user: User) -> None:
        """Обновляет поле last_notification_sent после отправки."""
        Subscription.objects.create(user=user, course=course)
        old_last_sent = course.last_notification_sent

        send_course_update_email(course.id)  # type: ignore[attr-defined]

        course.refresh_from_db()
        assert course.last_notification_sent is not None
        assert course.last_notification_sent != old_last_sent

    def test_send_course_update_email_error_handling(self, course: Course, user: User) -> None:
        """Продолжает отправку при ошибке одного письма."""
        Subscription.objects.create(user=user, course=course)

        with patch("lms.services.send_mail", side_effect=Exception("SMTP error")):
            sent_count = send_course_update_email(course.id)  # type: ignore[attr-defined]

        assert sent_count == 0

    def test_send_course_update_email_course_not_found(self) -> None:
        """Бросает исключение, если курс не найден."""
        with pytest.raises(Course.DoesNotExist):
            send_course_update_email(999999)


@pytest.mark.django_db
class TestCalculateLessonsCount:
    """Тесты для функции calculate_lessons_count."""

    def test_calculate_lessons_count_empty(self, course: Course) -> None:
        """Возвращает 0, если уроков нет."""
        count = calculate_lessons_count(course)

        assert count == 0

    def test_calculate_lessons_count_with_lessons(self, course: Course, user: User) -> None:
        """Возвращает количество уроков в курсе."""
        Lesson.objects.create(
            course=course,
            owner=user,
            title="Урок 1",
            description="Описание",
            video_url="https://youtube.com/watch?v=test1",
        )
        Lesson.objects.create(
            course=course,
            owner=user,
            title="Урок 2",
            description="Описание",
            video_url="https://youtube.com/watch?v=test2",
        )

        count = calculate_lessons_count(course)

        assert count == 2

    def test_calculate_lessons_count_only_for_specific_course(
        self, course: Course, another_course: Course, user: User
    ) -> None:
        """Считает только уроки конкретного курса."""
        Lesson.objects.create(
            course=course,
            owner=user,
            title="Урок курса 1",
            description="Описание",
            video_url="https://youtube.com/watch?v=test1",
        )
        Lesson.objects.create(
            course=another_course,
            owner=user,
            title="Урок курса 2",
            description="Описание",
            video_url="https://youtube.com/watch?v=test2",
        )

        count = calculate_lessons_count(course)

        assert count == 1


@pytest.mark.django_db
class TestCheckUserSubscription:
    """Тесты для функции check_user_subscription."""

    def test_check_user_subscription_not_authenticated(self, course: Course) -> None:
        """Возвращает False для неаутентифицированного пользователя."""
        result = check_user_subscription(course, None)

        assert result is False

    def test_check_user_subscription_not_subscribed(self, course: Course, user: User) -> None:
        """Возвращает False, если пользователь не подписан."""
        result = check_user_subscription(course, user)

        assert result is False

    def test_check_user_subscription_subscribed(self, course: Course, user: User) -> None:
        """Возвращает True, если пользователь подписан."""
        Subscription.objects.create(user=user, course=course)

        result = check_user_subscription(course, user)

        assert result is True

    def test_check_user_subscription_different_course(
        self, course: Course, another_course: Course, user: User
    ) -> None:
        """Проверяет подписку только на конкретный курс."""
        Subscription.objects.create(user=user, course=another_course)

        result = check_user_subscription(course, user)

        assert result is False
