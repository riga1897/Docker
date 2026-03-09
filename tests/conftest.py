"""Общие фикстуры для всех тестов."""

import pytest
from rest_framework.test import APIClient

from lms.models import Course
from users.models import User


@pytest.fixture
def user(db: None) -> User:
    """Создать обычного пользователя для тестов."""
    return User.objects.create_user(email="testuser@example.com", password="testpass123")


@pytest.fixture
def another_user(db: None) -> User:
    """Создать второго пользователя для тестов."""
    return User.objects.create_user(email="anotheruser@example.com", password="testpass123")


@pytest.fixture
def api_client() -> APIClient:
    """Создать API клиент для тестов."""
    return APIClient()


@pytest.fixture
def course(db: None, user: User) -> Course:
    """Создать курс для тестов."""
    return Course.objects.create(title="Test Course", description="Test Description", owner=user)


@pytest.fixture
def another_course(db: None, user: User) -> Course:
    """Создать второй курс для тестов."""
    return Course.objects.create(title="Another Test Course", description="Another Description", owner=user)
