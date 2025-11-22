#!/bin/sh
# Healthcheck script для Celery Beat
# Проверяет что процесс beat запущен и работает

set -e

# Проверяем что процесс celery beat работает
if ps aux | grep -v grep | grep -q "celery.*beat"; then
    # Проверяем что файл schedule создан/обновляется
    if [ -f /app/celerybeat/celerybeat-schedule ] || [ -f /app/celerybeat-schedule.db ]; then
        echo "✓ Celery Beat is running"
        exit 0
    else
        echo "✗ Celery Beat schedule file not found"
        exit 1
    fi
else
    echo "✗ Celery Beat process not found"
    exit 1
fi
