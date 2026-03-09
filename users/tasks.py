"""
Celery задачи для Users приложения.

Этот модуль содержит периодические задачи для:
- Блокировки пользователей, неактивных более 30 дней

Задачи являются тонкими обертками над сервисными функциями из users/services.py.
Вся бизнес-логика находится в service layer для удобства тестирования.
"""

from celery import shared_task


@shared_task
def block_inactive_users_task(days: int = 30) -> int:
    """
    Celery задача для блокировки неактивных пользователей.

    Запускается периодически через celery-beat (раз в сутки).
    Является тонкой оберткой над block_inactive_users из services.

    Args:
        days: Количество дней неактивности (по умолчанию 30)

    Returns:
        Количество заблокированных пользователей
    """
    from users.services import block_inactive_users

    return block_inactive_users(days)
