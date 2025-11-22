# ... предыдущая часть Dockerfile (builder stage)

# Стадия 2: Runtime - финальный образ
FROM python:3.13-slim AS runtime

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для запуска приложения
RUN groupadd -r django && useradd -r -g django django

# Рабочая директория
WORKDIR /app

# Копирование виртуального окружения из builder
COPY --from=builder /app/.venv /app/.venv

# Копирование entrypoint и healthcheck скриптов
COPY --chown=django:django docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY --chown=django:django docker/healthcheck-*.sh /docker-healthcheck/

RUN chmod +x /docker-entrypoint.sh /docker-healthcheck/*.sh

# Копирование приложения
COPY --chown=django:django . .

# Создание директорий
RUN mkdir -p /app/media /app/static /app/logs /app/celerybeat && \
    chown -R django:django /app/media /app/static /app/logs /app/celerybeat

# Переключение на непривилегированного пользователя
USER django

# Health check будет настроен в зависимости от сервиса
# ENTRYPOINT ["/docker-entrypoint.sh"]
EXPOSE 8000

# Базовая команда (переопределяется в docker-compose)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
