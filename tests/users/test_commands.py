"""
Тесты для management commands приложения users.
"""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from users.models import User


@pytest.mark.django_db
class TestCreateSuperuserCustomCommand:
    """Тесты для команды create_superuser_custom."""

    def test_create_superuser_with_arguments(self) -> None:
        """Тест создания суперпользователя с аргументами командной строки."""
        out = StringIO()
        call_command(
            "create_superuser_custom",
            email="test_admin@example.com",
            password="testpass123",
            stdout=out,
        )

        user = User.objects.get(email="test_admin@example.com")
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.check_password("testpass123") is True
        assert "Суперпользователь успешно создан" in out.getvalue()

    def test_create_superuser_existing_user(self) -> None:
        """Тест обработки ошибки при попытке создать существующего пользователя."""
        User.objects.create_superuser(email="existing@example.com", password="password123")

        with pytest.raises(CommandError) as exc_info:
            call_command(
                "create_superuser_custom",
                email="existing@example.com",
                password="newpass123",
            )

        assert "Пользователь с email existing@example.com уже существует" in str(exc_info.value)

    def test_create_superuser_invalid_email(self) -> None:
        """Тест обработки ошибки при невалидном email."""
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "create_superuser_custom",
                email="invalid-email",
                password="testpass123",
            )

        assert "Невалидный email адрес" in str(exc_info.value)

    @patch("users.management.commands.create_superuser_custom.getpass.getpass")
    @patch("users.management.commands.create_superuser_custom.input")
    def test_create_superuser_interactive_mode(self, mock_input: object, mock_getpass: object) -> None:
        """Тест создания суперпользователя в интерактивном режиме."""
        mock_input.return_value = "interactive@example.com"  # type: ignore[attr-defined]
        mock_getpass.side_effect = ["password123", "password123"]  # type: ignore[attr-defined]

        out = StringIO()
        call_command("create_superuser_custom", stdout=out)

        user = User.objects.get(email="interactive@example.com")
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.check_password("password123") is True
        assert "Суперпользователь успешно создан" in out.getvalue()

    @patch("users.management.commands.create_superuser_custom.getpass.getpass")
    @patch("users.management.commands.create_superuser_custom.input")
    def test_create_superuser_interactive_password_mismatch(self, mock_input: object, mock_getpass: object) -> None:
        """Тест обработки несовпадения паролей в интерактивном режиме."""
        mock_input.return_value = "test@example.com"  # type: ignore[attr-defined]
        mock_getpass.side_effect = ["password123", "different"]  # type: ignore[attr-defined]

        with pytest.raises(CommandError) as exc_info:
            call_command("create_superuser_custom")

        assert "Пароли не совпадают" in str(exc_info.value)

    @patch("users.management.commands.create_superuser_custom.input")
    def test_create_superuser_interactive_empty_email(self, mock_input: object) -> None:
        """Тест обработки пустого email в интерактивном режиме."""
        mock_input.return_value = "  "  # type: ignore[attr-defined]

        with pytest.raises(CommandError) as exc_info:
            call_command("create_superuser_custom")

        assert "Email не может быть пустым" in str(exc_info.value)

    @patch("users.management.commands.create_superuser_custom.getpass.getpass")
    @patch("users.management.commands.create_superuser_custom.input")
    def test_create_superuser_interactive_empty_password(self, mock_input: object, mock_getpass: object) -> None:
        """Тест обработки пустого пароля в интерактивном режиме."""
        mock_input.return_value = "test@example.com"  # type: ignore[attr-defined]
        mock_getpass.return_value = ""  # type: ignore[attr-defined]

        with pytest.raises(CommandError) as exc_info:
            call_command("create_superuser_custom")

        assert "Пароль не может быть пустым" in str(exc_info.value)
