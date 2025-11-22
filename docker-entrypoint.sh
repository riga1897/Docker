#!/bin/sh
# Docker entrypoint script для Django DRF приложения

set -e

echo "=== Django DRF Docker Entrypoint ==="

# Функция для ожидания сервисов
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3

    echo "Waiting for $service at $host:$port..."
    until nc -z "$host" "$port"; do
        echo "$service is unavailable - sleeping"
        sleep 2
    done
    echo "✓ $service is ready"
}

# Ожидание PostgreSQL (для всех сервисов, которым нужна БД)
if [ -n "${DATABASE_URL}" ] || [ -n "${POSTGRES_HOST}" ]; then
    wait_for_service "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}" "PostgreSQL"
fi

# Ожидание Redis (если используется)
if [ -n "${REDIS_URL}" ] || [ -n "${REDIS_HOST}" ]; then
    wait_for_service "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}" "Redis"
fi

# Определяем тип сервиса
SERVICE_TYPE="unknown"
case "$1" in
    "python"|"gunicorn")
        SERVICE_TYPE="web"
        ;;
    "celery")
        SERVICE_TYPE="celery"
        ;;
    "celery-beat")
        SERVICE_TYPE="celery-beat"
        ;;
esac

echo "Service type: $SERVICE_TYPE"

# Действия для web сервиса
if [ "$SERVICE_TYPE" = "web" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
    echo "✓ Migrations applied"

    # Сборка статики для production
    if [ "$1" = "gunicorn" ]; then
        echo "Collecting static files for production..."
        python manage.py collectstatic --noinput --clear
        echo "✓ Static files collected"
    fi

    # Создание суперпользователя (только если указаны переменные)
    if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        echo "Creating superuser..."
        python manage.py createsuperuser \
            --email "$DJANGO_SUPERUSER_EMAIL" \
            --noinput || true
        echo "✓ Superuser created/updated"
    fi
fi

# Действия для Celery worker
if [ "$SERVICE_TYPE" = "celery" ]; then
    echo "Starting Celery worker..."
fi

# Действия для Celery beat
if [ "$SERVICE_TYPE" = "celery-beat" ]; then
    echo "Starting Celery beat scheduler..."
    # Создаем директорию для beat schedule file
    mkdir -p /app/celerybeat
    chown django:django /app/celerybeat
fi

# Запуск команды
echo "Starting: $@"
exec "$@"

