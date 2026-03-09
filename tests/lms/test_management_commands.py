"""
Тесты для management команд приложения lms.
"""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from lms.models import Course, Lesson
from users.models import Payment, User


@pytest.mark.django_db
class TestDelAllCommand:
    """Тесты для команды del_all."""

    @pytest.fixture
    def sample_data(self) -> tuple[User, Course, Lesson, Payment]:
        """Создаёт тестовые данные для проверки удаления."""
        user = User.objects.create_user(email="test@example.com", password="password")
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=user,
        )
        lesson = Lesson.objects.create(
            title="Test Lesson",
            description="Test Description",
            video_url="https://www.youtube.com/watch?v=test",
            course=course,
            owner=user,
        )
        payment = Payment.objects.create(
            owner=user,
            course=course,
            amount=1000,
            payment_method="cash",
        )
        return user, course, lesson, payment

    def test_del_all_with_force_without_users(self, sample_data: tuple) -> None:
        """Команда удаляет курсы, уроки и платежи, но не пользователей (с --force)."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        call_command("del_all", force=True, stdout=out)

        assert not Course.objects.exists()
        assert not Lesson.objects.exists()
        assert not Payment.objects.exists()
        assert User.objects.exists()
        assert User.objects.get(pk=user.pk) == user

        output = out.getvalue()
        assert "Удалено курсов: 1" in output
        assert "Удалено уроков: 1" in output
        assert "Удалено платежей: 1" in output
        assert "завершена успешно" in output

    def test_del_all_with_force_with_users(self, sample_data: tuple) -> None:
        """Команда удаляет всё включая пользователей (с --force --include-users)."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        call_command("del_all", force=True, include_users=True, stdout=out)

        assert not Course.objects.exists()
        assert not Lesson.objects.exists()
        assert not Payment.objects.exists()
        assert not User.objects.exists()

        output = out.getvalue()
        assert "Удалено пользователей: 1" in output
        assert "Доступ к админке потерян" in output

    def test_del_all_interactive_yes(self, sample_data: tuple) -> None:
        """Команда запрашивает подтверждение и удаляет при ответе 'yes'."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        with patch("builtins.input", return_value="yes"):
            call_command("del_all", stdout=out)

        assert not Course.objects.exists()
        assert not Lesson.objects.exists()
        assert not Payment.objects.exists()
        assert User.objects.exists()

    def test_del_all_interactive_no(self, sample_data: tuple) -> None:
        """Команда отменяет операцию при ответе 'no'."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        with patch("builtins.input", return_value="no"):
            call_command("del_all", stdout=out)

        assert Course.objects.exists()
        assert Lesson.objects.exists()
        assert Payment.objects.exists()
        assert User.objects.exists()
        assert "отменена" in out.getvalue()

    def test_del_all_interactive_да(self, sample_data: tuple) -> None:
        """Команда принимает 'да' как подтверждение."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        with patch("builtins.input", return_value="да"):
            call_command("del_all", stdout=out)

        assert not Course.objects.exists()

    def test_del_all_with_empty_database(self) -> None:
        """Команда корректно работает с пустой базой данных."""
        out = StringIO()
        call_command("del_all", force=True, stdout=out)

        output = out.getvalue()
        assert "Удалено курсов: 0" in output
        assert "Удалено уроков: 0" in output
        assert "Удалено платежей: 0" in output

    def test_del_all_shows_counts_before_deletion(self, sample_data: tuple) -> None:
        """Команда показывает количество записей перед удалением."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        with patch("builtins.input", return_value="no"):
            call_command("del_all", stdout=out)

        output = out.getvalue()
        assert "Платежей: 1" in output
        assert "Уроков: 1" in output
        assert "Курсов: 1" in output
        assert "НЕ будут затронуты" in output

    def test_del_all_shows_users_warning_when_include_users(self, sample_data: tuple) -> None:
        """Команда показывает предупреждение при удалении пользователей."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        with patch("builtins.input", return_value="no"):
            call_command("del_all", include_users=True, stdout=out)

        output = out.getvalue()
        assert "Пользователей: 1" in output
        assert "включая админов" in output

    def test_del_all_multiple_objects(self) -> None:
        """Команда корректно удаляет несколько объектов."""
        user1 = User.objects.create_user(email="user1@example.com", password="password")
        user2 = User.objects.create_user(email="user2@example.com", password="password")

        course1 = Course.objects.create(title="Course 1", description="Desc 1", owner=user1)
        course2 = Course.objects.create(title="Course 2", description="Desc 2", owner=user2)

        Lesson.objects.create(
            title="Lesson 1",
            description="Desc 1",
            video_url="https://www.youtube.com/watch?v=test1",
            course=course1,
            owner=user1,
        )
        lesson2 = Lesson.objects.create(
            title="Lesson 2",
            description="Desc 2",
            video_url="https://www.youtube.com/watch?v=test2",
            course=course2,
            owner=user2,
        )

        Payment.objects.create(owner=user1, course=course1, amount=1000, payment_method="cash")
        Payment.objects.create(owner=user2, lesson=lesson2, amount=2000, payment_method="transfer")

        out = StringIO()
        call_command("del_all", force=True, stdout=out)

        assert Course.objects.count() == 0
        assert Lesson.objects.count() == 0
        assert Payment.objects.count() == 0
        assert User.objects.count() == 2

        output = out.getvalue()
        assert "Удалено курсов: 2" in output
        assert "Удалено уроков: 2" in output
        assert "Удалено платежей: 2" in output

    def test_del_all_reset_sequence_for_non_postgresql(self, sample_data: tuple) -> None:
        """Команда корректно обрабатывает reset_sequence для не-PostgreSQL БД."""
        user, course, lesson, payment = sample_data

        out = StringIO()
        with patch("lms.management.commands.del_all.connection") as mock_connection:
            mock_connection.vendor = "sqlite"
            call_command("del_all", force=True, stdout=out)

        output = out.getvalue()
        assert "Сброс счетчика" in output
        assert "пропущен" in output
        assert "sqlite" in output
