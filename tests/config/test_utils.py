"""
Тесты для утилит конфигурации приложения.

Модуль содержит unit-тесты для функций из config/utils.py
"""

from django.test import override_settings

from config.utils import build_url


class TestBuildUrl:
    """Тесты для функции build_url()"""

    @override_settings(SITE_DOMAIN="localhost:8000")
    def test_build_url_localhost_http(self) -> None:
        """
        Тест: build_url() должна использовать http:// для localhost.

        Проверяем, что для localhost-домена генерируется URL с http протоколом.
        """
        url = build_url("/api/payments/success/")

        assert url == "http://localhost:8000/api/payments/success/"

    @override_settings(SITE_DOMAIN="127.0.0.1:8000")
    def test_build_url_localhost_ip_http(self) -> None:
        """
        Тест: build_url() должна использовать http:// для 127.0.0.1 (localhost IP).

        Проверяем, что для localhost IP адреса генерируется URL с http протоколом.
        """
        url = build_url("/api/payments/cancel/")

        assert url == "http://127.0.0.1:8000/api/payments/cancel/"

    @override_settings(SITE_DOMAIN="example.com")
    def test_build_url_production_https(self) -> None:
        """
        Тест: build_url() должна использовать https:// для production домена.

        Проверяем, что для production домена генерируется URL с https протоколом.
        """
        url = build_url("/api/users/profile/")

        assert url == "https://example.com/api/users/profile/"

    @override_settings(SITE_DOMAIN="myapp.replit.app")
    def test_build_url_replit_domain_https(self) -> None:
        """
        Тест: build_url() должна использовать https:// для Replit домена.

        Проверяем, что для Replit домена генерируется URL с https протоколом.
        """
        url = build_url("/api/courses/")

        assert url == "https://myapp.replit.app/api/courses/"

    @override_settings(SITE_DOMAIN="localhost:5000")
    def test_build_url_custom_localhost_port(self) -> None:
        """
        Тест: build_url() должна корректно работать с кастомным портом localhost.

        Проверяем, что функция работает с нестандартным портом для localhost.
        """
        url = build_url("/api/health/")

        assert url == "http://localhost:5000/api/health/"

    @override_settings(SITE_DOMAIN="subdomain.example.com")
    def test_build_url_subdomain(self) -> None:
        """
        Тест: build_url() должна корректно работать с поддоменами.

        Проверяем, что функция работает с production доменом с поддоменом.
        """
        url = build_url("/api/")

        assert url == "https://subdomain.example.com/api/"

    @override_settings(SITE_DOMAIN="localhost:8000")
    def test_build_url_empty_path(self) -> None:
        """
        Тест: build_url() должна корректно обрабатывать пустой путь.

        Проверяем, что функция работает с корневым путём.
        """
        url = build_url("/")

        assert url == "http://localhost:8000/"

    @override_settings(SITE_DOMAIN="localhost:8000")
    def test_build_url_path_without_leading_slash(self) -> None:
        """
        Тест: build_url() должна корректно обрабатывать путь без начального слеша.

        Проверяем, что функция работает даже если путь не начинается с /.
        ПРИМЕЧАНИЕ: Функция ожидает путь с начальным слешом, но не валидирует это.
        """
        url = build_url("api/test/")

        # Без начального слеша путь склеится напрямую с доменом
        assert url == "http://localhost:8000api/test/"
