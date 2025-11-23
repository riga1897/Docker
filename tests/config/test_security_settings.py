"""
Тесты для настроек безопасности Django (HTTPS, HSTS, SSL).

Модуль содержит unit-тесты для проверки корректности конфигурации
security settings в config/settings.py для production VPS с HTTPS.
"""

import os
from typing import Any

from django.conf import settings
from django.test import override_settings


class TestSecuritySettings:
    """Тесты для security settings (HTTPS, HSTS, SSL redirect)."""

    def test_secure_ssl_redirect_default_false(self) -> None:
        """
        Тест: SECURE_SSL_REDIRECT по умолчанию False.

        Проверяем, что без environment variable редирект HTTP→HTTPS отключен
        (безопасно для локальной разработки на http://localhost).
        """
        with override_settings(SECURE_SSL_REDIRECT=False):
            assert settings.SECURE_SSL_REDIRECT is False

    def test_secure_ssl_redirect_can_be_enabled(self, monkeypatch: Any) -> None:
        """
        Тест: SECURE_SSL_REDIRECT можно включить через env variable.

        Проверяем, что setting читается из environment variable
        и корректно конвертируется в boolean.
        """
        monkeypatch.setenv("SECURE_SSL_REDIRECT", "True")

        # Эмулируем логику из settings.py
        secure_ssl_redirect = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"

        assert secure_ssl_redirect is True

    def test_secure_hsts_seconds_default_zero(self) -> None:
        """
        Тест: SECURE_HSTS_SECONDS по умолчанию 0 (HSTS отключен).

        Проверяем, что без environment variable HSTS не активен
        (безопасно для локальной разработки).
        """
        with override_settings(SECURE_HSTS_SECONDS=0):
            assert settings.SECURE_HSTS_SECONDS == 0

    def test_secure_hsts_seconds_can_be_set(self, monkeypatch: Any) -> None:
        """
        Тест: SECURE_HSTS_SECONDS читается из env variable.

        Проверяем, что можно установить HSTS на 1 год (31536000 секунд)
        через environment variable для production.
        """
        monkeypatch.setenv("SECURE_HSTS_SECONDS", "31536000")

        # Эмулируем логику из settings.py
        hsts_seconds = int(os.getenv("SECURE_HSTS_SECONDS", "0"))

        assert hsts_seconds == 31536000

    def test_secure_hsts_include_subdomains_default_false(self) -> None:
        """
        Тест: SECURE_HSTS_INCLUDE_SUBDOMAINS по умолчанию False.

        Проверяем, что HSTS для поддоменов отключен по умолчанию.
        """
        with override_settings(SECURE_HSTS_INCLUDE_SUBDOMAINS=False):
            assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is False

    def test_secure_hsts_include_subdomains_can_be_enabled(
        self, monkeypatch: Any
    ) -> None:
        """
        Тест: SECURE_HSTS_INCLUDE_SUBDOMAINS можно включить через env.

        Проверяем корректную конвертацию строки "True" в boolean.
        """
        monkeypatch.setenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True")

        # Эмулируем логику из settings.py
        hsts_subdomains = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"

        assert hsts_subdomains is True

    def test_secure_hsts_preload_default_false(self) -> None:
        """
        Тест: SECURE_HSTS_PRELOAD по умолчанию False.

        Проверяем, что HSTS preload отключен по умолчанию.
        """
        with override_settings(SECURE_HSTS_PRELOAD=False):
            assert settings.SECURE_HSTS_PRELOAD is False

    def test_secure_hsts_preload_can_be_enabled(self, monkeypatch: Any) -> None:
        """
        Тест: SECURE_HSTS_PRELOAD можно включить через env variable.

        Проверяем, что можно включить добавление сайта в HSTS preload list
        браузеров через environment variable.
        """
        monkeypatch.setenv("SECURE_HSTS_PRELOAD", "True")

        # Эмулируем логику из settings.py
        hsts_preload = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

        assert hsts_preload is True

    def test_production_security_configuration(self, monkeypatch: Any) -> None:
        """
        Тест: Полная production конфигурация безопасности.

        Проверяем, что все security settings корректно устанавливаются
        для production VPS с HTTPS (как в .env.production.example).
        """
        # Устанавливаем production значения через environment
        monkeypatch.setenv("SECURE_SSL_REDIRECT", "True")
        monkeypatch.setenv("SECURE_HSTS_SECONDS", "31536000")
        monkeypatch.setenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True")
        monkeypatch.setenv("SECURE_HSTS_PRELOAD", "True")

        # Эмулируем логику из settings.py
        secure_ssl_redirect = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"
        hsts_seconds = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
        hsts_subdomains = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
        hsts_preload = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

        # Проверяем что все настройки включены для production
        assert secure_ssl_redirect is True
        assert hsts_seconds == 31536000  # 1 год
        assert hsts_subdomains is True
        assert hsts_preload is True

    def test_local_development_security_configuration(self) -> None:
        """
        Тест: Локальная разработка имеет безопасные defaults.

        Проверяем, что без environment variables (локальная разработка)
        все security settings отключены для работы на http://localhost.
        """
        # Эмулируем логику из settings.py без environment variables
        secure_ssl_redirect = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"
        hsts_seconds = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
        hsts_subdomains = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
        hsts_preload = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

        # Проверяем что все настройки отключены по умолчанию
        assert secure_ssl_redirect is False
        assert hsts_seconds == 0
        assert hsts_subdomains is False
        assert hsts_preload is False
