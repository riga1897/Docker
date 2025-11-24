# LMS (Learning Management System) - Roadmap

## 📋 Содержание

1. [Текущее состояние](#текущее-состояние)
2. [Архитектура системы](#архитектура-системы)
3. [Планируемые модели](#планируемые-модели)
4. [API Endpoints](#api-endpoints)
5. [Бизнес-логика](#бизнес-логика)
6. [Будущие интеграции](#будущие-интеграции)

---

## Текущее состояние

### Существующие модели

#### `lms/models.py`

**BaseModel** - базовая модель с timestamps
```python
class BaseModel(models.Model):
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

**Course** - модель курса ✅ **Реализована**
```python
class Course(BaseModel):
    title: models.CharField = models.CharField(max_length=200, verbose_name="Название курса")
    description: models.TextField = models.TextField(verbose_name="Описание курса")
    preview: models.ImageField = models.ImageField(
        upload_to="courses/previews/",
        blank=True,
        null=True,
        verbose_name="Превью курса"
    )
    
    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["-created_at"]
```

**Lesson** - модель урока ✅ **Реализована**
```python
class Lesson(BaseModel):
    course: models.ForeignKey = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс"
    )
    title: models.CharField = models.CharField(max_length=200, verbose_name="Название урока")
    description: models.TextField = models.TextField(verbose_name="Описание урока")
    preview: models.ImageField = models.ImageField(
        upload_to="lessons/previews/",
        blank=True,
        null=True,
        verbose_name="Превью урока"
    )
    video_url: models.URLField = models.URLField(
        max_length=500,
        verbose_name="Ссылка на видео"
    )
    
    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["course", "id"]
```

### Что уже готово
- ✅ Базовая структура Django проекта
- ✅ PostgreSQL база данных с демо-данными
- ✅ DRF установлен и настроен
- ✅ Django Filter для фильтрации и сортировки API
- ✅ **Динамическая главная страница API** - автоматический сбор endpoints из роутеров
- ✅ Кастомная модель User с email-авторизацией
- ✅ **Полностью реализованные модели Course и Lesson** с полями
- ✅ **REST API для Course и Lesson** (ViewSet для Course, Generic views для Lesson)
- ✅ **User API** (UserViewSet с CRUD операциями)
- ✅ **Система платежей** (модель Payment с фильтрацией + Stripe интеграция)
- ✅ **CourseSerializer расширен** - lessons_count + вложенные lessons
- ✅ **Публичные и детальные профили** - PublicUserSerializer и UserDetailSerializer
- ✅ **Service Layer Pattern** - бизнес-логика в `users/services.py` и `lms/services.py` (Stripe, платежи, подписки, вычисления сериализаторов)
- ✅ **Celery интеграция** - асинхронные задачи (email рассылки, блокировка неактивных пользователей)
- ✅ **283 теста** - все проходят (78 Django APITestCase + 205 pytest, **98.22% coverage**)
- ✅ **Coverage Aggregation** - правильная работа pytest-cov с параллельным запуском (-n auto)
- ✅ **Django Fixtures** для тестовых данных
- ✅ **Dual Testing Strategy** - API тесты в app folders, unit/integration тесты в tests/
- ✅ **Git Branching Strategy** - Gitflow с release ветками для структурированных релизов
- ✅ **CI/CD Pipeline** - GitHub Actions с автоматическим deployment и созданием PR
- ✅ **Четырёхуровневая архитектура deployment:**
  - Development (локальная разработка, port 5000)
  - Staging (Docker Desktop, port 8000, live reload)
  - Pre-Production (release/* → VPS, port 8000, Gunicorn, TEST Stripe keys)
  - Production (main → VPS, port 8000, Gunicorn, LIVE Stripe keys)
- ✅ **Docker контейнеризация** - 5 сервисов (web, db, redis, celery_worker, celery_beat)
- ✅ **Автоматическое создание PR** - после успешного preprod deployment
- ✅ **GitHub Container Registry** - хранение Docker образов с тегами preprod-latest и latest

### Демонстрационные данные

**Текущая база данных содержит:**
- 1 суперпользователь: `admin@example.com` / `admin123`
- 3 курса:
  - Python для начинающих
  - Django REST Framework
  - PostgreSQL и базы данных
- 5 уроков:
  - 3 урока в курсе Python
  - 2 урока в курсе Django
- 3 платежа:
  - 2 платежа за курсы (2500₽, 3000₽)
  - 1 платёж за урок (500₽)

**Доступные Fixtures:**

Все демо-данные сохранены в `lms/fixtures/` и `users/fixtures/` для быстрого восстановления:

```bash
# Загрузка демо-данных
python manage.py loaddata lms/fixtures/courses.json    # 3 курса (1 KB)
python manage.py loaddata lms/fixtures/lessons.json    # 5 уроков (2.1 KB)
python manage.py loaddata users/fixtures/payments.json # 3 платежа
```

**Использование fixtures:**
- Для быстрого старта разработки
- Для тестирования API с реальными данными
- Для восстановления после пересоздания БД

---

## Git Branching Strategy

Проект использует **Gitflow** - структурированную стратегию ветвления для надёжных релизов.

### Постоянные ветки

| Ветка | Назначение | Deployment |
|-------|-----------|------------|
| `main` | Production-ready код | → Production VPS (автоматически) |
| `develop` | Интеграция фич, активная разработка | → Staging (Docker Desktop, локально) |

### Временные ветки

| Префикс | Назначение | Создаётся из | Мержится в | Пример |
|---------|-----------|--------------|------------|--------|
| `feature/*` | Новые фичи | `develop` | `develop` | `feature/payment-integration` |
| `release/*` | Pre-Production тестирование | `develop` | `main` + `develop` | `release/v1.0` |
| `hotfix/*` | Срочные исправления в production | `main` | `main` + `develop` | `hotfix/critical-bug` |
| `bugfix/*` | Исправления багов | `develop` | `develop` | `bugfix/login-error` |

### Gitflow Workflow

```bash
# 1. Разработка новой фичи
git checkout develop
git pull origin develop
git checkout -b feature/stripe-checkout
# ... разработка ...
git push origin feature/stripe-checkout
# Создать PR: feature/stripe-checkout → develop

# 2. Тестирование в Staging (Docker Desktop)
git checkout develop
git pull origin develop
docker compose up  # Локальное тестирование

# 3. Создание релиза для Pre-Production
git checkout -b release/v1.0 develop
git push origin release/v1.0
# → CI/CD автоматически:
#    - Собирает Docker образ (preprod-latest)
#    - Деплоит на preprod VPS
#    - Проверяет health check
#    - Создаёт draft PR: release/v1.0 → main

# 4. Тестирование на препроде
# Открыть http://<PREPROD_IP>:8000/api/
# Протестировать с TEST Stripe keys

# 5. Если нашли баг на препроде
git checkout release/v1.0
git checkout -b bugfix/preprod-fix
# ... исправление ...
git checkout release/v1.0
git merge bugfix/preprod-fix
git push origin release/v1.0
# → CI/CD автоматически ре-деплоит на preprod

# 6. Релиз в Production (после успешного тестирования)
# Вариант A: через GitHub UI
#   - Открыть draft PR (создан автоматически)
#   - Нажать "Ready for review"
#   - Нажать "Merge Pull Request"
# Вариант B: через командную строку
git checkout main
git pull origin main
git merge release/v1.0
git tag -a v1.0 -m "Release version 1.0"
git push origin main --tags
# → CI/CD автоматически деплоит на production VPS

# 7. Вернуть изменения в develop
git checkout develop
git merge release/v1.0
git push origin develop

# 8. Удалить release ветку (опционально)
git branch -d release/v1.0
git push origin --delete release/v1.0
```

### Hotfix Workflow (срочные исправления в production)

```bash
# 1. Создать hotfix из main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# 2. Исправить баг
# ... код ...
git push origin hotfix/critical-security-fix

# 3. Merge в main (production)
git checkout main
git merge hotfix/critical-security-fix
git tag -a v1.0.1 -m "Hotfix: critical security fix"
git push origin main --tags
# → CI/CD автоматически деплоит на production

# 4. Merge в develop (чтобы fix попал в будущие релизы)
git checkout develop
git merge hotfix/critical-security-fix
git push origin develop

# 5. Удалить hotfix ветку
git branch -d hotfix/critical-security-fix
git push origin --delete hotfix/critical-security-fix
```

### CI/CD Автоматизация

| Событие | Триггер | Действия |
|---------|---------|----------|
| Push в `release/*` | GitHub Actions | 1. Запуск тестов (283 теста)<br>2. Code quality checks (ruff, mypy, black)<br>3. Build Docker образа (preprod-latest)<br>4. Push в GHCR<br>5. Deploy на preprod VPS<br>6. Health check<br>7. **Автоматическое создание draft PR** |
| Merge в `main` | GitHub Actions | 1. Запуск тестов<br>2. Code quality checks<br>3. Build Docker образа (latest)<br>4. Push в GHCR<br>5. Deploy на production VPS<br>6. Health check |
| Push в `feature/*` или `develop` | - | Нет автодеплоя (только локальная разработка) |

### GitHub Secrets для CI/CD

**Pre-Production:**
- `PREPROD_SERVER_IP` - IP адрес препрод сервера
- `PREPROD_SSH_USER` - SSH пользователь
- `PREPROD_SSH_KEY` - Приватный SSH ключ
- `PREPROD_DEPLOY_DIR` - Директория деплоя (`/opt/lms-preprod`)
- `PREPROD_STRIPE_SECRET_KEY` - Stripe TEST secret key
- `PREPROD_STRIPE_PUBLISHABLE_KEY` - Stripe TEST publishable key

**Production:**
- `SERVER_IP` - IP адрес production сервера
- `SSH_USER` - SSH пользователь
- `SSH_KEY` - Приватный SSH ключ
- `DEPLOY_DIR` - Директория деплоя (`/opt/lms`)
- `STRIPE_SECRET_KEY` - Stripe LIVE secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe LIVE publishable key

### Преимущества Gitflow

✅ **Защита production** - код попадает в production только после тестирования на preprod  
✅ **Структурированные релизы** - release ветки позволяют тестировать и фиксить перед релизом  
✅ **Параллельная разработка** - multiple features одновременно в develop  
✅ **Hotfix без влияния на develop** - срочные исправления не ждут завершения фич  
✅ **Автоматизация** - CI/CD автоматически деплоит и создаёт PR  
✅ **История релизов** - git tags отслеживают все версии  

### Соглашения об именовании

- Используйте lowercase с дефисами: `feature/user-authentication`
- Включайте номер тикета (если есть): `feature/JIRA-123-payment-flow`
- Будьте описательными: `bugfix/fix-login-timeout` вместо `bugfix/fix-bug`
- Для release используйте версию: `release/v1.0`, `release/v1.1`
- Для hotfix указывайте суть: `hotfix/security-patch` или `hotfix/v1.0.1`

---

## Ближайшие улучшения

### 📸 Превью изображения в демо-данных (fixtures)

**Статус:** ✅ **РЕАЛИЗОВАНО** (27 октября 2025)

**Что реализовано:**

- ✅ Поля `preview` добавлены в модели Course и Lesson
- ✅ Поля `preview` включены в API сериализаторы
- ✅ Реальные файлы превью на диске:
  - `media/courses/previews/` — 17 файлов
  - `media/lessons/previews/` — 15 файлов
- ✅ **Fixtures содержат пути к превью:**
  ```json
  // lms/fixtures/courses.json
  "preview": "courses/previews/test_preview_4XBpvRe.jpg"
  
  // lms/fixtures/lessons.json
  "preview": "lessons/previews/lesson_preview_7SyCgUf.jpg"
  ```

**Результат:**

При загрузке fixtures через `python manage.py loaddata`:
- Все 3 курса имеют превью ✅
- Все 5 уроков имеют превью ✅
- API возвращает полные URL к изображениям ✅
- ImageField работает корректно во всех endpoints ✅

**Польза:**
- 🎨 API выглядит профессионально сразу после `loaddata`
- 💼 Удобная демонстрация проекта потенциальным работодателям
- 🧪 Полноценное тестирование ImageField в API endpoints

---

### 🏗️ Рефакторинг: Service Layer для бизнес-логики

**Статус:** ✅ **ЗАВЕРШЁН** (18 ноября 2025)

**Что было реализовано:**

1. **Расширен `lms/services.py`** - добавлены функции для вычислений:
   ```python
   def calculate_lessons_count(course: Course) -> int:
       """Вычислить количество уроков в курсе."""
       return course.lessons.count()
   
   def check_user_subscription(course: Course, user: User | None) -> bool:
       """Проверить подписан ли пользователь на курс."""
       if user is None or not user.is_authenticated:
           return False
       return Subscription.objects.filter(user=user, course=course).exists()
   ```

2. **Упрощён `CourseSerializer`** - делегирование вычислений в service-функции:
   - `get_lessons_count()` теперь вызывает `calculate_lessons_count()`
   - `get_is_subscribed()` теперь вызывает `check_user_subscription()`
   - Сериализатор фокусируется только на сериализации данных
   - Добавлена защита от отсутствия request context (работает в admin, CLI, тестах)

3. **Существующие сервисы** (ранее реализованные):
   - ✅ `users/services.py` - Stripe интеграция, платежи, блокировка пользователей
   - ✅ `lms/services.py` - Email уведомления, подписки, Celery задачи

**Результаты:**

- ✅ **265 тестов** проходят (78 Django APITestCase + 187 pytest)
- ✅ **87.68% покрытие кода** (было 98.20% до рефакторинга с учетом расширения тестов)
- ✅ **100% покрытие** `lms/services.py` и `lms/serializers.py`
- ✅ **10 новых тестов** для service-функций и regression тестов сериализатора
- ✅ **Полная типизация** с Mypy (100% type coverage)

**Архитектурные улучшения:**

| Компонент | До рефакторинга | После рефакторинга |
|-----------|-----------------|-------------------|
| **Serializers** | Содержали бизнес-логику вычислений | Только сериализация данных |
| **ViewSets** | HTTP обработка + бизнес-логика | Только HTTP обработка |
| **Services** | Частичная реализация | Полная бизнес-логика |
| **Тестируемость** | Integration тесты через HTTP | Unit-тесты для чистых функций |
| **Переиспользование** | Дублирование логики | Одна функция — много мест использования |

**Польза от рефакторинга:**

- ✅ **Легче тестировать** - unit-тесты для чистых функций вместо integration-тестов
- ✅ **Переиспользование логики** - одна функция в разных местах (API, CLI, Celery tasks)
- ✅ **Четкое разделение ответственности** - Service Layer Pattern полностью реализован
- ✅ **Упрощение сериализаторов** - фокус на данных, а не вычислениях
- ✅ **Безопасность** - сериализатор работает даже без request context

**Следующий этап:** Docker-контейнеризация 🐳

---

### ⚡ Celery & Redis Integration (Асинхронные задачи)

**Статус:** ✅ **РЕАЛИЗОВАНО** (ноябрь 2025)

**Обзор:**

Проект использует Celery для асинхронной обработки задач и Redis в качестве message broker. Это позволяет выполнять длительные операции (отправка email, обработка данных) без блокировки HTTP-запросов и запускать периодические задачи по расписанию.

**Архитектура системы:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Celery Architecture                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Django     │         │    Redis     │         │   Celery     │
│  Web Server  │────────▶│   (Broker)   │◀────────│   Worker     │
│              │  Queue  │              │  Fetch  │              │
│              │  Task   │   Port 6379  │  Task   │              │
└──────────────┘         └──────────────┘         └──────────────┘
       │                                                  │
       │                                                  │
       ▼                                                  ▼
┌──────────────┐                                 ┌──────────────┐
│  PostgreSQL  │◀────────────────────────────────│  Execute     │
│   Database   │         Read/Write              │  Business    │
│              │                                 │  Logic       │
└──────────────┘                                 └──────────────┘
       ▲
       │
       │
┌──────────────┐         ┌──────────────┐
│ Celery Beat  │────────▶│   Schedule   │
│  Scheduler   │  Every  │  Periodic    │
│              │  Day    │  Tasks       │
└──────────────┘  3:00AM └──────────────┘
```

**Компоненты:**

| Компонент | Роль | Технология | Порт |
|-----------|------|------------|------|
| **Redis** | Message Broker - очередь задач | Redis 7 | 6379 |
| **Celery Worker** | Выполнение асинхронных задач | Celery 5.4.0 | - |
| **Celery Beat** | Планировщик периодических задач | django-celery-beat | - |
| **Django** | Создание задач (producer) | Django 5.2.7 | 8000 |
| **PostgreSQL** | Хранение данных и результатов | PostgreSQL 16 | 5432 |

**Текущая реализация:**

#### 1. **Email уведомления при обновлении курсов** 📧

**Файлы:**
- `lms/services.py` - `notify_course_subscribers()` - бизнес-логика отправки
- `lms/tasks.py` - `send_course_update_notification.delay()` - Celery задача
- `lms/views.py` - `CourseViewSet.perform_update()` - триггер при обновлении

**Поток работы:**
```
1. Пользователь обновляет курс через API (PUT/PATCH /api/courses/{id}/)
   │
   ▼
2. CourseViewSet.perform_update() сохраняет изменения в БД
   │
   ▼
3. Вызывается send_course_update_notification.delay(course.pk)
   │
   ▼
4. Задача помещается в Redis очередь
   │
   ▼
5. Celery Worker забирает задачу и выполняет notify_course_subscribers()
   │
   ▼
6. Сервис находит всех подписчиков курса
   │
   ▼
7. Проверка cooldown (не чаще 1 раза в 4 часа для каждого курса)
   │
   ▼
8. Отправка email всем подписчикам
   │
   ▼
9. Обновление last_notified в БД
```

**Защита от спама (Cooldown):**
- Email отправляется **не чаще 1 раза в 4 часа** для каждого курса
- Настройка через переменную окружения `EMAIL_NOTIFICATION_COOLDOWN_HOURS=4`
- Информация о последней отправке хранится в поле `Course.last_notified`

**Конфигурация:**
```python
# config/settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Dev
EMAIL_NOTIFICATION_COOLDOWN_HOURS = int(os.getenv('EMAIL_NOTIFICATION_COOLDOWN_HOURS', 4))
```

#### 2. **Периодическая блокировка неактивных пользователей** 🔒

**Файлы:**
- `users/services.py` - `block_inactive_users()` - бизнес-логика блокировки
- `users/tasks.py` - `block_inactive_users_task()` - Celery задача
- `config/celery.py` - расписание Celery Beat

**Расписание:**
```python
# config/celery.py
app.conf.beat_schedule = {
    'block-inactive-users-daily': {
        'task': 'users.tasks.block_inactive_users_task',
        'schedule': crontab(hour=3, minute=0),  # Каждый день в 3:00 UTC
    },
}
```

**Логика блокировки:**
- Задача запускается **каждый день в 3:00 UTC**
- Находит пользователей без логина > 30 дней (настраивается через `INACTIVE_USER_DAYS`)
- Устанавливает `is_active=False` для неактивных пользователей
- Возвращает количество заблокированных пользователей

**Конфигурация:**
```bash
# .env
INACTIVE_USER_DAYS=30  # Блокировать после 30 дней неактивности
```

**Service Layer Pattern:**

Все Celery задачи следуют паттерну **тонких оберток**:

```python
# lms/tasks.py (тонкая обертка)
@shared_task
def send_course_update_notification(course_id: int) -> dict[str, Any]:
    """Celery задача: отправить email уведомление подписчикам курса."""
    course = Course.objects.get(pk=course_id)
    return notify_course_subscribers(course)  # Делегирование в service

# lms/services.py (бизнес-логика)
def notify_course_subscribers(course: Course) -> dict[str, Any]:
    """Отправить email уведомление подписчикам курса с cooldown защитой."""
    # Вся бизнес-логика здесь
    ...
```

**Преимущества:**
- ✅ Легко тестировать сервисы без Celery
- ✅ Переиспользование логики вне задач
- ✅ Четкое разделение ответственности

**Покрытие тестами:**

| Модуль | Тесты | Покрытие |
|--------|-------|----------|
| `lms/services.py` | 15+ unit тестов | 100% |
| `lms/tasks.py` | 3 integration теста | 100% |
| `users/services.py` | 10+ unit тестов | 100% |
| `users/tasks.py` | 2 integration теста | 100% |

**Best Practices реализованные в проекте:**

1. **Идемпотентность задач** ✅
   - Задачи можно запускать многократно без побочных эффектов
   - Cooldown защита предотвращает дублирование email
   - Блокировка пользователей проверяет текущий статус

2. **Разделение ответственности** ✅
   - Задачи (`tasks.py`) - только Celery обертки
   - Сервисы (`services.py`) - вся бизнес-логика
   - ViewSets - только HTTP обработка

3. **Типизация и документация** ✅
   - Все функции имеют полные type hints
   - Docstrings на русском языке описывают поведение
   - Mypy проверяет типы на 100%

4. **Настраиваемость через окружение** ✅
   - `EMAIL_NOTIFICATION_COOLDOWN_HOURS` - частота уведомлений
   - `INACTIVE_USER_DAYS` - порог неактивности
   - Легко менять без изменения кода

5. **Graceful degradation** ✅
   - Если Redis недоступен, задачи просто не выполняются
   - Django продолжает работать
   - Email backend можно переключить (console/SMTP)

**Запуск Celery (локальная разработка):**

```bash
# 1. Запустить Redis
redis-server

# 2. Запустить Celery Worker
celery -A config worker --loglevel=info

# 3. Запустить Celery Beat (для периодических задач)
celery -A config beat --loglevel=info
```

**Мониторинг и отладка:**

```bash
# Проверить статус воркеров
celery -A config inspect active

# Посмотреть зарегистрированные задачи
celery -A config inspect registered

# Проверить расписание Beat
celery -A config inspect scheduled

# Отменить все задачи
celery -A config purge
```

**Troubleshooting:**

| Проблема | Причина | Решение |
|----------|---------|---------|
| Задачи не выполняются | Redis не запущен | `redis-server` или проверить `REDIS_URL` |
| Worker не видит задачи | Импорт не работает | Проверить `config/celery.py` автоимпорт |
| Beat не запускает задачи | Beat не запущен | Запустить `celery -A config beat` |
| Email не отправляются | Cooldown активен | Подождать 4 часа или изменить `EMAIL_NOTIFICATION_COOLDOWN_HOURS=0` |
| Задачи висят в очереди | Worker упал | Перезапустить worker, проверить логи |

**Переменные окружения:**

```bash
# .env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
EMAIL_NOTIFICATION_COOLDOWN_HOURS=4
INACTIVE_USER_DAYS=30
```

**Документация:**
- Подробная инструкция: [docs/CELERY_SETUP.md](docs/CELERY_SETUP.md)
- Примеры использования: `tests/lms/test_lms_tasks.py`, `tests/users/test_user_tasks.py`

**Следующие улучшения (опционально):**

- 🌸 **Flower** - веб-интерфейс для мониторинга Celery (порт 5555)
- 📊 **Result backend** - сохранение результатов задач в Redis/PostgreSQL
- 🔄 **Retry policies** - автоматическая повторная попытка при ошибках
- 📈 **Rate limiting** - ограничение количества задач в секунду
- 🔔 **Notifications** - уведомления о провалах задач

---

### ⚡ Оптимизация проекта (ноябрь 2025)

**Статус:** 🚧 В работе

**Цель:**
Улучшение производительности, уменьшение дублирования кода и оптимизация CI/CD pipeline для ускорения разработки.

**Основные направления:**

#### 1. Рефакторинг дублирования кода

**Проблема:**
- Дублирование логики URL-генерации в `users/services.py`
- `get_stripe_success_url()` и `get_stripe_cancel_url()` содержат идентичную логику определения протокола (http/https)

**Решение:**
- ✅ Создать `config/utils.py` с универсальной функцией `build_url(path: str) -> str`
- ✅ Вынести `SITE_DOMAIN` в `config/settings.py` для централизованной конфигурации
- ✅ Рефакторить `users/services.py` для использования новой утилиты
- ✅ Покрыть unit-тестами функцию `build_url()` (localhost и production сценарии)

**Польза:**
- Единая точка истины для URL-генерации
- Проще тестировать и поддерживать
- Переиспользование в других частях проекта

#### 2. Оптимизация CI/CD Pipeline

**Текущее состояние:**
- Test job: ~3-4 минуты (265 тестов последовательно)
- Lint job: ~2-3 минуты (ruff, black, mypy, isort, flake8 последовательно)
- Каждый раз устанавливаются зависимости заново

**Улучшения:**

**a) Кэширование Poetry dependencies:**
```yaml
- name: Cache Poetry dependencies
  uses: actions/cache@v3
  with:
    path: |
      ~/.cache/pypoetry
      .venv
    key: ${{ runner.os }}-poetry-${{ hashFiles('poetry.lock') }}
```

**Ожидаемая выгода:** Ускорение установки зависимостей с ~2 минут до ~30 секунд

**b) Параллельные тесты через pytest-xdist:**
```bash
pytest -n auto  # Автоматическое использование всех CPU
```

**Ожидаемая выгода:** Ускорение тестов в 2-4 раза (с ~4 минут до ~1-2 минут)

**c) Параллельный запуск lint проверок:**
```bash
ruff check . & \
black --check . & \
mypy . & \
isort --check-only . & \
flake8 . & \
wait
```

**Ожидаемая выгода:** Ускорение lint job с ~3 минут до ~1 минуты

**Итого:** Общее время CI/CD pipeline может сократиться с ~10 минут до ~3-4 минут ⚡

#### 3. Улучшение Docker Health Checks

**Текущее состояние:**
- PostgreSQL и Redis имеют health checks ✅
- Web service имеет HTTP health check ✅
- Celery worker и beat **не имеют** детальных health checks ❌

**Улучшения для docker-compose.prod.yml:**

**a) Health check для celery_worker:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "celery -A config inspect ping -d celery@$$HOSTNAME"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**b) Health check для celery_beat:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "celery -A config inspect scheduled || exit 1"]
  interval: 60s
  timeout: 10s
  retries: 3
  start_period: 30s
```

**c) Зависимости с condition: service_healthy:**
```yaml
web:
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy

celery_worker:
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
```

**Польза:**
- Предотвращение запуска сервисов до готовности зависимостей
- Более надежный deployment
- Автоматическое обнаружение проблем с Celery

#### 4. Унификация скриптов (опционально)

**Текущее состояние:**
- Дублирование скриптов: `scripts/unix/` и `scripts/windows/`
- Разные синтаксисы: bash (.sh) и PowerShell (.ps1)

**Решение:**
- Python-скрипты вместо shell для кроссплатформенности
- Уже есть `scripts/check.py` и `scripts/fix.py` ✅
- Расширить для других операций (test, watch, docker)

**Метрики успеха:**

| Метрика | До оптимизации | После оптимизации |
|---------|----------------|-------------------|
| **CI/CD время** | ~10 минут | ~3-4 минуты |
| **Дублирование кода** | 2 функции URL | 1 универсальная |
| **Тесты в CI** | Последовательно | Параллельно (x4) |
| **Lint проверки** | Последовательно | Параллельно (x5) |
| **Docker reliability** | Базовый | С health checks |

**Ожидаемые результаты:**
- ⚡ Быстрая обратная связь от CI (3-4 минуты вместо 10)
- 🔧 Чище и проще поддерживать код
- 🐳 Более надежный Docker deployment
- 📊 Сохранение высокого coverage (98.22%)

---

### 🐳 Docker Containerization

**Статус:** ✅ **ЗАВЕРШЁН** (ноябрь 2025)

**Цель:**
Контейнеризация всех компонентов приложения для воспроизводимого окружения разработки и упрощения deployment. На первом этапе фокусируемся на development окружении с Django dev server, затем переход на production с Gunicorn.

**Этапы реализации:**

| Этап | Описание | Статус |
|------|----------|--------|
| **Этап 1** | Docker для разработки (dev server) | 📋 Текущий приоритет |
| **Этап 2** | Production deployment (Gunicorn) | 🔮 Будущий этап |

**Архитектура Docker-окружения (Этап 1 - Development):**

```
┌─────────────────────────────────────────────────────┐
│                docker-compose.yaml                  │
└─────────────────────────────────────────────────────┘
           │
           ├─► 🐳 web (Django runserver)
           │   └─ Порт: 8000:8000
           │   └─ Команда: python manage.py runserver 0.0.0.0:8000
           │   └─ Зависит от: db, redis
           │
           ├─► 🐘 db (PostgreSQL 16)
           │   └─ Порт: 5433:5432 (избегание конфликта с локальным Postgres)
           │   └─ Volume: postgres_data
           │
           ├─► 🔴 redis (Redis 7-alpine)
           │   └─ Порт: 6379
           │   └─ Брокер для Celery
           │
           ├─► 👷 celery_worker
           │   └─ Обработка асинхронных задач
           │   └─ Зависит от: db, redis
           │
           └─► ⏰ celery_beat
               └─ Планировщик периодических задач
               └─ Зависит от: db, redis
```

**Компоненты для реализации (Этап 1):**

1. **Dockerfile** (multi-stage build)
   - Multi-stage build для оптимизации размера образа
   - Base stage: Python 3.12-slim, установка системных зависимостей
   - Builder stage: установка Poetry и Python зависимостей
   - Final stage: копирование только необходимых файлов
   - Non-root user для безопасности
   - HEALTHCHECK для проверки работоспособности

2. **docker-compose.yaml**
   - Сервисы: web (dev server), db, redis, celery_worker, celery_beat
   - Networks для изоляции сервисов
   - **Volumes для постоянного хранения:**
     - `postgres_data` - данные PostgreSQL (named volume, критично!)
     - `media_volume` - загруженные файлы (превью курсов/уроков, named volume)
     - `static` - статические файлы Django (после collectstatic)
     - `.:/code` - bind mount кода для live reload
   - Environment variables через .env файл
   - Health checks для зависимых сервисов
   - Restart policies для автовосстановления
   - **Команда web сервиса:** `python manage.py runserver 0.0.0.0:8000` (development mode)
   
   **Выбор образов Docker:**
   
   | Сервис | Образ | Обоснование |
   |--------|-------|-------------|
   | PostgreSQL | `postgres:16` | Стандартный образ (Debian-based) для лучшей совместимости и соответствия учебному материалу. Размер ~380MB. |
   | Redis | `redis:7-alpine` | Alpine образ (~30MB) достаточен для брокера сообщений, нет необходимости в расширениях. |
   | Python | `python:3.12-slim` | Slim образ (~120MB) - компромисс между размером и совместимостью. |
   
   **postgres:16 vs postgres:16-alpine:**
   - ✅ `postgres:16` (выбрано) - стандартный Debian-based образ, максимальная совместимость с расширениями, используется в большинстве учебных курсов
   - ⚡ `postgres:16-alpine` - минималистичный Alpine образ (~3x меньше), но могут быть проблемы с некоторыми расширениями
   
   Для production можно рассмотреть переход на Alpine, но для обучения рекомендуется стандартный образ.

3. **.env.example**
   - Шаблон переменных окружения для быстрого старта
   - Секреты: SECRET_KEY, DATABASE_URL, REDIS_URL, STRIPE_SECRET_KEY
   - Конфигурация: DEBUG, ALLOWED_HOSTS, CELERY_BROKER_URL
   - Настройки Celery: EMAIL_NOTIFICATION_COOLDOWN_HOURS, INACTIVE_USER_DAYS
   
   **Важно: Гибридный подход env_file + environment** 🔧
   
   В docker-compose.yaml используется **гибридный подход** для переменных окружения:
   
   ```yaml
   # docker-compose.yaml
   services:
     web:
       env_file: .env              # Подтягиваем ВСЕ переменные из .env
       environment:                 # Переопределяем Docker-специфичные
         POSTGRES_HOST: db         # В Docker используем имя сервиса
         REDIS_URL: redis://redis:6379/0
         CELERY_BROKER_URL: redis://redis:6379/0
   ```
   
   **Обоснование выбора:**
   
   | Подход | Плюсы | Минусы |
   |--------|-------|--------|
   | **Только env_file** | Простота, DRY | Неявность, нет контроля |
   | **Только environment** | Явность, документация | Дублирование, многословность |
   | **Гибридный (выбрано)** ✅ | Простота + контроль | Требует понимания приоритета |
   
   **Преимущества гибридного подхода:**
   - ✅ **Простота разработки** - один .env файл для локальной разработки И Docker
   - ✅ **Docker-специфичные настройки** - явно переопределены (db вместо localhost)
   - ✅ **Нет дублирования** - SECRET_KEY, STRIPE_KEY и т.д. в одном месте (.env)
   - ✅ **Гибкость** - легко переопределить отдельные переменные для Docker
   
   **Пример .env файла:**
   ```bash
   # .env (работает и локально, и в Docker)
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   STRIPE_SECRET_KEY=sk_test_...
   
   # Эти переменные переопределяются в docker-compose.yaml:
   POSTGRES_HOST=localhost  # → db в Docker
   REDIS_URL=redis://localhost:6379/0  # → redis://redis:6379/0 в Docker
   ```
   
   **Приоритет переменных:**
   1. `environment:` в docker-compose.yaml (наивысший)
   2. `env_file:` из .env файла
   3. Переменные окружения хоста (самый низкий)

4. **.dockerignore**
   - Исключения для оптимизации build: .git, __pycache__, *.pyc
   - Исключения файлов разработки: .env, venv, .vscode, .pytest_cache
   - Исключения тестовых данных: htmlcov, .coverage, test_db.sqlite3

5. **Документация и инструкции**
   - Инструкции по первоначальной настройке
   - Команды для запуска: `docker-compose up -d`
   - Выполнение миграций: `docker-compose exec web python manage.py migrate`
   - Создание суперпользователя: `docker-compose exec web python manage.py createsuperuser`
   - Загрузка fixtures: `docker-compose exec web python manage.py loaddata ...`
   - Остановка: `docker-compose down` / `docker-compose down -v` (с удалением volumes)
   - Troubleshooting: логи, пересборка образов, очистка volumes

#### 📦 Стратегия работы с данными (Fixtures)

**Цель:** Обеспечить воспроизводимость данных между окружениями (локальная разработка, Docker, production)

**Проблема:**
- При пересоздании Docker контейнера БД пустая
- Каждый разработчик видит разные данные
- Тестирование API без данных затруднено

**Решение через Fixtures:**

1. **Выгрузка актуальных данных из текущей БД:**
   ```bash
   # Курсы (включая preview paths)
   python manage.py dumpdata lms.Course --indent 2 > lms/fixtures/courses.json
   
   # Уроки
   python manage.py dumpdata lms.Lesson --indent 2 > lms/fixtures/lessons.json
   
   # Платежи
   python manage.py dumpdata users.Payment --indent 2 > users/fixtures/payments.json
   
   # Пользователи (опционально, без паролей)
   python manage.py dumpdata users.User --natural-foreign --indent 2 > users/fixtures/users.json
   
   # Подписки
   python manage.py dumpdata lms.Subscription --indent 2 > lms/fixtures/subscriptions.json
   ```

2. **Первый запуск Docker с загрузкой данных:**
   ```bash
   # Шаг 1: Запустить контейнеры
   docker-compose up -d
   
   # Шаг 2: Применить миграции
   docker-compose exec web python manage.py migrate
   
   # Шаг 3: Загрузить fixtures
   docker-compose exec web python manage.py loaddata lms/fixtures/courses.json
   docker-compose exec web python manage.py loaddata lms/fixtures/lessons.json
   docker-compose exec web python manage.py loaddata users/fixtures/payments.json
   docker-compose exec web python manage.py loaddata lms/fixtures/subscriptions.json
   
   # Шаг 4: Создать суперпользователя
   docker-compose exec web python manage.py createsuperuser
   
   # Готово! API доступен с демо-данными на http://localhost:8000/api/
   ```

3. **Media файлы (превью) — отдельное управление:**
   - Fixtures содержат **пути** к файлам (например: `preview: "courses/previews/python.jpg"`)
   - **Сами файлы** хранятся в `media/` директории
   - В Docker монтируется `media_volume` для постоянного хранения
   - При первом запуске можно скопировать существующие превью в контейнер:
     ```bash
     docker cp media/. lms_web:/code/media/
     ```

**Преимущества этого подхода:**

✅ **Воспроизводимость** — одинаковые данные в любом окружении  
✅ **Быстрый старт** — новый разработчик получает готовую БД за минуту  
✅ **Портативность** — проект работает на любой платформе с Docker  
✅ **Тестирование** — API всегда имеет реалистичные данные  
✅ **Изоляция** — каждый проект в своём контейнере, никаких конфликтов

**Обновление fixtures при изменении данных:**

```bash
# После добавления новых курсов/уроков в БД
python manage.py dumpdata lms.Course --indent 2 > lms/fixtures/courses.json
python manage.py dumpdata lms.Lesson --indent 2 > lms/fixtures/lessons.json

# Commit обновлённые fixtures в Git
git add lms/fixtures/*.json users/fixtures/*.json
git commit -m "docs: update fixtures with new courses"
```

#### 🧪 Тестирование в Docker

**Проект использует dual testing strategy:**
- **78 тестов** Django APITestCase (`lms/tests.py`, `users/tests.py`) — тестирование API endpoints
- **187 тестов** pytest-django (`tests/` директория) — unit/integration тесты services, models, tasks

**Запуск тестов в Docker:**

```bash
# Вариант 1: Единый скрипт для всех тестов (рекомендуется)
docker-compose exec web ./scripts/unix/test_all.sh
# Запускает 265 тестов + генерирует coverage отчёт (87.68%)

# Вариант 2: Через Makefile (упрощённый синтаксис, Linux/Mac/WSL)
make test-docker

# Вариант 3: Раздельный запуск
docker-compose exec web python manage.py test  # Django тесты (78)
docker-compose exec web poetry run pytest      # pytest тесты (187)
```

**Кросс-платформенная структура скриптов:**

Скрипты упорядочены по платформам для удобства:

```
scripts/
├── unix/              # Скрипты для Linux/Mac/WSL (bash)
│   ├── test_all.sh    # Все тесты + coverage
│   ├── check.sh       # Проверка качества кода
│   ├── fix.sh         # Автоисправление
│   └── watch.sh       # Watch-режим (автопроверка)
│
└── windows/           # Скрипты для Windows
    ├── test_all.bat   # CMD версия
    ├── test_all.ps1   # PowerShell версия
    ├── check.bat/ps1  # Проверка качества
    └── fix.bat/ps1    # Автоисправление
```

**Локальный запуск (вне Docker):**

**Linux / macOS / WSL:**
```bash
./scripts/unix/test_all.sh           # Все тесты
make test                             # Или через Makefile
```

**Windows CMD:**
```cmd
scripts\windows\test_all.bat         # Все тесты
```

**Windows PowerShell:**
```powershell
.\scripts\windows\test_all.ps1       # Все тесты
```

**Скрипт `test_all` выполняет:**

1. Django APITestCase тесты → coverage данные
2. pytest-django тесты → append к coverage
3. Генерация отчёта: `coverage report` + HTML в `htmlcov/`

> 📖 **Подробная инструкция**: [scripts/README.md](../scripts/README.md)

**Комбинированный coverage:**
```bash
docker-compose exec web bash -c "
  coverage run --source='users,lms,config' manage.py test && \
  coverage run --append --source='users,lms,config' -m pytest --no-cov && \
  coverage report
"
# Результат: 87.68% coverage (users, lms, config modules)
```

**Makefile команды для тестирования:**

| Команда | Описание |
|---------|----------|
| `make test` | Все тесты локально (Django + pytest) |
| `make test-docker` | Все тесты в Docker контейнере |
| `make check` | Code quality checks (ruff, mypy, flake8) |
| `make fix` | Auto-fix code style |

**pytest-django конфигурация** (из `pyproject.toml`):

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings_test"
addopts = [
    "-v",
    "--reuse-db",              # Переиспользует тестовую БД (быстрее)
    "--cov=users",
    "--cov=lms",
    "--cov=config",
    "--cov-report=html",
    "--cov-report=term-missing",
]
```

**Особенности тестирования в Docker:**

- ✅ **Изолированная тестовая БД** — создаётся автоматически в PostgreSQL контейнере
- ✅ **Переиспользование БД** — `--reuse-db` ускоряет повторные запуски
- ✅ **Одинаковое окружение** — тесты работают идентично на всех машинах
- ✅ **Фикстуры pytest-django** — `db`, `client`, `admin_user` доступны автоматически

**Troubleshooting:**

```bash
# Пересоздать тестовую БД (если тесты падают)
docker-compose exec web python manage.py test --keepdb=false

# Очистить coverage данные
docker-compose exec web coverage erase

# Запустить конкретный тест
docker-compose exec web pytest tests/lms/test_lms_services.py::test_calculate_lessons_count
```

6. **Проверка работоспособности сервисов**
   
   После запуска `docker-compose up -d` необходимо убедиться, что все сервисы работают корректно:
   
   ```bash
   # 1. Статус всех контейнеров (должны быть "Up")
   docker-compose ps
   
   # 2. Логи сервисов для диагностики
   docker-compose logs web        # Django dev server
   docker-compose logs db         # PostgreSQL
   docker-compose logs redis      # Redis
   docker-compose logs celery_worker  # Celery worker
   docker-compose logs celery_beat    # Celery beat
   
   # 3. Проверка Django приложения
   docker-compose exec web python manage.py check
   # Expected: "System check identified no issues"
   
   # 4. Проверка PostgreSQL
   docker-compose exec db psql -U lms_user -d lms_db -c "SELECT 1"
   # Expected: "1" (одна строка)
   
   # 5. Проверка Redis
   docker-compose exec redis redis-cli ping
   # Expected: "PONG"
   
   # 6. Проверка Celery worker
   docker-compose exec celery_worker celery -A config inspect ping
   # Expected: JSON с "ok: pong"
   
   # 7. HTTP проверка Django
   curl http://localhost:8000/api/
   # Expected: JSON ответ с API endpoints
   ```
   
   **Индикаторы успешного запуска:**
   - ✅ Все контейнеры в статусе "Up" (не "Restarting" или "Exit")
   - ✅ Django отвечает на HTTP запросы
   - ✅ PostgreSQL принимает SQL запросы
   - ✅ Redis отвечает на ping
   - ✅ Celery worker отзывается на inspect ping

**Важно: Персистентность данных PostgreSQL** ⚠️

Docker volumes критически важны для сохранения состояния базы данных:

**Проблема без volumes:**
- При `docker-compose down` все данные из PostgreSQL контейнера **ТЕРЯЮТСЯ**
- Каждый `docker-compose up` создает пустую БД
- Пользователи, курсы, платежи исчезают при перезапуске

**Решение - Named volumes:**
```yaml
# docker-compose.yaml
services:
  db:
    image: postgres:16  # Стандартный образ (не Alpine) для совместимости
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Монтируем volume
    environment:
      POSTGRES_DB: lms_db
      POSTGRES_USER: lms_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}

volumes:
  postgres_data:  # Определяем named volume (управляется Docker)
```

**Что происходит:**
1. Docker создает volume `postgres_data` в `/var/lib/docker/volumes/`
2. Данные PostgreSQL хранятся в этом volume, НЕ в контейнере
3. При остановке/удалении контейнера данные остаются в volume
4. При новом запуске контейнер монтирует тот же volume - данные на месте!

**Команды для работы с volumes:**
```bash
# Посмотреть все volumes
docker volume ls

# Инспектировать volume (узнать путь на хосте)
docker volume inspect <project>_postgres_data

# Backup базы данных
docker-compose exec db pg_dump -U lms_user lms_db > backup.sql

# Restore базы данных
cat backup.sql | docker-compose exec -T db psql -U lms_user lms_db

# ОПАСНО: Удалить volumes (потеря данных!)
docker-compose down -v
```

**Best practices для работы с volumes:**
- ✅ **Всегда используйте named volumes** для production данных
- ✅ **Регулярные backups** через `pg_dump` перед обновлениями
- ✅ **Bind mounts для разработки** (`./media:/app/media`) - файлы доступны на хосте
- ❌ **НЕ используйте** `-v` флаг при остановке production окружения
- ❌ **НЕ храните** критичные данные внутри контейнера (только в volumes)

**Польза Docker-контейнеризации:**
- ✅ **Воспроизводимость** - одинаковое окружение на dev/staging/production
- ✅ **Изоляция** - каждый сервис в своем контейнере
- ✅ **Быстрый старт** - `docker-compose up` поднимает всё окружение за минуты
- ✅ **Масштабируемость** - легко добавить реплики сервисов
- ✅ **CI/CD готовность** - образы можно использовать в пайплайнах
- ✅ **Team collaboration** - все разработчики работают в идентичном окружении

**Приоритет:** Высокий (следующий шаг после Service Layer ✅)

---

### 🔮 Этап 2: Production Deployment (Gunicorn)

**Статус:** 🔮 Будущий этап (после освоения Docker на занятиях)

**Когда реализовывать:** После успешного запуска Docker окружения с dev server и прохождения учебного материала по Gunicorn.

**Изменения для production:**

1. **Gunicorn** - Production WSGI сервер
   - Заменяет встроенный `runserver` Django
   - Многопроцессность для обработки concurrent запросов
   - Конфигурация: 4 воркера, timeout 120s, graceful reload
   - Команда: `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --reuse-port`

2. **Обновление docker-compose.yaml**
   ```yaml
   services:
     web:
       command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --reuse-port
       # Вместо: python manage.py runserver 0.0.0.0:5000
   ```

3. **Настройка статических файлов** ⚠️ **ВАЖНО**
   - В **development** с `runserver`: collectstatic НЕ нужен (Django раздаёт статику автоматически)
   - В **production** с Gunicorn: необходим `collectstatic` для сбора статики
   
   **Изменения в Dockerfile для production:**
   ```dockerfile
   # Добавить создание директории staticfiles с правильными правами
   RUN mkdir -p /app/staticfiles && \
       chown -R django:django /app/staticfiles
   ```
   
   **Раскомментировать в docker-entrypoint.sh:**
   ```bash
   echo "Collecting static files..."
   python manage.py collectstatic --noinput
   echo "✓ Static files collected"
   ```
   
   **Без этого получите:** `PermissionError: [Errno 13] Permission denied: '/app/staticfiles/css'`

4. **Дополнительные сервисы (опционально)**
   - **Flower** - веб-интерфейс для мониторинга Celery (порт 5555)
   - **Nginx** - reverse proxy для статических файлов
   - **Certbot** - автоматическое обновление SSL сертификатов

**Зависимости для добавления:**
```toml
[tool.poetry.dependencies]
gunicorn = "^22.0.0"  # Production WSGI server
```

**Польза Gunicorn:**
- ✅ **Стабильность** - обработка ошибок и graceful restart
- ✅ **Производительность** - многопроцессность, connection pooling
- ✅ **Production-ready** - используется в крупных проектах (Instagram, Pinterest)
- ✅ **Мониторинг** - детальные логи и метрики

---

### 🚀 Миграция на Docker-инфраструктуру (Полный переход)

**Цель:** Постепенный отказ от локального PostgreSQL и полный переход на Docker-based разработку

**Статус:** 📋 Запланировано (стратегический план)

**Обоснование:**
- 🎯 **Изоляция проектов** — каждый проект в своём контейнере с отдельной БД
- 🔄 **Воспроизводимость** — одинаковое окружение на любой ОС
- 🚀 **Портативность** — проект работает на любой платформе с Docker
- ✅ **Упрощение setup** — `docker-compose up` вместо установки PostgreSQL/Redis локально
- 🔒 **Соответствие production** — dev = prod окружение минимизирует сюрпризы при деплое

#### 📊 Сравнение workflow разработки

| Аспект | Локальная разработка | Docker разработка (🎯 Целевой) |
|--------|---------------------|-------------------------------|
| **Старт проекта** | `poetry run python manage.py runserver` | `docker-compose up` |
| **Тесты** | `poetry run pytest` | `docker-compose exec web poetry run pytest` |
| **Миграции** | `python manage.py migrate` | `docker-compose exec web python manage.py migrate` |
| **PostgreSQL** | Локальный на порту 5432 | Docker контейнер (5433→5432) |
| **Redis** | Локальный процесс | Docker контейнер |
| **Celery** | 3 отдельных процесса (worker, beat, Django) | 5 контейнеров (auto-restart) |
| **Изоляция между проектами** | ❌ Конфликты портов БД | ✅ Полная изоляция (named volumes) |
| **Скорость первого старта** | ✅ Мгновенно (если уже установлено) | ⚠️ ~2-3 минуты (build образов) |
| **Скорость перезапуска** | ✅ ~2 секунды | ✅ ~5 секунд |
| **Воспроизводимость** | ⚠️ Зависит от локального окружения | ✅ 100% воспроизводимо |
| **Требования** | PostgreSQL, Redis, Python установлены | Только Docker Desktop |
| **Управление зависимостями** | Poetry локально | Poetry в контейнере |
| **Логи** | Разрозненные в терминалах | Централизованные `docker-compose logs` |
| **Backup БД** | `pg_dump` локально | `docker-compose exec db pg_dump` |

**Вывод:** Docker предоставляет лучшую изоляцию и воспроизводимость за счёт минимальных накладных расходов на скорость.

---

#### 🗓️ План миграции по этапам

**Стратегия:** Поэтапный переход с сохранением работоспособности локальной разработки до полной стабилизации Docker.

---

##### **Этап 1: Подготовка Docker-инфраструктуры** 📋

**Цель:** Создать полностью работающее Docker окружение параллельно с локальной разработкой

**Статус:** 🔄 Текущий приоритет

**Задачи:**

1. **Создать Docker конфигурацию:**
   - `Dockerfile` с multi-stage build (Python 3.12-slim, Poetry, dependencies)
   - `docker-compose.yml` с 5 сервисами (web, db, redis, celery_worker, celery_beat)
   - `.dockerignore` для оптимизации build

2. **Настроить порты (избежать конфликтов):**
   ```yaml
   services:
     web:
       ports:
         - "8000:8000"  # Django dev server
     db:
       ports:
         - "5433:5432"  # PostgreSQL (локальный остаётся на 5432)
     redis:
       # Порт 6379 только внутри Docker network
   ```

3. **Создать named volumes:**
   ```yaml
   volumes:
     postgres_data:      # Данные PostgreSQL
     media_volume:       # Превью курсов/уроков
   ```

4. **Обновить fixtures:**
   - Выгрузить актуальные данные из локальной БД
   - Обновить `lms/fixtures/*.json` и `users/fixtures/*.json`
   - Скопировать media файлы (превью)

5. **Создать документацию:**
   - `docs/DOCKER_SETUP.md` — полная инструкция по setup
   - Обновить `README.md` с Docker Quick Start
   - Troubleshooting guide для частых проблем

**Критерии успеха:**
- ✅ `docker-compose up -d` запускает все 5 сервисов успешно
- ✅ Миграции применяются: `docker-compose exec web python manage.py migrate`
- ✅ Fixtures загружаются: `docker-compose exec web python manage.py loaddata`
- ✅ API отвечает на `http://localhost:8000/api/` с данными
- ✅ Celery worker обрабатывает задачи
- ✅ Тесты проходят: `docker-compose exec web poetry run pytest` (265 тестов, 87.68%)

**Риски и митигация:**
- ⚠️ **Проблема:** Build занимает много времени
  - **Решение:** Использовать Docker layer caching, оптимизировать порядок COPY в Dockerfile
- ⚠️ **Проблема:** Volumes не сохраняют данные
  - **Решение:** Проверить маппинг `postgres_data:/var/lib/postgresql/data`, убедиться что не используется `-v` флаг

**Длительность:** ~1-2 дня разработки + тестирования

---

##### **Этап 2: Параллельная работа (переходный период)** 🔄

**Цель:** Команда тестирует Docker окружение, но локальная разработка остаётся доступной как fallback

**Статус:** 🔮 Следующий этап

**Задачи:**

1. **Двойное тестирование:**
   - Запускать тесты и локально, и в Docker
   - Сравнивать производительность и стабильность
   - Выявлять проблемы Docker setup

2. **Обновить CI/CD (если есть):**
   - Переключить пайплайны на Docker
   - Использовать `docker-compose run web pytest` в GitHub Actions/GitLab CI

3. **Документация для команды:**
   - Написать guide по переключению между окружениями
   - FAQ по частым проблемам Docker
   - Видео-tutorial для новых разработчиков

4. **Мониторинг стабильности:**
   - Логировать проблемы с Docker
   - Собирать feedback от команды
   - Итеративно улучшать конфигурацию

**Критерии успеха:**
- ✅ Все разработчики могут запустить Docker окружение
- ✅ Docker тесты проходят стабильно
- ✅ Производительность приемлема (перезапуск <10 секунд)
- ✅ Нет критических blocker-ов в Docker workflow

**Риски и митигация:**
- ⚠️ **Проблема:** Разработчики предпочитают локальную разработку из-за привычки
  - **Решение:** Провести workshop по Docker преимуществам, показать реальные кейсы изоляции
- ⚠️ **Проблема:** Docker Desktop тормозит на старых машинах
  - **Решение:** Оптимизировать ресурсы (2 CPU, 4GB RAM минимум), использовать volume caching

**Длительность:** ~1-2 недели параллельной работы

---

##### **Этап 3: Полная миграция (Docker как primary)** 🎯

**Цель:** Docker становится единственным рекомендованным способом разработки

**Статус:** 🔮 Будущий этап

**Задачи:**

1. **Обновить всю документацию:**
   - README.md — Docker Quick Start как основная секция
   - Локальная разработка помечается как "Legacy / Alternative"
   - Убрать инструкции по установке PostgreSQL/Redis локально из главных docs

2. **Переключить onboarding:**
   - Новые разработчики начинают с Docker setup
   - Checklist: установить Docker Desktop → clone repo → `docker-compose up` → готово

3. **Обновить скрипты и команды:**
   - `scripts/test.sh` → вызывает `docker-compose exec web poetry run pytest`
   - `scripts/migrate.sh` → вызывает `docker-compose exec web python manage.py migrate`
   - Все helper скрипты переключены на Docker

4. **Архивировать локальные конфигурации:**
   - Создать `docs/legacy/LOCAL_SETUP.md` для тех, кто хочет локальную разработку
   - Основная документация только про Docker

**Критерии успеха:**
- ✅ 100% команды работает в Docker
- ✅ Все CI/CD пайплайны на Docker
- ✅ Документация обновлена (Docker primary, локальное legacy)
- ✅ Новые разработчики стартуют с Docker без вопросов

**Риски и митигация:**
- ⚠️ **Проблема:** Некоторые разработчики не хотят переходить
  - **Решение:** Soft mandate — показать преимущества, не блокировать локальную работу жёстко
- ⚠️ **Проблема:** Специфичные edge-cases не работают в Docker
  - **Решение:** Документировать workaround-ы, возможно патчить docker-compose.yml

**Длительность:** ~1 неделя обновления документации + переход команды

---

##### **Этап 4: Очистка и оптимизация** 🧹

**Цель:** Удалить legacy код и конфигурации, оптимизировать Docker setup

**Статус:** 🔮 Финальный этап

**Задачи:**

1. **Удалить локальные конфигурации из основных docs:**
   - Убрать секции про локальную установку PostgreSQL из README.md
   - Переместить в `docs/legacy/` если нужно сохранить для истории
   - Обновить `replit.md` (удалить упоминания локального Postgres)

2. **Оптимизация Docker:**
   - Multi-stage build для уменьшения размера образа
   - Docker layer caching в CI/CD
   - Health checks для auto-restart проблемных контейнеров

3. **Автоматизация:**
   - `make docker-start` → `docker-compose up -d && loaddata`
   - `make docker-test` → запуск тестов в контейнере
   - `make docker-shell` → интерактивный shell в контейнере

4. **Production readiness (опционально):**
   - Переключение на Gunicorn (Этап 2 Docker)
   - Настройка Nginx для статики
   - SSL сертификаты через Certbot

**Критерии успеха:**
- ✅ Документация чистая и содержит только Docker workflow
- ✅ Build образа оптимизирован (<2 минуты first build)
- ✅ Автоматизированы частые команды (Makefile/scripts)
- ✅ Zero упоминаний локального PostgreSQL в основной документации

**Риски и митигация:**
- ⚠️ **Проблема:** Потеря исторических знаний о локальном setup
  - **Решение:** Сохранить в `docs/legacy/` с пометкой "deprecated"
- ⚠️ **Проблема:** Новые проблемы появляются после удаления fallback
  - **Решение:** Мониторинг в течение месяца, быстрые hotfix-ы

**Длительность:** ~2-3 дня очистки + неделя мониторинга

---

#### 📈 Ожидаемые выгоды после полной миграции

**Для разработчиков:**
- ✅ Быстрый onboarding новых членов команды (~5 минут setup)
- ✅ Нет конфликтов портов между проектами
- ✅ Одинаковое окружение у всех (нет "works on my machine")
- ✅ Простой переход между проектами (разные docker-compose.yml)

**Для проекта:**
- ✅ Портативность — работает на любой платформе с Docker
- ✅ CI/CD готовность — образы используются в пайплайнах
- ✅ Масштабируемость — легко добавить реплики сервисов
- ✅ Соответствие production — минимум различий между dev и prod

**Метрики успеха:**
- 🎯 **Время setup для нового разработчика:** с 2 часов → 5 минут
- 🎯 **Количество "works on my machine" проблем:** -80%
- 🎯 **Время переключения между проектами:** с 10 минут → 30 секунд

---

## Архитектура системы

### Структура приложения

```
lms/
├── models.py           # Модели данных
├── serializers.py      # DRF сериализаторы (планируется)
├── views.py           # ViewSets для API (планируется)
├── urls.py            # URL routing (планируется)
├── services.py        # Бизнес-логика (планируется)
├── permissions.py     # Права доступа (планируется)
├── tasks.py           # Celery задачи (планируется)
└── migrations/        # Миграции БД
```

### Принципы разработки

**Архитектурные стандарты проекта:**
- TDD подход (RED-GREEN-REFACTOR)
- 100% type coverage (mypy)
- 100% test coverage (pytest)
- Композиция через миксины
- Service Layer Pattern
- Pydantic валидация

---

## Модели системы

### ✅ Реализованные модели

#### 1. Course (Курс) - Базовая версия

**Статус:** ✅ **Реализована** (базовая функциональность)

**Поля (реализованы):**
```python
class Course(BaseModel):
    # Основная информация
    owner: models.ForeignKey            # ✅ Владелец курса (User)
    title: models.CharField              # ✅ Название курса
    description: models.TextField        # ✅ Описание курса
    preview: models.ImageField          # ✅ Превью изображение
    last_notification_sent: models.DateTimeField  # ✅ Cooldown для email уведомлений
    
    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["-created_at"]
```

**⏳ Планируется добавить:**
- `author_name` - Имя автора для отображения
- `price`, `currency` - Ценообразование
- `status`, `published_at` - Статус публикации
- `category`, `tags` - Категоризация
- `students_count`, `rating` - Статистика

#### 2. Lesson (Урок) - Базовая версия

**Статус:** ✅ **Реализована** (базовая функциональность)

**Поля (реализованы):**
```python
class Lesson(BaseModel):
    # Принадлежность
    owner: models.ForeignKey            # ✅ Владелец урока (User)
    course: models.ForeignKey           # ✅ Курс
    
    # Основная информация
    title: models.CharField             # ✅ Название урока
    description: models.TextField       # ✅ Описание
    preview: models.ImageField          # ✅ Превью урока
    
    # Контент
    video_url: models.URLField          # ✅ URL видео (YouTube, Vimeo)
    
    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["course", "id"]
```

**⏳ Планируется добавить:**
- `order` - Порядковый номер урока
- `duration` - Длительность видео
- `transcript` - Текстовая расшифровка
- `materials` - Дополнительные материалы
- `is_preview` - Доступен для предпросмотра

---

#### 4. Subscription (Подписка на курс) - Базовая версия

**Статус:** ✅ **Реализована** (базовая функциональность)

**Поля (реализованы):**
```python
class Subscription(BaseModel):
    # Связи
    user: models.ForeignKey             # ✅ Пользователь
    course: models.ForeignKey           # ✅ Курс
    
    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = [["user", "course"]]
```

**⏳ Планируется добавить:**
- `started_at`, `expires_at` - Сроки подписки
- `status` - Статус (active, expired, cancelled)
- `payment` - Связь с платежом

#### 5. Payment (Платеж) - Базовая версия

**Статус:** ✅ **Реализована** (базовая функциональность)

**Поля (реализованы):**
```python
class Payment(BaseModel):
    # Связи
    user: models.ForeignKey             # ✅ Плательщик
    course: models.ForeignKey           # ✅ Оплаченный курс (nullable)
    lesson: models.ForeignKey           # ✅ Оплаченный урок (nullable)
    
    # Сумма
    payment_amount: models.DecimalField # ✅ Сумма платежа
    
    # Платежная система
    payment_method: models.CharField    # ✅ Способ оплаты (cash, transfer, stripe)
    stripe_session_id: models.CharField # ✅ ID Stripe Checkout Session
    stripe_payment_status: models.CharField  # ✅ Статус оплаты в Stripe
    
    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
```

**⏳ Планируется добавить:**
- `currency` - Поддержка разных валют
- `status` - Унифицированный статус (pending, completed, failed, refunded)
- `transaction_id` - Универсальный ID транзакции

---

### ⏳ Планируемые модели (не реализованы)

#### 1. CourseReview (Отзыв о курсе)

**Описание:** Отзывы студентов о курсе

**Поля:**
```python
class CourseReview(BaseModel):
    # Связи
    user: models.ForeignKey             # Автор отзыва
    course: models.ForeignKey           # Курс
    
    # Оценка
    rating: models.IntegerField         # Оценка 1-5
    
    # Отзыв
    title: models.CharField             # Заголовок
    text: models.TextField              # Текст отзыва
    
    # Модерация
    is_approved: models.BooleanField    # Одобрен модератором
    
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = [['user', 'course']]
```

**Методы:**
- `approve()` - одобрить отзыв
- `calculate_helpfulness()` - полезность отзыва

#### 2. LessonProgress (Прогресс изучения)

**Статус:** ⏳ **НЕ реализована** (не требовалась заданием курса)

**Описание:** Прогресс пользователя по урокам

**Планируемые поля:**
```python
class LessonProgress(BaseModel):
    # Связи
    user: models.ForeignKey             # Пользователь
    lesson: models.ForeignKey           # Урок
    
    # Прогресс
    is_completed: models.BooleanField   # Завершен ли урок
    watch_percentage: models.IntegerField # Процент просмотра (0-100)
    last_position: models.IntegerField  # Последняя позиция в секундах
    
    # Даты
    started_at: models.DateTimeField    # Начало просмотра
    completed_at: models.DateTimeField  # Завершение (null если не завершен)
    
    class Meta:
        verbose_name = "Прогресс урока"
        verbose_name_plural = "Прогресс уроков"
        unique_together = [['user', 'lesson']]
```

**Планируемые методы:**
- `mark_completed()` - отметить завершенным
- `update_progress(position)` - обновить позицию
- `get_course_progress()` - прогресс по всему курсу

---

## API Endpoints

### Планируемые REST API endpoints

#### Courses

```
GET    /api/v1/courses/              # Список всех курсов
POST   /api/v1/courses/              # Создать курс (только владелец)
GET    /api/v1/courses/{id}/         # Детали курса
PUT    /api/v1/courses/{id}/         # Обновить курс (только владелец)
PATCH  /api/v1/courses/{id}/         # Частичное обновление
DELETE /api/v1/courses/{id}/         # Удалить курс (только владелец)

GET    /api/v1/courses/{id}/lessons/ # Уроки курса
POST   /api/v1/courses/{id}/enroll/  # Записаться на курс
GET    /api/v1/courses/{id}/reviews/ # Отзывы о курсе
```

#### Lessons

```
GET    /api/v1/lessons/              # Список уроков (с фильтрацией)
POST   /api/v1/lessons/              # Создать урок (только владелец курса)
GET    /api/v1/lessons/{id}/         # Детали урока
PUT    /api/v1/lessons/{id}/         # Обновить урок
DELETE /api/v1/lessons/{id}/         # Удалить урок

POST   /api/v1/lessons/{id}/complete/ # Отметить урок завершенным
POST   /api/v1/lessons/{id}/progress/ # Обновить прогресс
```

#### Subscriptions

```
GET    /api/v1/subscriptions/        # Мои подписки
POST   /api/v1/subscriptions/        # Создать подписку (после оплаты)
GET    /api/v1/subscriptions/{id}/   # Детали подписки
DELETE /api/v1/subscriptions/{id}/   # Отменить подписку
```

#### Payments

```
GET    /api/v1/payments/             # История платежей
POST   /api/v1/payments/             # Создать платеж
GET    /api/v1/payments/{id}/        # Детали платежа
POST   /api/v1/payments/{id}/refund/ # Возврат платежа
```

#### Reviews

```
GET    /api/v1/reviews/              # Все отзывы (с фильтрацией)
POST   /api/v1/reviews/              # Создать отзыв
GET    /api/v1/reviews/{id}/         # Детали отзыва
PUT    /api/v1/reviews/{id}/         # Обновить отзыв
DELETE /api/v1/reviews/{id}/         # Удалить отзыв
```

### Сериализаторы

```python
# Планируемые DRF сериализаторы

CourseSerializer              # Базовая сериализация курса
CourseDetailSerializer        # Детальная с уроками
CourseCreateSerializer        # Создание курса
CourseUpdateSerializer        # Обновление курса

LessonSerializer              # Базовая сериализация урока
LessonDetailSerializer        # Детальная с прогрессом
LessonCreateSerializer        # Создание урока

SubscriptionSerializer        # Подписка
PaymentSerializer             # Платеж
ReviewSerializer              # Отзыв
ProgressSerializer            # Прогресс
```

---

## Бизнес-логика

### 1. Подписка на курс

**Сценарий:**
1. Пользователь выбирает курс
2. Создается платеж (Payment) со статусом `pending`
3. Пользователь оплачивает через платежную систему
4. При успешной оплате:
   - Payment.status = `completed`
   - Создается Subscription со статусом `active`
   - Отправляется email с подтверждением
5. Пользователь получает доступ к урокам

**Права доступа:**
- Только подписанные пользователи видят контент уроков
- Уроки с `is_preview=True` видны всем

---

### 2. Прогресс обучения

**Отслеживание:**
- При просмотре видео сохраняется позиция каждые N секунд
- При достижении 90% - урок считается завершенным
- Прогресс по курсу = завершенные уроки / всего уроков

**Геймификация (будущее):**
- Достижения за завершение курсов
- Сертификаты о прохождении
- Бейджи за активность

---

### 3. Рейтинги и отзывы

**Правила:**
- Отзыв может оставить только студент с активной подпиской
- Один отзыв на курс от одного пользователя
- Рейтинг курса = среднее арифметическое всех оценок
- Отзывы проходят модерацию перед публикацией

---

### 4. Права доступа

**Роли:**

**Студент (обычный пользователь):**
- Просмотр курсов
- Покупка/подписка на курсы
- Просмотр уроков (только купленных курсов)
- Оставление отзывов
- Отслеживание прогресса

**Владелец курса (преподаватель):**
- Все права студента +
- Создание/редактирование своих курсов
- Создание/редактирование уроков в своих курсах
- Просмотр статистики по своим курсам

**Модератор (is_staff):**
- Все права владельца +
- Модерация отзывов
- Просмотр всех курсов

---

## Будущие интеграции

### Платежные системы

**Приоритет 1: Stripe**
- Прием платежей по картам
- Автоматические подписки
- Webhooks для обработки платежей

**Приоритет 2: PayPal**
- Альтернативный способ оплаты
- Международные платежи

### Email уведомления

**События для отправки:**
- Успешная регистрация
- Покупка курса
- Завершение курса
- Истечение подписки
- Новый урок в купленном курсе

**Сервисы:**
- SendGrid или Mailgun
- Шаблоны писем на русском языке

### Видео хостинг

**Варианты:**
- YouTube (бесплатно, но ограничения)
- Vimeo (платно, но профессионально)
- Собственный CDN (дорого, полный контроль)

**Функции:**
- Защита от скачивания
- Адаптивное качество
- Субтитры

### Аналитика

**Метрики:**
- Популярность курсов
- Конверсия просмотр → покупка
- Средний прогресс по курсам
- Время на платформе

**Инструменты:**
- Google Analytics
- Mixpanel или Amplitude
- Собственная аналитика в Django Admin

### Социальные функции

**Будущие возможности:**
- Форум для обсуждения уроков
- Q&A с преподавателем
- Групповые задания
- Сертификаты LinkedIn

### Инфраструктура и оптимизация

**Приоритет: Средний** (после базового функционала)

**Workflows для среды разработки:**
- Параллельный запуск Redis Server через Workflow (пример: Replit Workflows)
- Celery Worker через Workflow для асинхронных задач
- Celery Beat через Workflow для периодических задач
- Управление и мониторинг всех сервисов в едином интерфейсе
- **Альтернатива:** переход на process-compose или Docker Compose

**Django кэширование через Redis:**
- Интеграция Redis для кэширования (база данных №1, отдельная от Celery)
- Кэширование результатов запросов для оптимизации производительности
- Session storage через Redis для масштабируемости
- Template fragment caching для сложных view
- Low-level cache API для custom кэширования
- Production-ready оптимизация: снижение нагрузки на PostgreSQL

**Оптимизация .gitignore и .dockerignore:**
- Анализ текущего состояния: выявление дублирования между файлами
- Рациональное разделение ответственности:
  - `.gitignore` — что не коммитить в Git репозиторий (IDE настройки, секреты, временные файлы)
  - `.dockerignore` — что не копировать в Docker образ (тесты, документация, dev-зависимости)
- Устранение избыточного дублирования (файлы которые нужны в обоих)
- Документация различий и обоснование включенных/исключенных файлов
- Оптимизация размера Docker образа через исключение ненужных файлов
- Приоритет: Низкий (не влияет на функционал, но улучшает поддерживаемость)

**Этапы миграции инфраструктуры:**
1. **Текущий этап (Development):** Workflows для параллельного запуска сервисов (примеры: Replit, PM2, supervisord)
2. **Промежуточный (Staging/Docker):** process-compose для локальной Docker разработки
3. **Финальный (Production):** полный переход на Docker Compose для production deployment

---

## Порядок реализации

### ✅ Фаза 1: MVP (Minimum Viable Product) - ЗАВЕРШЕНА

1. ✅ Базовая структура проекта
2. ✅ User модель с email-авторизацией
3. ✅ **Course модель** с полями (базовая функциональность)
4. ✅ **Lesson модель** с полями (базовая функциональность)
5. ✅ **DRF API** для Course и Lesson (ViewSet + Generic Views)
6. ✅ **Базовые права доступа** (IsOwner, IsNotModerator, IsModeratorOrOwner, IsSelf)

### ✅ Фаза 2: Монетизация - ЗАВЕРШЕНА

7. ✅ Subscription модель (базовая функциональность)
8. ✅ Payment модель (cash, transfer, Stripe)
9. ✅ Интеграция Stripe (Checkout Session, Payment Status)
10. ✅ Email уведомления (Celery tasks, cooldown для курсов)

### ⏳ Фаза 3: Вовлечение - НЕ РЕАЛИЗОВАНА (не требовалась заданием курса)

11. ⏳ CourseReview модель
12. ⏳ LessonProgress модель
13. ⏳ Сертификаты о прохождении
14. ⏳ Рекомендательная система

---

## Backlog / Отложенные задачи

### Роль "Казначей" для управления платежами

**Статус:** 🔮 Backlog (будущая реализация)

**Контекст:**
В текущей версии система использует упрощенную модель доступа к платежам:
- Каждый пользователь видит и управляет только своими платежами
- Нет специализированных ролей для финансового контроля

**Описание задачи:**
Добавить роль "Казначей" с расширенными правами для управления финансами:

**Функциональность:**
- **Полный доступ к платежам**: Казначей видит все платежи всех пользователей
- **CRUD операции**: Создание, редактирование, удаление любых платежей
- **Просмотр пользователей**: Доступ к списку пользователей для связывания с платежами
- **Финансовая отчетность**: Экспорт отчетов, статистика по платежам

**Требования перед реализацией:**

1. **Бизнес-процессы:**
   - Описать workflow для работы казначея
   - Определить сценарии использования (создание платежей, корректировки, возвраты)
   - Разграничить права между казначеем и администратором

2. **Безопасность:**
   - Аудит всех действий казначея (логирование изменений)
   - Двухфакторная аутентификация для роли казначея
   - Защита от случайного удаления/изменения платежей

3. **Техническая реализация:**
   - Permission класс `IsTreasurer` (проверка группы "Казначеи")
   - Permission класс `IsPaymentOwnerOrTreasurer` (владелец ИЛИ казначей)
   - Обновление `PaymentViewSet.get_queryset()` - фильтрация для казначея
   - Группа Django "Казначеи" через fixtures

4. **Тестирование:**
   - Unit-тесты для permissions
   - API тесты для доступа казначея к чужим платежам
   - Тесты безопасности (обычный пользователь не может стать казначеем)

**Приоритет:** Низкий (реализовывать только при явной бизнес-потребности)

**Зависимости:** Требуется четкое понимание бизнес-требований и процессов

**Альтернативы:**
- Использовать Django Admin для управления платежами администраторами
- Создать отдельный dashboard для финансового отдела

---

**Дата создания:** 27 октября 2025  
**Версия:** 1.3.4  
**Последнее обновление:** 18 ноября 2025  

**История изменений:**

**v1.3.4** (18 ноября 2025):
- 🐳 Финализация Docker Compose setup: production-ready конфигурация с 5 сервисами
- 🔧 Исправлена интеграция .env и config/settings.py: POSTGRES_*, CELERY_*, EMAIL_BACKEND читаются из окружения
- 📝 Реализована поддержка локальной разработки (localhost) и Docker окружения через единый .env файл
- 🗺️ Roadmap: добавлена секция "Инфраструктура и оптимизация" с задачами по Workflows и Redis кэшированию
- 🔄 Docker Compose переопределяет переменные окружения для контейнеров (POSTGRES_HOST=db, CELERY_*=redis://redis:6379/0)
- ✅ Docker setup готов к локальному запуску (работает на любой ОС с Docker Desktop/Engine)
- 🚀 Roadmap обновлен: этапы миграции инфраструктуры (Development Workflows → Staging/Docker → Production)

**v1.3.3** (18 ноября 2025):
- 📂 Реорганизация скриптов по платформам: `scripts/unix/` и `scripts/windows/`
- 🪟 Добавлены кросс-платформенные версии скриптов: `.sh`, `.bat` (CMD), `.ps1` (PowerShell)
- 📝 Создан `scripts/README.md` с подробными инструкциями для каждой платформы
- 🔄 Обновлена документация (README.md, roadmap) с кросс-платформенными примерами
- ✅ Кросс-платформенная поддержка: одинаковый функционал для всех ОС

**v1.3.2** (18 ноября 2025):
- 🧪 Создан `scripts/test_all.sh` — единый скрипт для запуска всех 265 тестов с coverage
- 📦 Добавлен `Makefile` с короткими командами: test, test-docker, check, fix, docker-*
- 📝 Добавлена подсекция "🧪 Тестирование в Docker" в roadmap с примерами команд
- 📖 Обновлён README.md: секция тестирования теперь включает Makefile и scripts/test_all.sh
- ✅ Упрощён workflow: `make test` вместо длинной команды coverage

**v1.3.1** (18 ноября 2025):
- 🔧 Актуализирована секция "📸 Превью изображения в демо-данных" — исправлено противоречие
- ✅ Подтверждено что fixtures содержат пути к превью (реализовано 27 октября)
- 📝 Обновлён статус секции с устаревшей информации на актуальное состояние

**v1.3** (18 ноября 2025):
- Обновлена архитектура Docker: порты Django 8000:8000, PostgreSQL 5433:5432 (избежание конфликта)
- Добавлены named volumes: `media_volume` для превью, `postgres_data` для БД
- Новая подсекция "📦 Стратегия работы с данными (Fixtures)" с полным workflow
- **Новая секция:** "🚀 Миграция на Docker-инфраструктуру (Полный переход)"
  - 4 этапа миграции: Подготовка → Параллельная работа → Полная миграция → Очистка
  - Сравнительная таблица workflow (локальная vs Docker разработка)
  - Детальное описание каждого этапа с критериями успеха, рисками и длительностью
  - Метрики успеха и ожидаемые выгоды

**v1.2** (18 ноября 2025):
- Завершён рефакторинг Service Layer (265 тестов, 87.68% покрытие)
- Добавлена comprehensive документация Celery & Redis Integration
- Обновлена Docker секция: разделение на Development (Этап 1) и Production (Этап 2)
