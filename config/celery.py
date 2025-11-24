"""
Celery конфигурация для Django проекта.

Этот модуль настраивает Celery для асинхронной обработки задач:
- Рассылка email подписчикам при обновлении курсов
- Периодическая блокировка неактивных пользователей

Поддерживает solo pool для Windows совместимости.
"""

import os

from celery import Celery

# Устанавливаем Django settings модуль для Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создаем Celery app
app = Celery("lms_project")

# Загружаем конфигурацию из Django settings с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находим tasks.py во всех зарегистрированных Django приложениях
app.autodiscover_tasks()


# @app.task(bind=True, ignore_result=True)
# def debug_task(self) -> str:
#     """Отладочная задача для проверки работы Celery."""
#     return f"Request: {self.request!r}"
