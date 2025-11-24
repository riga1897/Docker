"""Валидаторы для приложения LMS."""

import re

from rest_framework.serializers import ValidationError


def validate_youtube_url(value: str | None) -> None:
    """
    Проверяет, что URL ведёт только на YouTube.

    Разрешены следующие форматы:
    - https://www.youtube.com/watch?v=...
    - https://youtube.com/...
    - https://youtu.be/...

    Args:
        value: URL для проверки

    Raises:
        ValidationError: Если URL не ведёт на YouTube
    """
    if not value:
        return

    youtube_pattern = r"^https?://(www\.)?(youtube\.com|youtu\.be)/"

    if not re.match(youtube_pattern, value, re.IGNORECASE):
        raise ValidationError("Разрешены только ссылки на YouTube.")
