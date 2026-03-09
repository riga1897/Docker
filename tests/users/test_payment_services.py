"""
Тесты для сервисных функций платежей (users/services.py).

Проверка новых функций Service Layer:
- prepare_stripe_payment_data()
- refresh_payment_status()
"""

from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest

from lms.models import Course, Lesson
from users.models import Payment, User
from users.services import prepare_stripe_payment_data, refresh_payment_status


@pytest.mark.django_db
class TestPrepareStripePaymentData:
    """Тесты для prepare_stripe_payment_data()."""

    @patch("users.services.create_stripe_checkout_session")
    @patch("users.services.create_stripe_product_and_price")
    def test_prepare_stripe_payment_for_course(
        self,
        mock_create_product: Any,
        mock_create_session: Any,
    ) -> None:
        """Проверка подготовки Stripe данных для курса."""
        mock_create_product.return_value = ("prod_123", "price_456")
        mock_create_session.return_value = ("session_789", "https://stripe.com/pay")

        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Test Course",
            description="Test",
            owner=owner,
        )

        result = prepare_stripe_payment_data(
            amount=Decimal("1000.00"),
            course=course,
            lesson=None,
        )

        assert result["stripe_session_id"] == "session_789"
        assert result["payment_link"] == "https://stripe.com/pay"
        mock_create_product.assert_called_once_with("Курс: Test Course", Decimal("1000.00"))
        mock_create_session.assert_called_once()

    @patch("users.services.create_stripe_checkout_session")
    @patch("users.services.create_stripe_product_and_price")
    def test_prepare_stripe_payment_for_lesson(
        self,
        mock_create_product: Any,
        mock_create_session: Any,
    ) -> None:
        """Проверка подготовки Stripe данных для урока."""
        mock_create_product.return_value = ("prod_123", "price_456")
        mock_create_session.return_value = ("session_789", "https://stripe.com/pay")

        owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        course = Course.objects.create(
            title="Course",
            description="Desc",
            owner=owner,
        )
        lesson = Lesson.objects.create(
            title="Test Lesson",
            description="Test",
            course=course,
            owner=owner,
            video_url="https://www.youtube.com/watch?v=test",
        )

        result = prepare_stripe_payment_data(
            amount=Decimal("500.00"),
            course=None,
            lesson=lesson,
        )

        assert result["stripe_session_id"] == "session_789"
        assert result["payment_link"] == "https://stripe.com/pay"
        mock_create_product.assert_called_once_with("Урок: Test Lesson", Decimal("500.00"))

    @patch("users.services.create_stripe_checkout_session")
    @patch("users.services.create_stripe_product_and_price")
    def test_prepare_stripe_payment_without_course_or_lesson(
        self,
        mock_create_product: Any,
        mock_create_session: Any,
    ) -> None:
        """Проверка подготовки Stripe данных без курса и урока."""
        mock_create_product.return_value = ("prod_123", "price_456")
        mock_create_session.return_value = ("session_789", "https://stripe.com/pay")

        result = prepare_stripe_payment_data(
            amount=Decimal("100.00"),
            course=None,
            lesson=None,
        )

        assert result["stripe_session_id"] == "session_789"
        assert result["payment_link"] == "https://stripe.com/pay"
        mock_create_product.assert_called_once_with("Платёж", Decimal("100.00"))


@pytest.mark.django_db
class TestRefreshPaymentStatus:
    """Тесты для refresh_payment_status()."""

    @patch("users.services.check_stripe_payment_status")
    def test_refresh_payment_status_paid(
        self,
        mock_check_status: Any,
    ) -> None:
        """Проверка обновления статуса платежа: paid."""
        mock_check_status.return_value = "paid"

        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        payment = Payment.objects.create(
            owner=user,
            amount=Decimal("1000.00"),
            payment_method="stripe",
            stripe_session_id="session_123",
        )

        result = refresh_payment_status(payment.pk)  # type: ignore[arg-type]

        assert result["payment_status"] == "paid"
        assert result["message"] == "Платёж успешно завершён"
        mock_check_status.assert_called_once_with("session_123")

    @patch("users.services.check_stripe_payment_status")
    def test_refresh_payment_status_unpaid(
        self,
        mock_check_status: Any,
    ) -> None:
        """Проверка обновления статуса платежа: unpaid."""
        mock_check_status.return_value = "unpaid"

        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        payment = Payment.objects.create(
            owner=user,
            amount=Decimal("500.00"),
            payment_method="stripe",
            stripe_session_id="session_456",
        )

        result = refresh_payment_status(payment.pk)  # type: ignore[arg-type]

        assert result["payment_status"] == "unpaid"
        assert result["message"] == "Платёж ожидает оплаты"

    def test_refresh_payment_status_non_stripe_payment(self) -> None:
        """Проверка ошибки для не-Stripe платежа."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        payment = Payment.objects.create(
            owner=user,
            amount=Decimal("300.00"),
            payment_method="cash",
        )

        with pytest.raises(ValueError, match="Платёж не был создан через Stripe"):
            refresh_payment_status(payment.pk)  # type: ignore[arg-type]

    def test_refresh_payment_status_no_session_id(self) -> None:
        """Проверка ошибки для Stripe платежа без session_id."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        payment = Payment.objects.create(
            owner=user,
            amount=Decimal("200.00"),
            payment_method="stripe",
            stripe_session_id=None,
        )

        with pytest.raises(ValueError, match="Платёж не был создан через Stripe"):
            refresh_payment_status(payment.pk)  # type: ignore[arg-type]

    def test_refresh_payment_status_payment_not_found(self) -> None:
        """Проверка ошибки для несуществующего платежа."""
        with pytest.raises(Payment.DoesNotExist):
            refresh_payment_status(99999)
