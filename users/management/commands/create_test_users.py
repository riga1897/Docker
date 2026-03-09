"""
Management команда для создания тестовых пользователей.

Создаёт демо-пользователей для разработки и тестирования системы прав доступа.
Команда идемпотентная - можно запускать многократно без побочных эффектов.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    """
    Команда для создания тестовых пользователей с разными правами доступа.

    Создаёт следующих пользователей:
    1. Модератор (moderator@example.com / moderator123)
       - Входит в группу "Модераторы"
       - Может редактировать любые курсы и уроки
       - НЕ является суперпользователем

    2. Обычный пользователь (user@example.com / user123)
       - Не входит в группу "Модераторы"
       - Может редактировать только свои курсы и уроки
       - НЕ является суперпользователем

    Примеры использования:
        python manage.py create_test_users
    """

    help = "Создание тестовых пользователей для разработки (модератор, обычный пользователь)"

    def handle(self, *_args, **options) -> None:  # type: ignore[no-untyped-def]
        """Обработка команды создания тестовых пользователей."""
        moderator = self._create_moderator()
        user = self._create_regular_user()

        self.stdout.write(self.style.SUCCESS("\n✅ Создание тестовых пользователей завершено успешно!"))
        self.stdout.write("\nДля входа используйте:")
        self.stdout.write(f"  Модератор:   {moderator.email} / moderator123")  # type: ignore[attr-defined]
        self.stdout.write(f"  Пользователь: {user.email} / user123")  # type: ignore[attr-defined]

    def _create_moderator(self) -> User:
        """Создание тестового пользователя-модератора."""
        email = "moderator@example.com"
        password = "moderator123"

        moderator, created = User.objects.get_or_create(
            email=email,
            defaults={
                "is_staff": False,
                "is_superuser": False,
            },
        )

        if created:
            moderator.set_password(password)
            moderator.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Модератор создан: {moderator.email} (ID: {moderator.id})"  # type: ignore[attr-defined]
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"• Модератор уже существует: {moderator.email} (ID: {moderator.id})"  # type: ignore[attr-defined]
                )
            )

        moderators_group = Group.objects.get(name="Модераторы")
        if moderators_group not in moderator.groups.all():  # type: ignore[attr-defined]
            moderator.groups.add(moderators_group)  # type: ignore[attr-defined]
            self.stdout.write(self.style.SUCCESS(f"✓ Модератор добавлен в группу '{moderators_group.name}'"))
        else:
            self.stdout.write(self.style.WARNING(f"• Модератор уже в группе '{moderators_group.name}'"))

        return moderator  # type: ignore[return-value]

    def _create_regular_user(self) -> User:
        """Создание тестового обычного пользователя."""
        email = "user@example.com"
        password = "user123"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "is_staff": False,
                "is_superuser": False,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Пользователь создан: {user.email} (ID: {user.id})"  # type: ignore[attr-defined]
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"• Пользователь уже существует: {user.email} (ID: {user.id})"  # type: ignore[attr-defined]
                )
            )

        return user  # type: ignore[return-value]
