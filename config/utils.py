"""
Утилиты для приложения Django LMS.

Этот модуль содержит вспомогательные функции общего назначения,
используемые в различных частях приложения.
"""

from django.conf import settings


def build_url(path: str) -> str:
    """
    Генерирует полный URL на основе пути и настроек домена.

    Автоматически определяет протокол (http/https) в зависимости от домена:
    - localhost или 127.0.0.1 → http://
    - production domain → https://

    Args:
        path: Путь относительно корня сайта (например, '/api/payments/success/')

    Returns:
        str: Полный URL (например, 'https://example.com/api/payments/success/')

    Examples:
        >>> build_url('/api/payments/success/')
        'http://localhost:8000/api/payments/success/'  # если SITE_DOMAIN='localhost:8000'

        >>> build_url('/api/payments/cancel/')
        'https://myapp.example.com/api/payments/cancel/'  # если SITE_DOMAIN='myapp.example.com'
    """
    domain = settings.SITE_DOMAIN

    # Определяем localhost по наличию 'localhost' или '127.0.0.1' в домене
    protocol = "http" if "localhost" in domain or "127.0.0.1" in domain else "https"

    url = f"{protocol}://{domain}{path}"

    return url
