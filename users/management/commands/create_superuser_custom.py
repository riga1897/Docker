"""
Management команда для создания суперпользователя.
"""

import getpass

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from users.models import User


class Command(BaseCommand):
    """
    Команда для создания суперпользователя с email и паролем.

    Поддерживает два режима работы:
    1. Интерактивный режим (без параметров):
        python manage.py create_superuser_custom

    2. Параметризованный режим (с параметрами):
        python manage.py create_superuser_custom --email admin@example.com --password admin123

    В интерактивном режиме команда запросит email и пароль с консоли.
    Пароль запрашивается дважды для подтверждения.
    """

    help = "Создание суперпользователя с email и паролем (интерактивно или через параметры)"

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        """Добавление аргументов командной строки."""
        parser.add_argument(
            "--email",
            type=str,
            help="Email адрес суперпользователя",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Пароль суперпользователя",
        )

    def handle(self, *_args, **options) -> None:  # type: ignore[no-untyped-def]
        """Обработка команды создания суперпользователя."""
        email: str | None = options.get("email")
        password: str | None = options.get("password")

        if not email:
            email = input("Email адрес суперпользователя: ").strip()
            if not email:
                raise CommandError("Email не может быть пустым")

        if not password:
            password = getpass.getpass("Пароль суперпользователя: ")
            if not password:
                raise CommandError("Пароль не может быть пустым")
            password_confirm = getpass.getpass("Пароль (повторно): ")
            if password != password_confirm:
                raise CommandError("Пароли не совпадают")

        try:
            validate_email(email)
        except ValidationError as e:
            raise CommandError(f"Невалидный email адрес: {email}") from e

        if User.objects.filter(email=email).exists():
            raise CommandError(f"Пользователь с email {email} уже существует")

        user = User.objects.create_superuser(email=email, password=password)

        self.stdout.write(
            self.style.SUCCESS(
                f"Суперпользователь успешно создан: {user.email} (ID: {user.id})"  # type: ignore[attr-defined]
            )
        )
