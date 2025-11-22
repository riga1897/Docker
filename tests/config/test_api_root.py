"""Тесты для корневого API endpoint."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAPIRoot:
    """Тесты для функции api_root."""

    def test_api_root_returns_all_endpoints(self, api_client: APIClient) -> None:
        """Корневой API возвращает все доступные endpoints."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Проверяем наличие основных endpoints
        assert "course" in data
        assert "user" in data
        assert "payment" in data
        assert "lesson" in data
        assert "register" in data
        assert "auth" in data

        # Проверяем структуру auth endpoint
        assert "obtain_token" in data["auth"]
        assert "refresh_token" in data["auth"]
        assert "verify_token" in data["auth"]

    def test_api_root_course_endpoint(self, api_client: APIClient) -> None:
        """Endpoint для курсов присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "course" in data
        assert "/api/courses/" in data["course"]

    def test_api_root_user_endpoint(self, api_client: APIClient) -> None:
        """Endpoint для пользователей присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "user" in data
        assert "/api/users/" in data["user"]

    def test_api_root_lesson_endpoint(self, api_client: APIClient) -> None:
        """Endpoint для уроков присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "lesson" in data
        assert "/api/lessons/" in data["lesson"]

    def test_api_root_payment_endpoint(self, api_client: APIClient) -> None:
        """Endpoint для платежей присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "payment" in data
        assert "/api/payments/" in data["payment"]

    def test_api_root_register_endpoint(self, api_client: APIClient) -> None:
        """Endpoint для регистрации присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "register" in data
        assert "/api/register/" in data["register"]

    def test_api_root_auth_endpoints(self, api_client: APIClient) -> None:
        """JWT аутентификация endpoints присутствуют в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "auth" in data
        assert isinstance(data["auth"], dict)
        assert "obtain_token" in data["auth"]
        assert "refresh_token" in data["auth"]
        assert "verify_token" in data["auth"]
        assert "/api/token/" in data["auth"]["obtain_token"]
        assert "/api/token/refresh/" in data["auth"]["refresh_token"]
        assert "/api/token/verify/" in data["auth"]["verify_token"]
