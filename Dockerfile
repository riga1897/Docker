# Dockerfile для Django LMS приложения
# Multi-stage build для оптимизации размера образа

# Стадия 1: Builder - установка зависимостей
FROM python:3.13.5-slim AS builder

# Переменные окружения для Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.1.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Рабочая директория
WORKDIR /app

# Копирование файлов зависимостей (poetry.lock будет создан автоматически в Linux окружении)
COPY pyproject.toml poetry.toml ./

# Установка зависимостей (Poetry создаст lockfile в Linux окружении)
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Стадия 2: Runtime - финальный образ
FROM python:3.13.5-slim AS runtime

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.1.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry глобально для доступа всем пользователям (включая django)
RUN pip install --break-system-packages "poetry==$POETRY_VERSION"

# Создание пользователя для запуска приложения (безопасность)
RUN groupadd -r django && useradd -r -g django django

# Рабочая директория
WORKDIR /app

# Копирование виртуального окружения из builder
COPY --from=builder --chown=django:django /app/.venv /app/.venv

# Копирование entrypoint script
COPY --chown=django:django docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Копирование приложения
COPY --chown=django:django . .

# Создание директорий для media, static и staticfiles
RUN mkdir -p /app/media /app/static /app/staticfiles && \
    chown -R django:django /app/media /app/static /app/staticfiles

# Переключение на непривилегированного пользователя
USER django

# Entrypoint для инициализации
ENTRYPOINT ["/docker-entrypoint.sh"]

# Порт приложения
EXPOSE 8000

# Команда по умолчанию - Gunicorn для production
# Override с помощью docker-compose для development: ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "config.wsgi:application"]
