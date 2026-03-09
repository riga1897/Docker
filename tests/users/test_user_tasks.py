"""
Тесты для users/tasks.py - Celery задачи для блокировки пользователей.

Проверяет, что Celery tasks корректно вызывают service functions.
"""

from unittest.mock import MagicMock, patch

import pytest

from users.tasks import block_inactive_users_task


@pytest.mark.django_db
class TestBlockInactiveUsersTask:
    """Тесты для Celery задачи block_inactive_users_task."""

    @patch("users.services.block_inactive_users")
    def test_block_inactive_users_task_calls_service(self, mock_block_users: MagicMock) -> None:
        """Задача вызывает сервисную функцию block_inactive_users."""
        mock_block_users.return_value = 10

        result = block_inactive_users_task()

        mock_block_users.assert_called_once_with(30)
        assert result == 10

    @patch("users.services.block_inactive_users")
    def test_block_inactive_users_task_custom_days(self, mock_block_users: MagicMock) -> None:
        """Задача принимает кастомное количество дней."""
        mock_block_users.return_value = 5

        result = block_inactive_users_task(days=15)

        mock_block_users.assert_called_once_with(15)
        assert result == 5

    @patch("users.services.block_inactive_users")
    def test_block_inactive_users_task_returns_count(self, mock_block_users: MagicMock) -> None:
        """Задача возвращает количество заблокированных пользователей."""
        mock_block_users.return_value = 7

        result = block_inactive_users_task()

        assert result == 7
