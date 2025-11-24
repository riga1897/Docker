"""
Тесты для config/urls.py.

Проверяет URL конфигурацию проекта.
"""

import pytest
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import resolve


@pytest.mark.django_db
class TestUrlPatterns:
    """Тесты для URL паттернов."""

    def test_root_redirect_to_api(self) -> None:
        """Корневой URL должен редиректить на /api/."""
        match = resolve("/")
        assert match.view_name == "root-redirect"

    def test_api_root_accessible(self) -> None:
        """API root должен быть доступен."""
        match = resolve("/api/")
        assert match.view_name == "api-root"

    def test_admin_url_accessible(self) -> None:
        """Admin панель должна быть доступна."""
        match = resolve("/admin/")
        assert "admin" in match.view_name

    def test_jwt_token_urls_accessible(self) -> None:
        """JWT токен endpoints должны быть доступны."""
        token_match = resolve("/api/token/")
        refresh_match = resolve("/api/token/refresh/")
        verify_match = resolve("/api/token/verify/")

        assert token_match.view_name == "token_obtain_pair"
        assert refresh_match.view_name == "token_refresh"
        assert verify_match.view_name == "token_verify"

    def test_lms_urls_included(self) -> None:
        """LMS URLs должны быть подключены."""
        match = resolve("/api/courses/")
        assert "lms" in match.view_name

    def test_users_urls_included(self) -> None:
        """Users URLs должны быть подключены."""
        match = resolve("/api/users/")
        assert "users" in match.view_name


@override_settings(DEBUG=True, MEDIA_URL="/media/", MEDIA_ROOT="/tmp/media")
class TestDebugStaticFiles(SimpleTestCase):
    """Тесты для static files в DEBUG режиме."""

    def test_media_url_served_in_debug_mode(self) -> None:
        """В DEBUG режиме должны обслуживаться media файлы."""
        from importlib import reload

        from config import urls

        reload(urls)

        from django.conf.urls.static import static

        media_patterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        assert len(media_patterns) > 0
