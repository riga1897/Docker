"""
Celery задачи для LMS приложения.

Этот модуль содержит асинхронные задачи для:
- Рассылки email уведомлений подписчикам при обновлении курсов

Задачи являются тонкими обертками над сервисными функциями из lms/services.py.
Вся бизнес-логика находится в service layer для удобства тестирования.
"""

from celery import shared_task


@shared_task
def send_course_update_notification(course_id: int) -> int:
    """
    Celery задача для отправки email уведомлений подписчикам курса.

    Вызывается асинхронно при обновлении курса через ViewSet.
    Является тонкой оберткой над send_course_update_email из services.

    Args:
        course_id: ID обновленного курса

    Returns:
        Количество отправленных писем
    """
    from lms.services import send_course_update_email

    return send_course_update_email(course_id)
