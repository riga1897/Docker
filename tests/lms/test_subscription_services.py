"""
Тесты для сервисных функций подписок (lms/services.py).

Проверка новых функций Service Layer:
- subscribe_user_to_course()
- unsubscribe_user_from_course()
- toggle_subscription()
"""

import pytest

from lms.models import Course, Subscription
from lms.services import (
    subscribe_user_to_course,
    toggle_subscription,
    unsubscribe_user_from_course,
)
from users.models import User


@pytest.mark.django_db
class TestSubscribeUserToCourse:
    """Тесты для subscribe_user_to_course()."""

    def test_subscribe_new_subscription(self) -> None:
        """Проверка создания новой подписки."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=owner,
        )

        subscription = subscribe_user_to_course(user, course)

        assert subscription.user == user
        assert subscription.course == course
        assert Subscription.objects.filter(user=user, course=course).exists()

    def test_subscribe_idempotent(self) -> None:
        """Проверка идемпотентности - повторная подписка не создаёт дубликат."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=owner,
        )

        subscription1 = subscribe_user_to_course(user, course)
        subscription2 = subscribe_user_to_course(user, course)

        assert subscription1.pk == subscription2.pk
        assert Subscription.objects.filter(user=user, course=course).count() == 1


@pytest.mark.django_db
class TestUnsubscribeUserFromCourse:
    """Тесты для unsubscribe_user_from_course()."""

    def test_unsubscribe_existing_subscription(self) -> None:
        """Проверка удаления существующей подписки."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=owner,
        )
        Subscription.objects.create(user=user, course=course)

        result = unsubscribe_user_from_course(user, course)

        assert result is True
        assert not Subscription.objects.filter(user=user, course=course).exists()

    def test_unsubscribe_no_subscription(self) -> None:
        """Проверка идемпотентности - отписка без подписки возвращает False."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=owner,
        )

        result = unsubscribe_user_from_course(user, course)

        assert result is False


@pytest.mark.django_db
class TestToggleSubscription:
    """Тесты для toggle_subscription()."""

    def test_toggle_creates_subscription_if_not_exists(self) -> None:
        """Проверка создания подписки при toggle без существующей подписки."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=owner,
        )

        is_subscribed, message = toggle_subscription(user, course)

        assert is_subscribed is True
        assert message == "подписка добавлена"
        assert Subscription.objects.filter(user=user, course=course).exists()

    def test_toggle_removes_subscription_if_exists(self) -> None:
        """Проверка удаления подписки при toggle с существующей подпиской."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=owner,
        )
        Subscription.objects.create(user=user, course=course)

        is_subscribed, message = toggle_subscription(user, course)

        assert is_subscribed is False
        assert message == "подписка удалена"
        assert not Subscription.objects.filter(user=user, course=course).exists()

    def test_toggle_twice_returns_to_original_state(self) -> None:
        """Проверка двойного toggle возвращает в исходное состояние."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=owner,
        )

        # Первый toggle - создаёт подписку
        is_subscribed1, message1 = toggle_subscription(user, course)
        assert is_subscribed1 is True
        assert message1 == "подписка добавлена"

        # Второй toggle - удаляет подписку
        is_subscribed2, message2 = toggle_subscription(user, course)
        assert is_subscribed2 is False
        assert message2 == "подписка удалена"

        # Состояние вернулось к исходному (без подписки)
        assert not Subscription.objects.filter(user=user, course=course).exists()
