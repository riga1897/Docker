"""
Тесты для management команд приложения users.
"""

from io import StringIO
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError

from users.models import User


@pytest.mark.django_db
class TestCreateSuperuserCustomCommand:
    """Тесты для команды create_superuser_custom."""

    def test_create_superuser_with_params(self) -> None:
        """Создание суперпользователя через параметры командной строки."""
        out = StringIO()
        call_command(
            "create_superuser_custom",
            email="admin@example.com",
            password="admin123",
            stdout=out,
        )

        assert User.objects.filter(email="admin@example.com").exists()
        user = User.objects.get(email="admin@example.com")
        assert user.is_superuser
        assert user.is_staff
        assert user.check_password("admin123")
        assert "Суперпользователь успешно создан" in out.getvalue()

    def test_create_superuser_interactive(self) -> None:
        """Создание суперпользователя в интерактивном режиме."""
        out = StringIO()
        with patch("builtins.input", return_value="interactive@example.com"):
            with patch("getpass.getpass", side_effect=["password123", "password123"]):
                call_command("create_superuser_custom", stdout=out)

        assert User.objects.filter(email="interactive@example.com").exists()
        user = User.objects.get(email="interactive@example.com")
        assert user.is_superuser
        assert user.check_password("password123")

    def test_create_superuser_empty_email_param(self) -> None:
        """Ошибка при пустом email в интерактивном режиме."""
        with patch("builtins.input", return_value=""):
            with pytest.raises(CommandError, match="Email не может быть пустым"):
                call_command("create_superuser_custom")

    def test_create_superuser_empty_password_param(self) -> None:
        """Ошибка при пустом пароле в интерактивном режиме."""
        with patch("builtins.input", return_value="test@example.com"):
            with patch("getpass.getpass", return_value=""):
                with pytest.raises(CommandError, match="Пароль не может быть пустым"):
                    call_command("create_superuser_custom")

    def test_create_superuser_password_mismatch(self) -> None:
        """Ошибка при несовпадении паролей."""
        with patch("builtins.input", return_value="test@example.com"):
            with patch("getpass.getpass", side_effect=["password1", "password2"]):
                with pytest.raises(CommandError, match="Пароли не совпадают"):
                    call_command("create_superuser_custom")

    def test_create_superuser_invalid_email(self) -> None:
        """Ошибка при невалидном email."""
        with pytest.raises(CommandError, match="Невалидный email адрес"):
            call_command(
                "create_superuser_custom",
                email="invalid-email",
                password="password123",
            )

    def test_create_superuser_duplicate_email(self) -> None:
        """Ошибка при создании пользователя с существующим email."""
        User.objects.create_user(email="existing@example.com", password="password")

        with pytest.raises(CommandError, match="уже существует"):
            call_command(
                "create_superuser_custom",
                email="existing@example.com",
                password="password123",
            )


@pytest.mark.django_db
class TestInitGroupsCommand:
    """Тесты для команды init_groups."""

    def test_init_groups_creates_moderators(self) -> None:
        """Команда создаёт группу Модераторы."""
        out = StringIO()
        call_command("init_groups", stdout=out)

        assert Group.objects.filter(name="Модераторы").exists()
        assert "успешно создана" in out.getvalue()

    def test_init_groups_idempotent(self) -> None:
        """Команда идемпотентная - можно запускать повторно."""
        Group.objects.create(name="Модераторы")

        out = StringIO()
        call_command("init_groups", stdout=out)

        assert Group.objects.filter(name="Модераторы").count() == 1
        assert "уже существует" in out.getvalue()

    def test_init_groups_removes_treasurers(self) -> None:
        """Команда удаляет группу Казначеи."""
        Group.objects.create(name="Казначеи")

        out = StringIO()
        call_command("init_groups", stdout=out)

        assert not Group.objects.filter(name="Казначеи").exists()
        assert "успешно удалена" in out.getvalue()

    def test_init_groups_treasurers_not_found(self) -> None:
        """Команда корректно работает если группа Казначеи не существует."""
        out = StringIO()
        call_command("init_groups", stdout=out)

        assert "не найдена" in out.getvalue()


@pytest.mark.django_db
class TestCreateTestUsersCommand:
    """Тесты для команды create_test_users."""

    def test_create_test_users(self) -> None:
        """Команда создаёт модератора и обычного пользователя."""
        Group.objects.create(name="Модераторы")

        out = StringIO()
        call_command("create_test_users", stdout=out)

        assert User.objects.filter(email="moderator@example.com").exists()
        assert User.objects.filter(email="user@example.com").exists()

        moderator = User.objects.get(email="moderator@example.com")
        user = User.objects.get(email="user@example.com")

        assert moderator.check_password("moderator123")
        assert user.check_password("user123")
        assert not moderator.is_superuser
        assert not user.is_superuser
        assert "завершено успешно" in out.getvalue()

    def test_create_test_users_adds_moderator_to_group(self) -> None:
        """Команда добавляет модератора в группу Модераторы."""
        moderators_group = Group.objects.create(name="Модераторы")

        call_command("create_test_users", stdout=StringIO())

        moderator = User.objects.get(email="moderator@example.com")
        assert moderators_group in moderator.groups.all()

    def test_create_test_users_idempotent(self) -> None:
        """Команда идемпотентная - можно запускать повторно."""
        Group.objects.create(name="Модераторы")
        call_command("create_test_users", stdout=StringIO())

        out = StringIO()
        call_command("create_test_users", stdout=out)

        assert User.objects.filter(email="moderator@example.com").count() == 1
        assert User.objects.filter(email="user@example.com").count() == 1
        assert "уже существует" in out.getvalue()

    def test_create_test_users_moderator_already_in_group(self) -> None:
        """Команда корректно работает если модератор уже в группе."""
        moderators_group = Group.objects.create(name="Модераторы")
        moderator = User.objects.create_user(email="moderator@example.com", password="old_password")
        moderator.groups.add(moderators_group)

        out = StringIO()
        call_command("create_test_users", stdout=out)

        assert "уже в группе" in out.getvalue()
