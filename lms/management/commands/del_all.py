"""
Управляющая команда для удаления всех данных из базы данных.

Использование:
    # Удалить курсы, уроки и платежи (пользователей не трогаем)
    python manage.py del_all

    # Удалить всё включая пользователей
    python manage.py del_all --include-users

    # Удалить без подтверждения (для автоматизации)
    python manage.py del_all --force

    # Полная очистка без подтверждения
    python manage.py del_all --include-users --force

⚠️ ВНИМАНИЕ: Эта команда безвозвратно удаляет данные из базы!
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import connection

from lms.models import Course, Lesson
from users.models import Payment, User


class Command(BaseCommand):
    """
    Управляющая команда для удаления всех данных из базы данных.

    По умолчанию удаляет только данные LMS (платежи, уроки, курсы),
    но не трогает пользователей (чтобы не потерять доступ к админке).

    Флаг --include-users позволяет удалить также всех пользователей.
    Флаг --force пропускает запрос подтверждения.
    """

    help = "Удаление всех данных из базы данных (курсы, уроки, платежи)"

    def add_arguments(self, parser: CommandParser) -> None:
        """Добавление аргументов командной строки."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Удалить без подтверждения",
        )
        parser.add_argument(
            "--include-users",
            action="store_true",
            help="Удалить также всех пользователей (по умолчанию НЕ удаляются)",
        )

    def reset_sequence(self, table_name: str) -> None:
        """
        Сброс счетчика AUTO_INCREMENT для таблицы.

        Поддерживает PostgreSQL (ALTER SEQUENCE).
        Для других БД (SQLite, MySQL) пропускается с информационным сообщением.

        Args:
            table_name: Имя таблицы для сброса счетчика
        """
        # Проверяем тип базы данных
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                # PostgreSQL использует SERIAL с sequence именем table_name_id_seq
                cursor.execute(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1;")
            self.stdout.write(self.style.SUCCESS(f"   Счётчик {table_name} сброшен"))
        else:
            # Для SQLite, MySQL и других БД сброс счетчиков работает иначе
            self.stdout.write(f"   Сброс счетчика {table_name} пропущен (БД: {connection.vendor})")

    def handle(self, *_args: Any, **options: Any) -> None:
        """Основная логика команды."""
        force = options["force"]
        include_users = options["include_users"]

        # Подсчёт записей до удаления
        payments_count = Payment.objects.count()
        lessons_count = Lesson.objects.count()
        courses_count = Course.objects.count()
        users_count = User.objects.count()

        # Вывод предупреждения
        self.stdout.write(self.style.WARNING("\n⚠️  ВНИМАНИЕ: Будут удалены следующие данные:\n"))
        self.stdout.write(f"  Платежей: {payments_count}")
        self.stdout.write(f"  Уроков: {lessons_count}")
        self.stdout.write(f"  Курсов: {courses_count}")

        if include_users:
            self.stdout.write(self.style.ERROR(f"  Пользователей: {users_count} (включая админов!)"))
        else:
            self.stdout.write("  Пользователей: НЕ будут затронуты")

        # Запрос подтверждения (если не --force)
        if not force:
            self.stdout.write("")
            confirmation = input("Вы уверены? (yes/no): ")
            if confirmation.lower() not in ["yes", "y", "да"]:
                self.stdout.write(self.style.WARNING("Операция отменена."))
                return

        # Удаление в правильном порядке (из-за ForeignKey)
        self.stdout.write("")

        # 1. Удаляем платежи (зависят от User, Course, Lesson)
        deleted_payments, _ = Payment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✅ Удалено платежей: {deleted_payments}"))
        self.reset_sequence("users_payment")

        # 2. Удаляем уроки (зависят от Course)
        deleted_lessons, _ = Lesson.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✅ Удалено уроков: {deleted_lessons}"))
        self.reset_sequence("lms_lesson")

        # 3. Удаляем курсы
        deleted_courses, _ = Course.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✅ Удалено курсов: {deleted_courses}"))
        self.reset_sequence("lms_course")

        # 4. Опционально удаляем пользователей
        if include_users:
            deleted_users, _ = User.objects.all().delete()
            self.stdout.write(self.style.ERROR(f"✅ Удалено пользователей: {deleted_users}"))
            self.reset_sequence("users_user")
            self.stdout.write(self.style.WARNING("\n⚠️  Все пользователи удалены! Доступ к админке потерян."))

        # Итоговое сообщение
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🎉 Операция завершена успешно!"))
