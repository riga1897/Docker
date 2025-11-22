# Настройка и запуск Celery

Это руководство описывает, как настроить и запустить Celery для асинхронных задач в LMS проекте.

## Обзор Celery интеграции

Проект использует Celery для двух типов асинхронных задач:

1. **Email рассылка**: Отправка уведомлений подписчикам при обновлении курса
2. **Периодические задачи**: Автоматическая блокировка неактивных пользователей (>30 дней)

### Архитектура

- **config/celery.py**: Конфигурация Celery приложения с solo pool для Windows compatibility
- **lms/tasks.py**: Email рассылка при обновлении курсов
- **users/tasks.py**: Периодическая блокировка неактивных пользователей
- **lms/services.py**: Бизнес-логика email рассылки
- **users/services.py**: Бизнес-логика блокировки пользователей

## Зависимости

Celery требует:
- **Redis**: Message broker для Celery
- **django-celery-beat**: Периодические задачи через Django Admin

Все зависимости уже установлены через Poetry.

## Запуск Celery

Для работы с асинхронными задачами требуется запустить несколько процессов.

### Локальная разработка

Требуется **4 отдельных терминала** (или используйте процесс-менеджер типа `supervisor`):

### Терминал 1: Redis

**Вариант 1: Локальный redis-server (рекомендуется)**

Если Redis установлен локально (через WSL, Memurai или нативную сборку):

```bash
redis-server
```

**Вариант 2: Docker**

Если используете Docker:

```bash
docker run -p 6379:6379 redis:alpine
```

Оба варианта запускают Redis на `localhost:6379`, что и ожидает конфигурация проекта.

### Терминал 2: Celery Worker

```bash
# Для Windows
poetry run celery -A config worker --pool=solo -l info

# Для Linux/macOS
poetry run celery -A config worker -l info
```

**Важно для Windows**: Флаг `--pool=solo` обязателен! Это предотвращает ошибки с `DatabaseWrapper` при использовании eventlet/gevent.

### Терминал 3: Celery Beat

```bash
poetry run celery -A config beat -l info
```

### Терминал 4: Django Server

```bash
poetry run python manage.py runserver
```

По умолчанию сервер запустится на `http://localhost:8000`

## Конфигурация

Основные настройки находятся в `config/settings.py`:

```python
# Celery Configuration
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    "block_inactive_users_daily": {
        "task": "users.tasks.block_inactive_users_task",
        "schedule": crontab(hour=3, minute=0),  # Каждый день в 3:00 UTC
    },
}
```

**Подключение:**
- Используется Redis на `localhost:6379`
- Для production настройте удалённый Redis сервер через переменную окружения `CELERY_BROKER_URL`

## Асинхронные задачи

### 1. Email рассылка при обновлении курса

**Задача**: `lms.tasks.send_course_update_notification`

**Триггер**: Автоматически вызывается при обновлении курса (PUT/PATCH `/api/lms/courses/{id}/`)

**Логика**:
- Проверяет 4-часовое окно с момента последней рассылки
- Отправляет email всем подписчикам курса
- Обновляет `Course.last_notification_sent`

**Использование** (автоматическое в `CourseViewSet.perform_update()`):
```python
from lms.tasks import send_course_update_notification

send_course_update_notification.delay(course_id=course.id)
```

### 2. Блокировка неактивных пользователей

**Задача**: `users.tasks.block_inactive_users_task`

**Триггер**: Автоматически каждый день в 3:00 UTC через Celery Beat

**Логика**:
- Находит всех активных пользователей с `last_login` старше 30 дней
- Устанавливает `is_active=False`
- Возвращает количество заблокированных пользователей

**Ручной запуск** (для тестирования):
```python
from users.tasks import block_inactive_users_task

# Блокировка неактивных >30 дней
result = block_inactive_users_task.delay()

# Блокировка неактивных >15 дней
result = block_inactive_users_task.delay(days=15)
```

## Тестирование Celery

### Проверка email рассылки

1. Запустите все процессы (worker + beat + Django)
2. Создайте курс и подпишитесь на него
3. Обновите курс через API (PUT/PATCH)
4. Проверьте console output Django server - увидите отправленный email

Пример вывода:
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Обновление курса: Django REST Framework
From: webmaster@localhost
To: user@example.com

Здравствуйте!

Курс "Django REST Framework" был обновлен.
```

### Проверка блокировки неактивных пользователей

1. Создайте пользователя с `last_login` старше 30 дней:
```python
from django.utils import timezone
from datetime import timedelta
from users.models import User

user = User.objects.create_user(email="inactive@example.com", password="test")
user.last_login = timezone.now() - timedelta(days=31)
user.save()
```

2. Запустите задачу вручную:
```bash
poetry run python manage.py shell
>>> from users.tasks import block_inactive_users_task
>>> result = block_inactive_users_task()
>>> print(f"Blocked {result} users")
```

3. Проверьте, что пользователь заблокирован:
```python
user.refresh_from_db()
assert user.is_active == False
```

## Email Backend

Проект использует **console email backend** для разработки:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

Все email отображаются в консоли Django server. Для production используйте SMTP backend.

## Мониторинг

### Celery Worker логи

Celery worker показывает:
- Полученные задачи
- Результаты выполнения
- Ошибки

Пример:
```
[2024-11-15 10:30:00,000: INFO/MainProcess] Task lms.tasks.send_course_update_notification[abc-123] received
[2024-11-15 10:30:01,500: INFO/MainProcess] Task lms.tasks.send_course_update_notification[abc-123] succeeded in 1.5s: 5
```

### Celery Beat логи

Celery beat показывает расписание периодических задач:
```
[2024-11-15 03:00:00,000: INFO/Beat] Scheduler: Sending due task block_inactive_users_daily
```

## Troubleshooting

### Windows: `DatabaseWrapper objects created in a thread can only be used in that same thread`

**Решение**: Используйте `--pool=solo` для celery worker:
```bash
celery -A config worker --pool=solo -l info
```

### Redis connection refused

**Проблема**: Redis не доступен

**Решение**: 
- Запустите Redis через `redis-server`, Docker или WSL
- Проверьте, что Redis слушает на порту 6379

### Задачи не выполняются

**Проблема**: Celery worker не запущен

**Решение**:
- Проверьте, что worker запущен и показывает `ready`
- Проверьте логи worker на ошибки
- Убедитесь, что Redis доступен

### Email не отправляются

**Проблема**: Не прошло 4 часа с последней рассылки

**Решение**: Проверьте `Course.last_notification_sent` или обнулите его:
```python
course.last_notification_sent = None
course.save()
```

## Дополнительные ресурсы

- [Celery Documentation](https://docs.celeryq.dev/)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/)
- [Redis Documentation](https://redis.io/docs/)
