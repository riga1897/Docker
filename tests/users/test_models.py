"""Тесты для моделей приложения Users."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from lms.models import Course, Lesson
from users.models import Payment, User


@pytest.mark.django_db
class TestPaymentModel:
    """Тесты для модели Payment."""

    def test_payment_creation_for_course(self) -> None:
        """Тест создания платежа за курс."""
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        course = Course.objects.create(title="Python Course", description="Learn Python", owner=user)

        payment = Payment.objects.create(owner=user, course=course, amount=Decimal("1500.00"), payment_method="cash")

        assert payment.id is not None  # type: ignore[attr-defined]
        assert payment.owner == user
        assert payment.course == course
        assert payment.lesson is None
        assert payment.amount == Decimal("1500.00")
        assert payment.payment_method == "cash"
        assert payment.payment_date is not None
        assert payment.created_at is not None
        assert payment.updated_at is not None

    def test_payment_creation_for_lesson(self) -> None:
        """Тест создания платежа за отдельный урок."""
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        course = Course.objects.create(title="Django Course", description="Learn Django", owner=user)
        lesson = Lesson.objects.create(
            course=course,
            title="Django Models",
            description="Learn models",
            video_url="https://youtube.com/test",
            owner=user,
        )

        payment = Payment.objects.create(
            owner=user, lesson=lesson, amount=Decimal("500.50"), payment_method="transfer"
        )

        assert payment.id is not None  # type: ignore[attr-defined]
        assert payment.owner == user
        assert payment.course is None
        assert payment.lesson == lesson
        assert payment.amount == Decimal("500.50")
        assert payment.payment_method == "transfer"

    def test_payment_str_method(self) -> None:
        """Тест строкового представления платежа."""
        user = User.objects.create_user(email="john@example.com", password="testpass")
        course = Course.objects.create(title="FastAPI Course", description="Learn FastAPI", owner=user)

        payment = Payment.objects.create(owner=user, course=course, amount=Decimal("2000.00"), payment_method="cash")

        assert "john@example.com" in str(payment)
        assert "FastAPI Course" in str(payment)
        assert "2000" in str(payment)

    def test_payment_validation_both_empty(self) -> None:
        """Тест валидации: оба поля course и lesson пустые (должна быть ошибка)."""
        user = User.objects.create_user(email="test@example.com", password="testpass")

        payment = Payment(owner=user, course=None, lesson=None, amount=Decimal("1000.00"), payment_method="cash")

        with pytest.raises(ValidationError) as exc_info:
            payment.clean()

        assert "Должен быть указан либо курс, либо урок для оплаты" in str(exc_info.value)

    def test_payment_validation_course_only_valid(self) -> None:
        """Тест валидации: только курс указан (валидно)."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Test Course", description="Test", owner=user)

        payment = Payment(owner=user, course=course, lesson=None, amount=Decimal("1000.00"), payment_method="transfer")

        payment.clean()

    def test_payment_validation_lesson_only_valid(self) -> None:
        """Тест валидации: только урок указан (валидно)."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Test Course", description="Test", owner=user)
        lesson = Lesson.objects.create(
            course=course, title="Test Lesson", description="Test", video_url="https://youtube.com/test", owner=user
        )

        payment = Payment(owner=user, course=None, lesson=lesson, amount=Decimal("500.00"), payment_method="cash")

        payment.clean()

    def test_payment_both_course_and_lesson(self) -> None:
        """Тест создания платежа с указанием и курса, и урока (допустимо)."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Test Course", description="Test", owner=user)
        lesson = Lesson.objects.create(
            course=course, title="Test Lesson", description="Test", video_url="https://youtube.com/test", owner=user
        )

        payment = Payment.objects.create(
            owner=user, course=course, lesson=lesson, amount=Decimal("2000.00"), payment_method="transfer"
        )

        assert payment.id is not None  # type: ignore[attr-defined]
        assert payment.course == course
        assert payment.lesson == lesson

    def test_payment_user_relation(self) -> None:
        """Тест связи платежа с пользователем."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Course 1", description="Test", owner=user)

        payment1 = Payment.objects.create(owner=user, course=course, amount=Decimal("1000.00"), payment_method="cash")
        payment2 = Payment.objects.create(
            owner=user, course=course, amount=Decimal("2000.00"), payment_method="transfer"
        )

        assert user.payments.count() == 2  # type: ignore[attr-defined]
        assert list(user.payments.all()) == [payment2, payment1]  # type: ignore[attr-defined]

    def test_payment_course_cascade_delete(self) -> None:
        """Тест каскадного удаления платежей при удалении курса."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Temporary Course", description="Will be deleted", owner=user)

        payment = Payment.objects.create(owner=user, course=course, amount=Decimal("1500.00"), payment_method="cash")

        payment_id = payment.id  # type: ignore[attr-defined]

        course.delete()

        assert not Payment.objects.filter(id=payment_id).exists()

    def test_payment_user_cascade_delete(self) -> None:
        """Тест каскадного удаления платежей при удалении пользователя."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Test Course", description="Test", owner=user)

        payment = Payment.objects.create(owner=user, course=course, amount=Decimal("1500.00"), payment_method="cash")

        payment_id = payment.id  # type: ignore[attr-defined]

        user.delete()

        assert not Payment.objects.filter(id=payment_id).exists()

    def test_payment_method_choices(self) -> None:
        """Тест выбора способа оплаты из доступных вариантов."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Test Course", description="Test", owner=user)

        payment_cash = Payment.objects.create(
            owner=user, course=course, amount=Decimal("1000.00"), payment_method="cash"
        )
        payment_transfer = Payment.objects.create(
            owner=user, course=course, amount=Decimal("2000.00"), payment_method="transfer"
        )

        assert payment_cash.payment_method == "cash"
        assert payment_transfer.payment_method == "transfer"

    def test_payment_has_timestamps(self) -> None:
        """Тест наличия временных меток из BaseModel."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        course = Course.objects.create(title="Test Course", description="Test", owner=user)

        payment = Payment.objects.create(owner=user, course=course, amount=Decimal("1000.00"), payment_method="cash")

        assert hasattr(payment, "created_at")
        assert hasattr(payment, "updated_at")
        assert payment.created_at is not None
        assert payment.updated_at is not None

    def test_payment_str_method_with_lesson(self) -> None:
        """Тест строкового представления платежа за урок."""
        user = User.objects.create_user(email="alice@example.com", password="testpass")
        course = Course.objects.create(title="Course", description="Test", owner=user)
        lesson = Lesson.objects.create(
            course=course,
            title="Advanced Lesson",
            description="Test",
            video_url="https://youtube.com/test",
            owner=user,
        )

        payment = Payment.objects.create(
            owner=user, lesson=lesson, amount=Decimal("750.00"), payment_method="transfer"
        )

        payment_str = str(payment)
        assert "alice@example.com" in payment_str
        assert "Advanced Lesson" in payment_str
        assert "750" in payment_str

    def test_payment_str_method_no_course_no_lesson(self) -> None:
        """Тест строкового представления платежа без курса и урока."""
        user = User.objects.create_user(email="bob@example.com", password="testpass")

        payment = Payment(owner=user, course=None, lesson=None, amount=Decimal("100.00"), payment_method="cash")

        payment_str = str(payment)
        assert "bob@example.com" in payment_str
        assert "Неизвестно" in payment_str
        assert "100" in payment_str


@pytest.mark.django_db
class TestUserManager:
    """Тесты для UserManager."""

    def test_create_user_without_email(self) -> None:
        """Тест создания пользователя без email (должна быть ошибка)."""
        with pytest.raises(ValueError) as exc_info:
            User.objects.create_user(email="", password="testpass")

        assert "Email обязателен" in str(exc_info.value)

    def test_create_superuser_without_is_staff(self) -> None:
        """Тест создания суперпользователя с is_staff=False (должна быть ошибка)."""
        with pytest.raises(ValueError) as exc_info:
            User.objects.create_superuser(email="admin@test.com", password="testpass", is_staff=False)

        assert "Суперпользователь должен иметь is_staff=True" in str(exc_info.value)

    def test_create_superuser_without_is_superuser(self) -> None:
        """Тест создания суперпользователя с is_superuser=False (должна быть ошибка)."""
        with pytest.raises(ValueError) as exc_info:
            User.objects.create_superuser(email="admin@test.com", password="testpass", is_superuser=False)

        assert "Суперпользователь должен иметь is_superuser=True" in str(exc_info.value)

    def test_create_user_success(self) -> None:
        """Тест успешного создания пользователя."""
        user = User.objects.create_user(email="newuser@test.com", password="securepass")

        assert user.email == "newuser@test.com"
        assert user.check_password("securepass")
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser_success(self) -> None:
        """Тест успешного создания суперпользователя."""
        superuser = User.objects.create_superuser(email="superadmin@test.com", password="adminpass")

        assert superuser.email == "superadmin@test.com"
        assert superuser.check_password("adminpass")
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
