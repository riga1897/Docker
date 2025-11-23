#!/bin/sh
# Docker entrypoint script для запуска Django

set -e

echo "=== Django LMS Docker Entrypoint ==="

# Активация виртуального окружения
export PATH="/app/.venv/bin:$PATH"
export VIRTUAL_ENV="/app/.venv"

# Ожидание готовности PostgreSQL (для web сервиса: python или gunicorn)
if [ "$1" = "python" ] || [ "$1" = "gunicorn" ]; then
    echo "Waiting for PostgreSQL..."
    until nc -z "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}"; do
      echo "PostgreSQL is unavailable - sleeping"
      sleep 1
    done
    echo "✓ PostgreSQL is ready"

    # Применение миграций
    echo "Applying database migrations..."
    python manage.py migrate --noinput
    echo "✓ Migrations applied"

    # Сборка статических файлов
    # Для development (runserver) - опционально, Django раздаёт статику автоматически
    # Для production (gunicorn) - ОБЯЗАТЕЛЬНО
    if [ "$1" = "gunicorn" ]; then
        echo "Collecting static files for production..."
        python manage.py collectstatic --noinput
        echo "✓ Static files collected to /app/staticfiles"
    else
        echo "Skipping collectstatic for development mode (runserver)"
    fi
fi

# Запуск команды
echo "Starting: $@"
exec "$@"
