"""
Тесты для users/services.py - функции блокировки неактивных пользователей.

Покрывает новые функции из users/services.py:
- get_inactive_users
- block_inactive_users
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from users.models import User
from users.services import block_inactive_users, get_inactive_users


@pytest.mark.django_db
class TestGetInactiveUsers:
    """Тесты для функции get_inactive_users."""

    def test_get_inactive_users_no_inactive(self, user: User) -> None:
        """Возвращает пустой QuerySet, если все пользователи активны."""
        user.last_login = timezone.now() - timedelta(days=15)
        user.save()

        inactive_users = get_inactive_users(days=30)

        assert inactive_users.count() == 0

    def test_get_inactive_users_one_inactive(self, user: User) -> None:
        """Возвращает пользователей неактивных более 30 дней."""
        user.last_login = timezone.now() - timedelta(days=31)
        user.save()

        inactive_users = get_inactive_users(days=30)

        assert inactive_users.count() == 1
        assert user in inactive_users

    def test_get_inactive_users_multiple_inactive(self, user: User, another_user: User) -> None:
        """Возвращает всех неактивных пользователей."""
        user.last_login = timezone.now() - timedelta(days=40)
        user.save()

        another_user.last_login = timezone.now() - timedelta(days=50)
        another_user.save()

        inactive_users = get_inactive_users(days=30)

        assert inactive_users.count() == 2
        assert user in inactive_users
        assert another_user in inactive_users

    def test_get_inactive_users_custom_days(self, user: User) -> None:
        """Работает с кастомным количеством дней."""
        user.last_login = timezone.now() - timedelta(days=8)
        user.save()

        inactive_users = get_inactive_users(days=7)

        assert inactive_users.count() == 1

    def test_get_inactive_users_excludes_already_inactive(self, user: User) -> None:
        """Не возвращает уже заблокированных пользователей."""
        user.last_login = timezone.now() - timedelta(days=40)
        user.is_active = False
        user.save()

        inactive_users = get_inactive_users(days=30)

        assert inactive_users.count() == 0

    def test_get_inactive_users_exact_boundary(self, user: User) -> None:
        """Возвращает пользователей на границе."""
        user.last_login = timezone.now() - timedelta(days=30, seconds=1)
        user.save()

        inactive_users = get_inactive_users(days=30)

        assert inactive_users.count() == 1


@pytest.mark.django_db
class TestBlockInactiveUsers:
    """Тесты для функции block_inactive_users."""

    def test_block_inactive_users_no_inactive(self, user: User) -> None:
        """Возвращает 0, если нет неактивных пользователей."""
        user.last_login = timezone.now() - timedelta(days=15)
        user.save()

        blocked_count = block_inactive_users(days=30)

        assert blocked_count == 0
        user.refresh_from_db()
        assert user.is_active is True

    def test_block_inactive_users_one_user(self, user: User) -> None:
        """Блокирует одного неактивного пользователя."""
        user.last_login = timezone.now() - timedelta(days=35)
        user.save()

        blocked_count = block_inactive_users(days=30)

        assert blocked_count == 1
        user.refresh_from_db()
        assert user.is_active is False

    def test_block_inactive_users_multiple_users(self, user: User, another_user: User) -> None:
        """Блокирует всех неактивных пользователей."""
        user.last_login = timezone.now() - timedelta(days=40)
        user.save()

        another_user.last_login = timezone.now() - timedelta(days=50)
        another_user.save()

        blocked_count = block_inactive_users(days=30)

        assert blocked_count == 2

        user.refresh_from_db()
        another_user.refresh_from_db()

        assert user.is_active is False
        assert another_user.is_active is False

    def test_block_inactive_users_custom_days(self, user: User) -> None:
        """Работает с кастомным количеством дней."""
        user.last_login = timezone.now() - timedelta(days=10)
        user.save()

        blocked_count = block_inactive_users(days=7)

        assert blocked_count == 1

        user.refresh_from_db()
        assert user.is_active is False

    def test_block_inactive_users_does_not_affect_active_users(self, user: User, another_user: User) -> None:
        """Не блокирует активных пользователей."""
        user.last_login = timezone.now() - timedelta(days=40)
        user.save()

        another_user.last_login = timezone.now() - timedelta(days=10)
        another_user.save()

        blocked_count = block_inactive_users(days=30)

        assert blocked_count == 1

        another_user.refresh_from_db()
        assert another_user.is_active is True
