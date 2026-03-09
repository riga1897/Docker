"""Unit-тесты для сервисных функций Stripe."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from users.services import (
    check_stripe_payment_status,
    create_stripe_checkout_session,
    create_stripe_product_and_price,
    get_stripe_cancel_url,
    get_stripe_success_url,
)


@pytest.mark.django_db
class TestStripeProductAndPrice:
    """Тесты для create_stripe_product_and_price()."""

    @patch("stripe.Price.create")
    @patch("stripe.Product.create")
    def test_create_product_and_price_success(
        self, mock_product_create: MagicMock, mock_price_create: MagicMock
    ) -> None:
        """Успешное создание продукта и цены в Stripe."""
        # Arrange
        mock_product = MagicMock()
        mock_product.id = "prod_test123"
        mock_product_create.return_value = mock_product

        mock_price = MagicMock()
        mock_price.id = "price_test456"
        mock_price_create.return_value = mock_price

        # Act
        product_id, price_id = create_stripe_product_and_price("Test Course", Decimal("1000.00"))

        # Assert
        assert product_id == "prod_test123"
        assert price_id == "price_test456"
        mock_product_create.assert_called_once_with(name="Test Course")
        mock_price_create.assert_called_once_with(
            product="prod_test123",
            unit_amount=100000,  # 1000.00 * 100
            currency="rub",
        )

    @patch("stripe.Price.create")
    @patch("stripe.Product.create")
    def test_create_product_and_price_converts_to_cents(
        self, mock_product_create: MagicMock, mock_price_create: MagicMock
    ) -> None:
        """Проверка правильной конвертации суммы в копейки."""
        # Arrange
        mock_product = MagicMock()
        mock_product.id = "prod_test"
        mock_product_create.return_value = mock_product

        mock_price = MagicMock()
        mock_price.id = "price_test"
        mock_price_create.return_value = mock_price

        # Act
        create_stripe_product_and_price("Test", Decimal("123.45"))

        # Assert
        mock_price_create.assert_called_once()
        call_kwargs = mock_price_create.call_args[1]
        assert call_kwargs["unit_amount"] == 12345  # 123.45 * 100

    @patch("stripe.Product.create")
    def test_create_product_and_price_raises_on_exception(self, mock_product_create: MagicMock) -> None:
        """Передача исключения при ошибке создания продукта."""
        # Arrange
        mock_product_create.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(Exception, match="API Error"):
            create_stripe_product_and_price("Test", Decimal("100.00"))


@pytest.mark.django_db
class TestStripeCheckoutSession:
    """Тесты для create_stripe_checkout_session()."""

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session_success(self, mock_session_create: MagicMock) -> None:
        """Успешное создание платежной сессии."""
        # Arrange
        mock_session = MagicMock()
        mock_session.id = "cs_test_session123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_session123"
        mock_session_create.return_value = mock_session

        # Act
        session_id, payment_url = create_stripe_checkout_session(
            price_id="price_test",
            success_url="https://example.com/success/",
            cancel_url="https://example.com/cancel/",
        )

        # Assert
        assert session_id == "cs_test_session123"
        assert payment_url == "https://checkout.stripe.com/pay/cs_test_session123"
        mock_session_create.assert_called_once_with(
            payment_method_types=["card"],
            line_items=[{"price": "price_test", "quantity": 1}],
            mode="payment",
            success_url="https://example.com/success/",
            cancel_url="https://example.com/cancel/",
        )

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session_raises_without_url(self, mock_session_create: MagicMock) -> None:
        """Ошибка если Stripe не вернул URL платежной сессии."""
        # Arrange
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = None
        mock_session_create.return_value = mock_session

        # Act & Assert
        with pytest.raises(ValueError, match="Stripe не вернул URL платежной сессии"):
            create_stripe_checkout_session(
                price_id="price_test",
                success_url="https://example.com/success/",
                cancel_url="https://example.com/cancel/",
            )


@pytest.mark.django_db
class TestStripePaymentStatus:
    """Тесты для check_stripe_payment_status()."""

    @patch("stripe.checkout.Session.retrieve")
    def test_check_payment_status_paid(self, mock_session_retrieve: MagicMock) -> None:
        """Проверка статуса: платеж завершен (paid)."""
        # Arrange
        mock_session = MagicMock()
        mock_session.payment_status = "paid"
        mock_session_retrieve.return_value = mock_session

        # Act
        status = check_stripe_payment_status("cs_test_session")

        # Assert
        assert status == "paid"
        mock_session_retrieve.assert_called_once_with("cs_test_session")

    @patch("stripe.checkout.Session.retrieve")
    def test_check_payment_status_unpaid(self, mock_session_retrieve: MagicMock) -> None:
        """Проверка статуса: платеж не завершен (unpaid)."""
        # Arrange
        mock_session = MagicMock()
        mock_session.payment_status = "unpaid"
        mock_session.status = "open"
        mock_session_retrieve.return_value = mock_session

        # Act
        status = check_stripe_payment_status("cs_test_session")

        # Assert
        assert status == "unpaid"

    @patch("stripe.checkout.Session.retrieve")
    def test_check_payment_status_expired(self, mock_session_retrieve: MagicMock) -> None:
        """Проверка статуса: сессия истекла (expired)."""
        # Arrange
        mock_session = MagicMock()
        mock_session.payment_status = "unpaid"
        mock_session.status = "expired"
        mock_session_retrieve.return_value = mock_session

        # Act
        status = check_stripe_payment_status("cs_test_session")

        # Assert
        assert status == "expired"

    @patch("stripe.checkout.Session.retrieve")
    def test_check_payment_status_canceled(self, mock_session_retrieve: MagicMock) -> None:
        """Проверка статуса: платеж отменен (canceled)."""
        # Arrange
        mock_session = MagicMock()
        mock_session.payment_status = "canceled"
        mock_session_retrieve.return_value = mock_session

        # Act
        status = check_stripe_payment_status("cs_test_session")

        # Assert
        assert status == "canceled"


@pytest.mark.django_db
class TestStripeURLHelpers:
    """
    Тесты для вспомогательных функций генерации URL.

    Эти функции теперь используют build_url() из config.utils,
    которая опирается на settings.SITE_DOMAIN.
    """

    @override_settings(SITE_DOMAIN="localhost:5000")
    def test_get_success_url_localhost(self) -> None:
        """Генерация success URL для localhost."""
        url = get_stripe_success_url()
        assert url == "http://localhost:5000/api/payments/success/"

    @override_settings(SITE_DOMAIN="myapp-username.replit.dev")
    def test_get_success_url_replit(self) -> None:
        """Генерация success URL для Replit домена."""
        url = get_stripe_success_url()
        assert url == "https://myapp-username.replit.dev/api/payments/success/"

    @override_settings(SITE_DOMAIN="localhost:5000")
    def test_get_cancel_url_localhost(self) -> None:
        """Генерация cancel URL для localhost."""
        url = get_stripe_cancel_url()
        assert url == "http://localhost:5000/api/payments/cancel/"

    @override_settings(SITE_DOMAIN="myapp-username.replit.dev")
    def test_get_cancel_url_replit(self) -> None:
        """Генерация cancel URL для Replit домена."""
        url = get_stripe_cancel_url()
        assert url == "https://myapp-username.replit.dev/api/payments/cancel/"

    @override_settings(SITE_DOMAIN="localhost:8000")
    def test_get_success_url_default(self) -> None:
        """Генерация success URL с дефолтным доменом."""
        url = get_stripe_success_url()
        assert url == "http://localhost:8000/api/payments/success/"

    @override_settings(SITE_DOMAIN="localhost:8000")
    def test_get_cancel_url_default(self) -> None:
        """Генерация cancel URL с дефолтным доменом."""
        url = get_stripe_cancel_url()
        assert url == "http://localhost:8000/api/payments/cancel/"
