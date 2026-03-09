"""
Management команда для инициализации групп пользователей.

Создаёт необходимые группы для работы системы прав доступа.
Команда идемпотентная - можно запускать многократно без побочных эффектов.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Команда для инициализации групп пользователей в системе.

    Выполняет следующие действия:
    1. Создаёт группу "Модераторы" (если её нет)
    2. Удаляет группу "Казначеи" (если она существует)

    Примеры использования:
        python manage.py init_groups
    """

    help = "Инициализация групп пользователей: создание Модераторов, удаление неиспользуемых групп"

    def handle(self, *_args, **options) -> None:  # type: ignore[no-untyped-def]
        """Обработка команды инициализации групп."""
        moderators_group, created = Group.objects.get_or_create(name="Модераторы")

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Группа '{moderators_group.name}' успешно создана (ID: {moderators_group.id})"  # type: ignore[attr-defined]
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"• Группа '{moderators_group.name}' уже существует (ID: {moderators_group.id})"  # type: ignore[attr-defined]
                )
            )

        try:
            treasurers_group = Group.objects.get(name="Казначеи")
            treasurers_group.delete()
            self.stdout.write(self.style.SUCCESS("✓ Группа 'Казначеи' успешно удалена"))
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING("• Группа 'Казначеи' не найдена (возможно, уже удалена)"))

        self.stdout.write(self.style.SUCCESS("\n✅ Инициализация групп завершена успешно!"))
