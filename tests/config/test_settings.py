"""
Тесты для config/settings.py.

Проверяет конфигурацию Django, особенно CSRF настройки для Replit.
"""

import pytest


@pytest.mark.django_db
class TestCsrfSettings:
    """Тесты для CSRF настроек Replit."""

    def test_csrf_cookie_settings(self) -> None:
        """Проверка настроек CSRF cookies для работы в iframe."""
        from django.conf import settings

        assert settings.CSRF_COOKIE_SAMESITE == "None"
        assert settings.CSRF_COOKIE_SECURE is True
        assert settings.SESSION_COOKIE_SAMESITE == "None"
        assert settings.SESSION_COOKIE_SECURE is True

    def test_secure_proxy_ssl_header(self) -> None:
        """Проверка настройки SSL через прокси Replit."""
        from django.conf import settings

        assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
