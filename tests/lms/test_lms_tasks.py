"""
Тесты для lms/tasks.py - Celery задачи для email рассылки.

Проверяет, что Celery tasks корректно вызывают service functions.
"""

from unittest.mock import MagicMock, patch

import pytest

from lms.tasks import send_course_update_notification


@pytest.mark.django_db
class TestSendCourseUpdateNotificationTask:
    """Тесты для Celery задачи send_course_update_notification."""

    @patch("lms.services.send_course_update_email")
    def test_send_course_update_notification_calls_service(self, mock_send_email: MagicMock) -> None:
        """Задача вызывает сервисную функцию send_course_update_email."""
        mock_send_email.return_value = 5
        course_id = 123

        result = send_course_update_notification(course_id)

        mock_send_email.assert_called_once_with(course_id)
        assert result == 5

    @patch("lms.services.send_course_update_email")
    def test_send_course_update_notification_returns_count(self, mock_send_email: MagicMock) -> None:
        """Задача возвращает количество отправленных писем."""
        mock_send_email.return_value = 3

        result = send_course_update_notification(999)

        assert result == 3
