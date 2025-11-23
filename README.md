# 🎓 LMS (Learning Management System) - Django REST Framework

> Платформа для онлайн-обучения с REST API на базе Django 5.2.7 и Django REST Framework

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16.1-red.svg)](https://www.django-rest-framework.org/)
[![Tests](https://img.shields.io/badge/Tests-265%20passed-success.svg)](.)
[![Code Coverage](https://img.shields.io/badge/Coverage-98.22%25-brightgreen.svg)](.)
[![Type Coverage](https://img.shields.io/badge/Type%20Coverage-100%25-success.svg)](.)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](.github/workflows/ci-cd.yml)

## 📋 Описание

LMS система — это backend-сервер для платформы онлайн-обучения, предоставляющий RESTful API для управления пользователями, курсами, уроками, подписками и платежами. Проект разработан с использованием современных практик разработки:

- ✅ **Comprehensive Testing** — все функции покрыты тестами (**265 тестов, 98.22% покрытие**)
- ✅ **100% Type Coverage** — полная типизация с Mypy (58 файлов)
- ✅ **Строгие стандарты кода** — Ruff, Black, isort, Flake8
- ✅ **CI/CD Pipeline** — автоматическое тестирование, сборка Docker образов и deployment через GitHub Actions
- ✅ **PostgreSQL** — надежная реляционная база данных с демо-данными
- ✅ **Email-авторизация** — современная аутентификация через email + JWT
- ✅ **API Документация** — Swagger UI + ReDoc через drf-spectacular
- ✅ **Stripe интеграция** — полная поддержка онлайн-платежей с автоматическим созданием сессий
- ✅ **Celery + Redis** — асинхронные задачи и периодические уведомления
- ✅ **Оптимизация запросов** — использование select_related и prefetch_related
- ✅ **Фильтрация и пагинация** — Django Filter + кастомная пагинация
- ✅ **Валидация данных** — YouTube URL валидатор для безопасности контента
- ✅ **Система подписок** — пользователи могут подписываться на обновления курсов

## 🛠 Технологический стек

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | 3.12 | Основной язык программирования |
| Django | 5.2.7 | Web-фреймворк |
| Django REST Framework | 3.16.1 | REST API |
| drf-spectacular | Latest | OpenAPI 3.0 документация |
| Django Filter | 25.2 | Фильтрация и сортировка API |
| django-cors-headers | 4.9.0 | CORS middleware |
| Stripe | 13.2.0 | Платежная интеграция |
| PostgreSQL | Latest | База данных |
| Redis | Latest | Message broker для Celery |
| Celery | 5.4.0 | Асинхронные задачи |
| django-celery-beat | Latest | Периодические задачи |
| Poetry | Latest | Управление зависимостями |
| Pytest | 8.4.2 | Тестирование |
| Mypy | 1.17.1 | Проверка типов |
| Ruff | 0.14.2 | Линтер |
| Black | 25.1.0 | Форматирование кода |

## ✨ Возможности

### 👥 Управление пользователями
- Регистрация с email вместо username
- CRUD операции для профилей пользователей
- Поля: email, имя, фамилия, телефон, город, аватар
- Безопасное хеширование паролей
- Публичные и детальные профили (PublicUserSerializer, UserDetailSerializer)

### 📚 Система обучения (LMS)
- **Курсы**: название, описание, превью-изображение, владелец
  - Количество уроков (`lessons_count`)
  - Вложенная информация по всем урокам
  - Статус подписки пользователя (`is_subscribed`)
- **Уроки**: название, описание, превью, ссылка на видео (только YouTube!)
  - Валидация YouTube URL через кастомный валидатор
- **Подписки**: система уведомлений об обновлениях курсов
  - Toggle endpoint для подписки/отписки
  - Уникальное ограничение user+course
- Связь курс-уроки (один курс → много уроков)
- Каскадное удаление
- Оптимизированные запросы (решение проблемы N+1)
- **Пагинация**: настраиваемый размер страницы (default: 10, max: 100)

### 💳 Платежная система
- Модель Payment для учёта платежей за курсы и уроки
- Поля: пользователь, дата платежа, курс/урок, сумма, способ оплаты (наличные/перевод/**Stripe**)
- **Stripe интеграция**:
  - Автоматическое создание продукта и цены в Stripe
  - Генерация checkout-сессии с ссылкой на оплату (`payment_link`)
  - Сохранение `stripe_session_id` для отслеживания статуса
  - Custom action `/check_status/` для проверки статуса платежа в реальном времени
  - Сервисный слой (`users/services.py`) с простыми функциями для работы с Stripe API
- Валидация: обязательно указать либо курс, либо урок
- Фильтрация по курсу, уроку, способу оплаты
- Сортировка по дате платежа и сумме
- Корректная обработка PATCH запросов

### ⚡ Асинхронные задачи (Celery & Redis)

Проект использует **Celery** для асинхронной обработки задач и **Redis** в качестве message broker. Это позволяет выполнять длительные операции без блокировки HTTP-запросов.

**Архитектура:**

```
┌──────────────┐    Task      ┌──────────────┐    Fetch   ┌──────────────┐
│   Django     │──────────────▶│    Redis     │◀───────────│   Celery     │
│  Web Server  │   to Queue   │   (Broker)   │   Task     │   Worker     │
└──────────────┘              └──────────────┘            └──────────────┘
       │                             ▲                            │
       │                             │                            │
       ▼                             │                            ▼
┌──────────────┐              ┌──────────────┐            ┌──────────────┐
│  PostgreSQL  │              │ Celery Beat  │            │  Execute     │
│   Database   │◀─────────────│  Scheduler   │            │  Business    │
└──────────────┘              └──────────────┘            │  Logic       │
                                                          └──────────────┘
```

**Реализованные задачи:**

#### 1. 📧 **Email уведомления при обновлении курсов**

- **Триггер**: Пользователь обновляет курс через API (`PUT/PATCH /api/courses/{id}/`)
- **Поток работы**:
  1. `CourseViewSet.perform_update()` сохраняет изменения в БД
  2. Вызывается `send_course_update_notification.delay(course_id)`
  3. Задача помещается в Redis очередь
  4. Celery Worker забирает задачу и выполняет `notify_course_subscribers()`
  5. Email отправляется всем подписчикам курса
- **Cooldown защита**: Уведомления не чаще **1 раза в 4 часа** для каждого курса
- **Конфигурация**: `EMAIL_NOTIFICATION_COOLDOWN_HOURS=4` (настраивается через .env)
- **Email backend**: `console` (для разработки) / `SMTP` (для production)

#### 2. 🔒 **Периодическая блокировка неактивных пользователей**

- **Триггер**: Celery Beat (автоматически по расписанию)
- **Расписание**: Каждый день в **3:00 UTC**
- **Логика**:
  1. Находит пользователей без логина > 30 дней
  2. Устанавливает `is_active=False`
  3. Возвращает количество заблокированных пользователей
- **Конфигурация**: `INACTIVE_USER_DAYS=30` (настраивается через .env)
- **Безопасность**: Только неактивные пользователи, суперпользователи не блокируются

#### 📐 **Service Layer Pattern**

Все Celery задачи следуют архитектурному паттерну **тонких оберток**:

- **Задачи** (`lms/tasks.py`, `users/tasks.py`) — только Celery обертки
- **Сервисы** (`lms/services.py`, `users/services.py`) — вся бизнес-логика
- **Преимущества**:
  - ✅ Легко тестировать сервисы без Celery
  - ✅ Переиспользование логики вне задач (CLI, admin, тесты)
  - ✅ 100% покрытие тестами для всех сервисов и задач

#### 🔧 **Технические детали**

- **Message Broker**: Redis 7 (порт 6379)
- **Компоненты**:
  - Celery Worker — выполнение асинхронных задач
  - Celery Beat — планировщик периодических задач
- **Мониторинг**: Логи Celery + команды inspect (`celery -A config inspect active`)
- **Переменные окружения**:
  ```bash
  REDIS_URL=redis://localhost:6379/0
  CELERY_BROKER_URL=redis://localhost:6379/0
  EMAIL_NOTIFICATION_COOLDOWN_HOURS=4
  INACTIVE_USER_DAYS=30
  ```

**Запуск Celery:**

```bash
# 1. Запустить Redis
redis-server

# 2. Запустить Celery Worker
celery -A config worker --loglevel=info

# 3. Запустить Celery Beat (для периодических задач)
celery -A config beat --loglevel=info
```

**Документация:** Подробная инструкция по настройке и troubleshooting в [docs/CELERY_SETUP.md](docs/CELERY_SETUP.md)

### 🔗 REST API
- Полный CRUD для всех сущностей
- ViewSet для Course, User и Payment
- Generic-классы для Lesson
- **Динамическая главная страница API** (`/api/`) - автоматический сбор endpoints
- Browsable интерфейс Django REST Framework
- Редирект с `/` на `/api/` для удобства
- Продвинутая фильтрация через Django Filter

### 📚 API Документация
- **OpenAPI 3.0** спецификация через drf-spectacular
- **Swagger UI** (`/api/docs/`) - интерактивная документация с возможностью тестирования
- **ReDoc** (`/api/redoc/`) - альтернативное представление документации
- **JSON Schema** (`/api/schema/`) - программный доступ к схеме API
- Все эндпоинты документированы с описаниями на русском языке
- Примеры запросов и ответов для каждого endpoint
- Ссылки на документацию доступны в API Root (`/api/`) в секции "documentation"

### 🗄️ Демонстрационные данные
- 1 суперпользователь: `admin@example.com` / `admin123`
- 3 курса (Python, Django REST Framework, PostgreSQL)
- 5 уроков (3 в курсе Python, 2 в курсе Django)
- 3 платежа (2 за курсы, 1 за урок)
- **Fixtures** для быстрого восстановления данных

## 🔐 Система авторизации и прав доступа

### Реализованные задания

#### ✅ Задание 1: JWT-авторизация и CRUD пользователей

- **Двойная аутентификация**:
  - **Session Authentication** — для работы через Browsable API Django REST Framework
  - **JWT Authentication** — для программного доступа (через `djangorestframework-simplejwt`)
- **Регистрация пользователей** через эндпоинт `/api/register/`
- **Получение JWT токенов**:
  - `/api/token/` — получение access и refresh токенов
  - `/api/token/refresh/` — обновление access токена
- **Защита эндпоинтов**: все API требуют авторизации, кроме регистрации и получения токенов
- **CRUD для пользователей** с email-аутентификацией (вместо username)

#### ✅ Задание 2: Группа модераторов

- **Создана группа "Модераторы"** через Django Admin
- **Права модераторов**:
  - ✅ Просмотр всех курсов и уроков
  - ✅ Редактирование любых курсов и уроков (даже чужих)
  - ❌ **НЕ могут** создавать новые курсы и уроки
  - ❌ **НЕ могут** удалять курсы и уроки
- **Проверка через** `request.user.groups.filter(name='Модераторы').exists()`
- **Управление**: назначение модераторов только через Django Admin (`/admin/`)

#### ✅ Задание 3: Владельцы объектов

- **Поле `owner`** добавлено в модели `Course`, `Lesson`, `Payment`
- **Автоматическая привязка** при создании через `perform_create()`
- **Права владельцев**:
  - ✅ Просмотр своих объектов
  - ✅ Редактирование только своих объектов
  - ✅ Удаление только своих объектов
- **Обычные пользователи** (не модераторы) видят все курсы/уроки, но редактируют только свои
- **Модераторы ИЛИ владельцы** могут редактировать курсы/уроки

#### ✅ Задание 4: Асинхронные задачи с Celery

- **Email уведомления**:
  - Автоматическая рассылка писем подписчикам при обновлении курса
  - Cooldown механизм: не чаще раза в 4 часа (настраивается через `.env`)
  - Celery задача `send_course_update_notification` в `lms/tasks.py`
  - Service layer для бизнес-логики в `lms/services.py`
- **Периодическая блокировка пользователей**:
  - Celery Beat задача запускается каждый день в 3:00 UTC
  - Блокировка пользователей без активности > 30 дней (настраивается через `.env`)
  - Задача `block_inactive_users_task` в `users/tasks.py`
  - Service layer для блокировки в `users/services.py`
- **Redis** как message broker для Celery
- **100% test coverage** для всех сервисов и задач (30 новых тестов)

#### ✅ Дополнительное задание: Публичные профили

- **Два типа сериализаторов**:
  - **`PublicUserSerializer`** — для чужих профилей (только общая информация)
  - **`UserDetailSerializer`** — для своего профиля (полные данные)
- **Публичные данные** (видны всем): `id`, `email`, `phone`, `city`
- **Приватные данные** (только для себя): `first_name`, `last_name`, `avatar`, `payment_set`
- **Редактирование профиля**: только своего (через permission `IsSelf`)
- **Модераторы** видят чужие профили так же, как обычные пользователи (только публичные данные)

---

### 📊 Матрица прав доступа

#### 👤 Users (Профили пользователей)

| Действие | Anonymous | User | Moderator | Owner |
|----------|-----------|------|-----------|-------|
| **LIST** `/users/` | ❌ | ✅ (публичные данные) | ✅ (публичные данные) | ✅ (публичные данные) |
| **CREATE** `/users/` | ✅ (регистрация) | ✅ | ✅ | — |
| **RETRIEVE** `/users/{id}/` | ❌ | ✅ (публичные) / ✅ (свой: полные) | ✅ (публичные) / ✅ (свой: полные) | ✅ (полные данные) |
| **UPDATE/PATCH** `/users/{id}/` | ❌ | ❌ | ❌ | ✅ (только свой) |
| **DELETE** `/users/{id}/` | ❌ | ❌ | ❌ | ✅ (только свой) |

**Примечание**: Модераторы видят чужие профили только с публичными данными, редактировать могут только свой профиль.

---

#### 📚 Courses (Курсы)

| Действие | Anonymous | User | Moderator | Owner |
|----------|-----------|------|-----------|-------|
| **LIST** `/courses/` | ❌ | ✅ | ✅ | ✅ |
| **CREATE** `/courses/` | ❌ | ✅ | ❌ (запрещено) | — |
| **RETRIEVE** `/courses/{id}/` | ❌ | ✅ | ✅ | ✅ |
| **UPDATE/PATCH** `/courses/{id}/` | ❌ | ❌ | ✅ (любой курс) | ✅ (только свой) |
| **DELETE** `/courses/{id}/` | ❌ | ❌ | ❌ | ✅ (только свой) |

**Особенности**:
- Модераторы **НЕ создают** курсы (согласно заданию)
- Модераторы **могут редактировать** любые курсы
- **Удалить** курс может только владелец

---

#### 📖 Lessons (Уроки)

| Действие | Anonymous | User | Moderator | Owner |
|----------|-----------|------|-----------|-------|
| **LIST** `/lessons/` | ❌ | ✅ | ✅ | ✅ |
| **CREATE** `/lessons/` | ❌ | ✅ | ❌ (запрещено) | — |
| **RETRIEVE** `/lessons/{id}/` | ❌ | ✅ | ✅ | ✅ |
| **UPDATE/PATCH** `/lessons/{id}/` | ❌ | ❌ | ✅ (любой урок) | ✅ (только свой) |
| **DELETE** `/lessons/{id}/` | ❌ | ❌ | ❌ | ✅ (только свой) |

**Особенности**:
- Аналогично курсам: модераторы не создают, но редактируют
- Удаление только владельцем

---

#### 💳 Payments (Платежи)

| Действие | Anonymous | User | Moderator | Owner |
|----------|-----------|------|-----------|-------|
| **LIST** `/payments/` | ❌ | ✅ (все платежи) | ✅ (все платежи) | ✅ (все платежи) |
| **CREATE** `/payments/` | ❌ | ✅ | ✅ | — |
| **RETRIEVE** `/payments/{id}/` | ❌ | ❌ | ❌ | ✅ (только свой) |
| **UPDATE/PATCH** `/payments/{id}/` | ❌ | ❌ | ❌ | ✅ (только свой) |
| **DELETE** `/payments/{id}/` | ❌ | ❌ | ❌ | ✅ (только свой) |

**Особенности**:
- Список платежей **виден всем** аутентифицированным (с фильтрацией)
- Детальный просмотр, редактирование и удаление — **только владелец**

---

### 🛡️ Permission классы

| Класс | Уровень проверки | Описание |
|-------|------------------|----------|
| **`IsModerator`** | Request | Пользователь входит в группу "Модераторы" |
| **`IsOwner`** | Object | Текущий пользователь = владелец объекта (`obj.owner == user`) |
| **`IsOwnerOrReadOnly`** | Object | Чтение всем, изменение только владельцу |
| **`IsModeratorOrOwner`** | Object | Модератор **ИЛИ** владелец (для редактирования) |
| **`IsNotModerator`** | Request | **НЕ** модератор (для создания курсов/уроков) |
| **`IsSelf`** | Object | Пользователь редактирует сам себя (для `UserViewSet`) |

**Реализация**: `users/permissions.py`

---

### 🔑 Ключевые принципы безопасности

1. **Модераторы** — "редакторы" контента: редактируют чужие объекты, но не создают и не удаляют
2. **Владельцы** — полный контроль над своими объектами (CRUD)
3. **Платежи** — строго приватные детали, но список виден всем (для аналитики)
4. **Профили** — публичные данные для всех, полные данные только для себя
5. **JWT токены** — безопасная stateless авторизация для мобильных/веб приложений

---

## 📡 API Endpoints

### Главная страница API

```bash
# Динамическая страница со ссылками на все endpoints
GET /api/
```

### Пользователи

```bash
# Список всех пользователей
GET /api/users/

# Создание нового пользователя
POST /api/users/
{
  "email": "user@example.com",
  "password": "securepass123",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7 999 123 4567",
  "city": "Москва"
}

# Получение информации о пользователе (с историей платежей)
GET /api/users/{id}/

# Обновление пользователя
PUT /api/users/{id}/
PATCH /api/users/{id}/

# Удаление пользователя
DELETE /api/users/{id}/
```

### Курсы

```bash
# Список всех курсов (с пагинацией, lessons_count, lessons и is_subscribed)
GET /api/courses/
GET /api/courses/?page=2
GET /api/courses/?page_size=5  # Custom page size (max 100)

# Создание курса
POST /api/courses/
{
  "title": "Python для начинающих",
  "description": "Изучаем Python с нуля",
  "preview": <file>
}

# Детали курса (с полной информацией по урокам)
GET /api/courses/{id}/

# Обновление курса
PUT /api/courses/{id}/
PATCH /api/courses/{id}/

# Удаление курса
DELETE /api/courses/{id}/
```

### Уроки

```bash
# Список всех уроков
GET /api/lessons/

# Создание урока
POST /api/lessons/
{
  "title": "Введение в Python",
  "description": "Первый урок курса",
  "course": 1,
  "video_url": "https://www.youtube.com/watch?v=xxxxx",
  "preview": <file>
}

# Детали урока
GET /api/lessons/{id}/

# Обновление урока
PUT /api/lessons/{id}/
PATCH /api/lessons/{id}/

# Удаление урока
DELETE /api/lessons/{id}/
```

### Подписки

```bash
# Toggle подписки на курс (subscribe/unsubscribe)
POST /api/subscription/
{
  "course_id": 1
}

# Ответ при подписке
{
  "message": "Подписка добавлена"
}

# Ответ при отписке
{
  "message": "Подписка удалена"
}

# Статус подписки доступен в поле is_subscribed при GET /api/courses/
```

### Платежи

```bash
# Список платежей с фильтрацией и сортировкой
GET /api/payments/
GET /api/payments/?course=1          # Фильтр по курсу
GET /api/payments/?lesson=2          # Фильтр по уроку
GET /api/payments/?payment_method=cash  # Фильтр по способу оплаты
GET /api/payments/?ordering=payment_date  # Сортировка по дате
GET /api/payments/?ordering=-amount   # Сортировка по сумме (убывание)

# Создание платежа (наличные/перевод)
POST /api/payments/
{
  "user": 1,
  "course": 1,
  "amount": "2500.00",
  "payment_method": "transfer",
  "payment_date": "2025-10-27T12:00:00Z"
}

# Создание платежа через Stripe
POST /api/payments/
{
  "user": 1,
  "course": 1,
  "amount": "2500.00",
  "payment_method": "stripe"
}

# Ответ при payment_method=stripe содержит:
{
  "id": 1,
  "user": 1,
  "course": 1,
  "amount": "2500.00",
  "payment_method": "stripe",
  "payment_link": "https://checkout.stripe.com/c/pay/cs_test_...",  # Ссылка на оплату
  "stripe_session_id": "cs_test_...",
  "payment_date": "2025-11-12T10:00:00Z"
}

# Проверка статуса платежа Stripe (дополнительное задание)
GET /api/payments/{id}/check_status/

# Ответ check_status:
{
  "status": "paid"  # или "unpaid", "expired", "canceled"
}

# Детали платежа
GET /api/payments/{id}/

# Обновление платежа
PUT /api/payments/{id}/
PATCH /api/payments/{id}/

# Удаление платежа
DELETE /api/payments/{id}/
```

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.12+ (локальная разработка)
- Poetry
- PostgreSQL

**Политика версий Python:**

Проект использует **гибкий constraint** `python = "^3.12"` в pyproject.toml для совместимости локальной разработки:

- **Локальная разработка**: Python 3.12+ (Replit использует 3.12.11)
- **Docker/Production**: Python 3.13.5 (точная версия закреплена в Dockerfile)
- **CI/CD тесты**: Python 3.13.5 (точная версия в GitHub Actions)

**Воспроизводимость production:**
Для полной идентичности с production окружением используйте Docker:
```bash
docker-compose up
```

Все зависимости совместимы с Python 3.12-3.13. Docker образ гарантирует воспроизводимость production builds.

### Установка

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd DRF
```

2. **Установите зависимости**
```bash
poetry install
```

3. **Настройте переменные окружения**

Создайте файл `.env`:
```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/lms_db

# Stripe API keys (для интеграции платежей)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
```

> **Примечание**: Для получения Stripe API ключей зарегистрируйтесь на https://stripe.com и используйте тестовые ключи из Dashboard.

4. **Примените миграции**
```bash
poetry run python manage.py migrate
```

5. **Загрузите демо-данные (опционально)**

```bash
# Вариант 1: Использовать готовые fixtures (РЕКОМЕНДУЕТСЯ)
poetry run python manage.py loaddata lms/fixtures/courses.json
poetry run python manage.py loaddata lms/fixtures/lessons.json
poetry run python manage.py loaddata users/fixtures/payments.json

# Fixtures включают:
# - 3 курса (Python, Django REST Framework, PostgreSQL)
# - 5 уроков (3 для Python, 2 для Django)
# - 3 платежа (демонстрация платежной системы)
```

**Или создайте суперпользователя вручную:**

```bash
# Стандартная команда Django
poetry run python manage.py createsuperuser
```

6. **Запустите сервер**
```bash
poetry run python manage.py runserver
```

Сервер будет доступен по адресу: `http://localhost:8000` или `http://127.0.0.1:8000`

API доступен по адресу: `http://localhost:8000/api/`

> **Примечание**: Для production или деплоя на удалённый сервер используйте `runserver 0.0.0.0:PORT`

**Доступные endpoints:**
- API Root: `http://localhost:8000/api/`
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- Admin Panel: `http://localhost:8000/admin/`

---

## 🚀 CI/CD Pipeline

Проект использует **GitHub Actions** для автоматизации тестирования, сборки и развёртывания.

### Pipeline Jobs:

1. **Test** — 265 тестов (Django + Pytest) с 98% coverage
2. **Lint** — Ruff, Black, Mypy, isort, Flake8
3. **Build & Push** — Docker образ → GitHub Container Registry
4. **Deploy** — Автоматическое развёртывание на production

### GitHub Secrets Setup:

Для работы CI/CD необходимо настроить secrets в `Settings` → `Secrets and variables` → `Actions`:

| Secret | Описание |
|--------|----------|
| `SSH_KEY` | Приватный SSH ключ для доступа к серверу |
| `SSH_USER` | Имя пользователя SSH (например, `deploy`) |
| `SERVER_IP` | IP-адрес production сервера |
| `DEPLOY_DIR` | Директория на сервере (например, `/opt/lms`) |
| `SECRET_KEY` | Django SECRET_KEY (опционально для тестов) |

### Triggers:

- ✅ `push` в `main` → полный pipeline + deployment
- ✅ `push` в `develop` → test + lint (без deployment)
- ✅ Pull Request → test + lint (без deployment)

**Подробная документация:** [docs/CI_CD.md](docs/CI_CD.md)

---

## 🐳 Docker Quick Start

Проект поддерживает запуск через Docker Compose для локальной разработки и тестирования. Все сервисы (Django, PostgreSQL, Redis, Celery) запускаются единой командой.

**Особенности Docker setup:**
- 🔧 Development конфигурация (Django runserver, DEBUG=True)
- 🐘 PostgreSQL 16 с health checks
- 🔄 Redis для Celery и будущего кэширования
- ⚡ Celery Worker + Beat для асинхронных задач
- 📦 Автоматическое применение миграций через entrypoint
- 💾 Named volumes для персистентности данных

### Быстрый запуск

1. **Убедитесь что Docker и Docker Compose установлены**
```bash
docker --version
docker-compose --version
```

2. **Запустите все сервисы**
```bash
docker-compose up -d
```

3. **Примените миграции и загрузите fixtures**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata lms/fixtures/courses.json
docker-compose exec web python manage.py loaddata lms/fixtures/lessons.json
docker-compose exec web python manage.py loaddata users/fixtures/payments.json
```

4. **Создайте суперпользователя (опционально)**
```bash
docker-compose exec web python manage.py createsuperuser
```

5. **Проверьте работоспособность**
```bash
# Статус всех контейнеров
docker-compose ps

# Логи конкретного сервиса
docker-compose logs web
docker-compose logs db
```

**Приложение будет доступно по адресу:** `http://localhost:8000/api/`

### Управление сервисами

```bash
# Остановить все сервисы
docker-compose down

# Остановить с удалением volumes (ОСТОРОЖНО: удалит данные БД!)
docker-compose down -v

# Просмотр логов в реальном времени
docker-compose logs -f web

# Перезапуск отдельного сервиса
docker-compose restart web
```

### Проверка работоспособности сервисов

Согласно заданию, каждый сервис должен быть проверен на корректную работу:

#### 1️⃣ **PostgreSQL (База данных)**

```bash
# Проверка статуса контейнера
docker-compose ps db

# Подключение к БД для проверки
docker-compose exec db psql -U lms_user -d lms_db -c "\dt"

# Проверка логов
docker-compose logs db

# Ожидаемый результат: список таблиц Django (users_user, lms_course, lms_lesson и т.д.)
```

**Критерии успеха:**
- ✅ Контейнер `db` в статусе `Up (healthy)`
- ✅ Команда `\dt` показывает таблицы Django
- ✅ Нет ошибок в логах

#### 2️⃣ **Redis (Message Broker)**

```bash
# Проверка статуса контейнера
docker-compose ps redis

# Проверка подключения
docker-compose exec redis redis-cli ping

# Проверка логов
docker-compose logs redis

# Ожидаемый результат: "PONG"
```

**Критерии успеха:**
- ✅ Контейнер `redis` в статусе `Up (healthy)`
- ✅ Команда `ping` возвращает `PONG`
- ✅ Redis готов принимать подключения

#### 3️⃣ **Django Web (Backend)**

```bash
# Проверка статуса контейнера
docker-compose ps web

# Проверка доступности API
curl http://localhost:8000/api/

# Проверка логов
docker-compose logs web

# Открыть в браузере
# http://localhost:8000/api/        - API Root
# http://localhost:8000/api/docs/   - Swagger UI
# http://localhost:8000/admin/      - Django Admin
```

**Критерии успеха:**
- ✅ Контейнер `web` в статусе `Up`
- ✅ API возвращает JSON с endpoints
- ✅ Swagger UI доступен
- ✅ Миграции применены без ошибок

#### 4️⃣ **Celery Worker (Асинхронные задачи)**

```bash
# Проверка статуса контейнера
docker-compose ps celery_worker

# Проверка активных задач
docker-compose exec celery_worker celery -A config inspect active

# Проверка зарегистрированных задач
docker-compose exec celery_worker celery -A config inspect registered

# Проверка логов
docker-compose logs celery_worker

# Ожидаемый результат: список задач (send_course_update_notification, block_inactive_users_task)
```

**Критерии успеха:**
- ✅ Контейнер `celery_worker` в статусе `Up`
- ✅ Worker подключен к Redis
- ✅ Зарегистрированы задачи из `lms.tasks` и `users.tasks`

#### 5️⃣ **Celery Beat (Планировщик)**

```bash
# Проверка статуса контейнера
docker-compose ps celery_beat

# Проверка логов (должен показывать расписание задач)
docker-compose logs celery_beat | grep "Scheduler"

# Проверка расписания задач
docker-compose exec celery_beat celery -A config inspect scheduled

# Ожидаемый результат: периодическая задача block_inactive_users_task запланирована
```

**Критерии успеха:**
- ✅ Контейнер `celery_beat` в статусе `Up`
- ✅ Beat scheduler запущен
- ✅ В логах видно расписание задач

#### 📋 **Комплексная проверка всех сервисов**

```bash
# Проверка статуса всех контейнеров
docker-compose ps

# Все сервисы должны быть в статусе Up:
# - lms_postgres       (Up, healthy)
# - lms_redis          (Up, healthy)
# - lms_web            (Up)
# - lms_celery_worker  (Up)
# - lms_celery_beat    (Up)

# Проверка сетевого взаимодействия
docker-compose exec web python manage.py check --deploy

# Запуск тестов в Docker
make test-docker
# или
docker-compose exec web ./scripts/unix/test_all.sh
```

**Итоговая проверка:**
- ✅ Все 5 контейнеров запущены
- ✅ PostgreSQL принимает подключения
- ✅ Redis отвечает на ping
- ✅ Django API доступен на порту 8000
- ✅ Celery Worker обрабатывает задачи
- ✅ Celery Beat планирует периодические задачи
- ✅ Тесты проходят успешно (265 тестов)

### 📖 Детальная документация

Comprehensive руководство по Docker setup доступно в [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md):
- 🏗️ Архитектура и диаграмма взаимодействия сервисов
- ⚙️ Переменные окружения (.env для localhost + docker-compose overrides)
- 💾 Volumes и персистентность данных (PostgreSQL, media, static)
- 🔍 Health checks и мониторинг
- 🛠️ Troubleshooting частых проблем
- 📊 Мониторинг, логи и метрики
- 🚀 Production roadmap (Gunicorn, nginx, масштабирование)

---

## 🧪 Тестирование

> **Быстрый старт**: `poetry run python manage.py test && poetry run pytest --reuse-db`
> Детальная инструкция: [docs/QUICK_START_TESTING.md](docs/QUICK_START_TESTING.md)

Проект имеет **265 тестов** (78 Django + 187 pytest) с покрытием кода **87.68%** 🎯

### Структура тестов

Проект использует **два вида тестов** согласно договоренности:

1. **Django APITestCase** (в папках приложений):
   - `lms/tests.py` — 36 тестов (API endpoints для Course, Lesson, Subscription)
   - `users/tests.py` — 42 теста (API endpoints для User, Payment)
   - Запуск: `python manage.py test`

2. **Pytest** (в папке tests/):
   - `tests/lms/` — unit/integration тесты (сервисы, модели, tasks, serializers)
   - `tests/users/` — unit/integration тесты (Stripe, permissions, JWT, tasks)
   - `tests/config/` — тесты конфигурации
   - **Всего: 187 тестов** (включая regression тесты для Service Layer)
   - Запуск: `pytest`

### Запуск всех тестов

#### 🚀 Рекомендуемый способ (через скрипт или Makefile):

**Linux / macOS / WSL:**

```bash
# Вариант 1: Единый скрипт (запускает 265 тестов + coverage)
./scripts/unix/test_all.sh

# Вариант 2: Через Makefile (еще короче!)
make test
```

**Windows CMD:**

```cmd
REM Запуск всех тестов
scripts\windows\test_all.bat
```

**Windows PowerShell:**

```powershell
# Запуск всех тестов
.\scripts\windows\test_all.ps1
```

**Docker (все платформы):**

```bash
# Через Makefile (если установлен make)
make test-docker

# Или напрямую
docker-compose exec web ./scripts/unix/test_all.sh
```

**Скрипт `test_all` автоматически:**
1. ✅ Запускает Django тесты (78) → coverage данные
2. ✅ Запускает pytest тесты (187) → append к coverage
3. ✅ Генерирует отчёт: `coverage report` + HTML в `htmlcov/`

> 📖 **Подробная инструкция по скриптам**: [scripts/README.md](scripts/README.md)

#### 📦 Ручной запуск (если нужен детальный контроль):

```bash
# Запуск ВСЕХ тестов
poetry run python manage.py test && poetry run pytest

# Django тесты (в приложениях)
poetry run python manage.py test

# Pytest тесты (в tests/)
poetry run pytest --reuse-db

# С объединенным отчётом о покрытии (Django + pytest)
coverage run --source='users,lms,config' manage.py test && \
coverage run --append --source='users,lms,config' -m pytest --no-cov && \
coverage report
```

#### 🐳 Тестирование в Docker:

```bash
# Все тесты в Docker
make test-docker

# Или напрямую
docker-compose exec web ./scripts/unix/test_all.sh

# Раздельный запуск в Docker
docker-compose exec web python manage.py test  # Django (78)
docker-compose exec web poetry run pytest      # pytest (187)
```

### 📊 Статистика

**265 тестов** — все проходят ✅ **Объединенное покрытие: 87.68%** 🎯

**Ключевые модули с 100% покрытием:**
- **lms/services.py** — Email уведомления + Service Layer (lessons_count, is_subscribed)
- **lms/serializers.py** — CourseSerializer с делегированием в сервисы
- **users/services.py** — Stripe API + блокировка пользователей
- **users/permissions.py** — кастомные права доступа
- **lms/tasks.py** и **users/tasks.py** — все Celery задачи

Подробнее: [docs/QUICK_START_TESTING.md](docs/QUICK_START_TESTING.md)

## 🎨 Качество кода

Проект придерживается строгих стандартов качества кода:

### Проверка кода

**Linux / macOS / WSL:**

```bash
# Через Makefile (рекомендуется)
make check  # Запуск всех проверок
make fix    # Автоисправление

# Через скрипты напрямую
./scripts/unix/check.sh
./scripts/unix/fix.sh

# Watch-режим (автопроверка при изменении файлов)
./scripts/unix/watch.sh
```

**Windows CMD:**

```cmd
REM Проверка качества кода
scripts\windows\check.bat

REM Автоисправление
scripts\windows\fix.bat
```

**Windows PowerShell:**

```powershell
# Проверка качества кода
.\scripts\windows\check.ps1

# Автоисправление
.\scripts\windows\fix.ps1
```

**Кросс-платформенно (через Poetry):**

```bash
# Работает на всех ОС
poetry run check
poetry run fix
```

**Доступные Makefile команды:**

| Команда | Описание |
|---------|----------|
| `make help` | Показать все доступные команды |
| `make test` | Запустить все тесты локально |
| `make test-docker` | Запустить тесты в Docker |
| `make check` | Code quality checks (ruff, mypy, flake8) |
| `make fix` | Auto-fix code style |
| `make docker-up` | Запустить Docker контейнеры |
| `make docker-down` | Остановить Docker контейнеры |
| `make docker-shell` | Открыть shell в web контейнере |
| `make docker-logs` | Показать логи всех контейнеров |

### Инструменты проверки

| Инструмент | Назначение | Статус |
|------------|------------|--------|
| **Mypy** | Проверка типов | ✅ 0 ошибок на 58 файлах |
| **Ruff** | Быстрая проверка кода | ✅ All checks passed |
| **Black** | Форматирование | ✅ 119 символов/строка |
| **isort** | Сортировка импортов | ✅ Совместимость с Black |
| **Flake8** | Дополнительные проверки | ✅ Passed |
| **Django** | System check | ✅ No issues |

### Watch-режим

Автоматическая проверка при изменении файлов (только Unix):

```bash
# Linux / macOS / WSL
./scripts/unix/watch.sh
```

> ⚠️ **Примечание:** Watch-режим доступен только на Unix-системах (требует `inotify-tools`). На Windows используйте IDE с авто-проверкой или запускайте `scripts\windows\check.bat` вручную.

## 🛠 Управление базой данных

### Работа с фикстурами

```bash
# Загрузка демо-данных
poetry run python manage.py loaddata lms/fixtures/courses.json
poetry run python manage.py loaddata lms/fixtures/lessons.json
poetry run python manage.py loaddata users/fixtures/payments.json

# Создание супер пользователя
poetry run python manage.py createsuperuser
```

## 📁 Структура проекта

> **⚠️ Примечание:** Папка `vehicle/` содержит отдельный проект и не относится к LMS системе.

```
DRF/
├── config/                 # Настройки Django
│   ├── settings.py         # Основные настройки (PostgreSQL, JWT, CORS)
│   ├── urls.py             # Главный URL роутинг
│   ├── views.py            # api_root() - динамическая главная API
│   └── wsgi.py             # WSGI конфигурация
├── users/                  # Приложение пользователей
│   ├── models.py           # User (email auth), Payment
│   ├── serializers.py      # PublicUserSerializer, UserDetailSerializer, RegisterSerializer
│   ├── views.py            # UserViewSet, PaymentViewSet
│   ├── permissions.py      # Custom permissions (IsOwner, IsModerator, etc.)
│   ├── tests.py            # 38 тестов (99% покрытие)
│   ├── urls.py             # URL маршруты
│   └── fixtures/           # Демо-данные (3 платежа)
├── lms/                    # Приложение LMS
│   ├── models.py           # Course, Lesson, Subscription + BaseModel
│   ├── serializers.py      # CourseSerializer (with lessons), LessonSerializer
│   ├── views.py            # CourseViewSet, Lesson views, SubscriptionToggle
│   ├── validators.py       # YouTube URL validator
│   ├── paginators.py       # LMSPaginator (10 per page, max 100)
│   ├── constants.py        # Subscription messages (DRY)
│   ├── tests.py            # 36 тестов (100% покрытие)
│   ├── urls.py             # URL маршруты
│   └── fixtures/           # Демо-данные (3 курса, 5 уроков)
├── docs/                   # Документация
│   ├── CELERY_SETUP.md     # Настройка Celery и асинхронных задач
│   ├── STRIPE_INTEGRATION.md # Интеграция с Stripe API
│   └── QUICK_START_TESTING.md # Быстрый старт для тестирования
├── media/                  # Загруженные файлы
│   ├── courses/previews/   # Превью курсов
│   └── lessons/previews/   # Превью уроков
├── static/                 # Статические файлы
├── pyproject.toml          # Конфигурация Poetry и инструментов
├── .editorconfig           # Настройки редактора
├── .gitignore              # Git ignore
└── README.md               # Этот файл
```

## 🔧 Разработка

### Рабочий процесс (TDD)

Проект следует строгому TDD подходу:

1. **RED** — Написать падающий тест
2. **GREEN** — Написать минимальный код для прохождения теста
3. **REFACTOR** — Улучшить код

### Создание нового приложения

```bash
poetry run python manage.py startapp app_name
```

Не забудьте:
- Добавить в `INSTALLED_APPS` в `config/settings.py`
- Создать тесты в `tests/app_name/`
- Следовать TDD подходу

### Работа с базой данных

```bash
# Создать миграции
poetry run python manage.py makemigrations

# Применить миграции
poetry run python manage.py migrate

# Откатить миграции
poetry run python manage.py migrate app_name 0001

# Загрузить демо-данные
poetry run python manage.py loaddata lms/fixtures/courses.json
poetry run python manage.py loaddata lms/fixtures/lessons.json
poetry run python manage.py loaddata users/fixtures/payments.json

# Выгрузить данные в fixtures
poetry run python manage.py dumpdata lms.Course --indent 2 > lms/fixtures/courses.json
poetry run python manage.py dumpdata lms.Lesson --indent 2 > lms/fixtures/lessons.json
poetry run python manage.py dumpdata users.Payment --indent 2 > users/fixtures/payments.json
```

### Оптимизация запросов к БД

Все ViewSet'ы используют `select_related()` и `prefetch_related()` для оптимизации запросов:

```python
# CourseViewSet - решение проблемы N+1 запросов
queryset = Course.objects.prefetch_related('lesson_set')

# PaymentViewSet - оптимизация всех связей
queryset = Payment.objects.select_related('user', 'course', 'lesson')
```

**Результат:** Сокращение запросов с 21 до 2 для списка курсов! 🚀

### Django Admin

Доступ к админ-панели: `http://localhost:8000/admin/`

## 📚 Дополнительная документация

- [docs/CELERY_SETUP.md](docs/CELERY_SETUP.md) — Настройка Celery и асинхронных задач
- [docs/STRIPE_INTEGRATION.md](docs/STRIPE_INTEGRATION.md) — Профессиональная интеграция с Stripe API
- [docs/QUICK_START_TESTING.md](docs/QUICK_START_TESTING.md) — Быстрый старт: запуск тестов и проверка покрытия


## ⚡ Производительность

- **Оптимизация запросов**: select_related и prefetch_related во всех ViewSet'ах
- **Сокращение запросов**: с 21 до 2 для списка курсов с уроками
- **Проблема N+1**: полностью решена
- **Тесты**: параллельное выполнение через pytest-xdist
- **Настройки для тестов**: SQLite in-memory для быстрого выполнения

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Следуйте TDD подходу
4. Запустите проверки: `poetry run check`
5. Убедитесь, что все тесты проходят: `poetry run pytest`
6. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
7. Push в branch (`git push origin feature/AmazingFeature`)
8. Откройте Pull Request

## 📄 Лицензия

Проект создан в образовательных целях.

## 👨‍💻 Автор

**Rinat Gabitov**
- Email: riga1897@yandex.ru

---

<div align="center">

**Сделано с ❤️ используя Django REST Framework**

[API](http://localhost:8000/api/) • [Админ](http://localhost:8000/admin/) • [docs/](./docs/)

</div>
