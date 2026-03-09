"""
Тесты для JWT авторизации.

Тестируем:
- Регистрацию пользователей (RegisterView)
- Получение токенов (TokenObtainPairView)
- Обновление токенов (TokenRefreshView)
- Проверку токенов (TokenVerifyView)
- Защиту endpoints (требуется авторизация)
"""

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture
def api_client() -> APIClient:
    """API клиент для тестов."""
    return APIClient()


@pytest.fixture
def sample_user() -> User:
    """Создать тестового пользователя."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.mark.django_db
class TestRegisterView:
    """Тесты для регистрации пользователей."""

    def test_register_new_user_success(self, api_client: APIClient) -> None:
        """Успешная регистрация нового пользователя."""
        url = reverse("users:register")
        data: dict[str, Any] = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "newpass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() == 1
        user = User.objects.first()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.check_password("newpass123")
        assert "password" not in response.data
        assert "password_confirm" not in response.data

    def test_register_password_mismatch(self, api_client: APIClient) -> None:
        """Ошибка при несовпадении паролей."""
        url = reverse("users:register")
        data: dict[str, str] = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "differentpass",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data
        assert User.objects.count() == 0

    def test_register_duplicate_email(self, api_client: APIClient, sample_user: User) -> None:
        """Ошибка при регистрации с существующим email."""
        url = reverse("users:register")
        data: dict[str, str] = {
            "email": sample_user.email,
            "password": "newpass123",
            "password_confirm": "newpass123",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert User.objects.count() == 1

    def test_register_missing_required_fields(self, api_client: APIClient) -> None:
        """Ошибка при отсутствии обязательных полей."""
        url = reverse("users:register")
        data: dict[str, str] = {
            "email": "newuser@example.com",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data
        assert User.objects.count() == 0


@pytest.mark.django_db
class TestTokenObtainPair:
    """Тесты для получения JWT токенов (login)."""

    def test_obtain_token_success(self, api_client: APIClient, sample_user: User) -> None:
        """Успешное получение токенов с правильными credentials."""
        url = reverse("token_obtain_pair")
        data: dict[str, str] = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert isinstance(response.data["access"], str)
        assert isinstance(response.data["refresh"], str)

    def test_obtain_token_wrong_password(self, api_client: APIClient, sample_user: User) -> None:
        """Ошибка при неправильном пароле."""
        url = reverse("token_obtain_pair")
        data: dict[str, str] = {
            "email": "testuser@example.com",
            "password": "wrongpassword",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_obtain_token_nonexistent_user(self, api_client: APIClient) -> None:
        """Ошибка при несуществующем пользователе."""
        url = reverse("token_obtain_pair")
        data: dict[str, str] = {
            "email": "nonexistent@example.com",
            "password": "somepassword",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    """Тесты для обновления JWT токенов."""

    def test_refresh_token_success(self, api_client: APIClient, sample_user: User) -> None:
        """Успешное обновление access токена."""
        token_url = reverse("token_obtain_pair")
        token_data: dict[str, str] = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        token_response = api_client.post(token_url, token_data, format="json")
        refresh_token = token_response.data["refresh"]

        refresh_url = reverse("token_refresh")
        refresh_data: dict[str, str] = {"refresh": refresh_token}
        response = api_client.post(refresh_url, refresh_data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert isinstance(response.data["access"], str)

    def test_refresh_token_invalid(self, api_client: APIClient) -> None:
        """Ошибка при невалидном refresh токене."""
        url = reverse("token_refresh")
        data: dict[str, str] = {"refresh": "invalid_token"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenVerify:
    """Тесты для проверки JWT токенов."""

    def test_verify_token_success(self, api_client: APIClient, sample_user: User) -> None:
        """Успешная проверка валидного токена."""
        token_url = reverse("token_obtain_pair")
        token_data: dict[str, str] = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        token_response = api_client.post(token_url, token_data, format="json")
        access_token = token_response.data["access"]

        verify_url = reverse("token_verify")
        verify_data: dict[str, str] = {"token": access_token}
        response = api_client.post(verify_url, verify_data, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_verify_token_invalid(self, api_client: APIClient) -> None:
        """Ошибка при проверке невалидного токена."""
        url = reverse("token_verify")
        data: dict[str, str] = {"token": "invalid_token"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProtectedEndpoints:
    """Тесты для защиты endpoints с помощью JWT."""

    def test_access_protected_endpoint_with_token(self, api_client: APIClient, sample_user: User) -> None:
        """Доступ к защищенному endpoint с валидным токеном."""
        token_url = reverse("token_obtain_pair")
        token_data: dict[str, str] = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        token_response = api_client.post(token_url, token_data, format="json")
        access_token = token_response.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("users:user-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_access_protected_endpoint_without_token(self, api_client: APIClient) -> None:
        """Доступ к защищенному endpoint без токена должен быть запрещен."""
        url = reverse("users:user-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_invalid_token(self, api_client: APIClient) -> None:
        """Доступ к защищенному endpoint с невалидным токеном."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        url = reverse("users:user-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
