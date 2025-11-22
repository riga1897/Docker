#!/bin/sh
# Healthcheck script для Celery worker
# Проверяет наличие активных воркеров через inspect ping

set -e

# Используем APP_MODULE из переменных окружения или по умолчанию
APP_MODULE="${CELERY_APP:-config}"

# Запускаем celery inspect ping с JSON выводом и timeout
output=$(celery -A $APP_MODULE inspect ping --timeout=5 --destination=1@worker1 --output=json 2>/dev/null || echo "{}")

# Проверяем что есть хотя бы один активный воркер
echo "$output" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    # Проверяем что есть хотя бы один воркер с статусом 'ok'
    if data and any('ok' in str(v).lower() for v in data.values() if v):
        print('✓ Celery workers are healthy')
        sys.exit(0)
    else:
        print('✗ No active Celery workers found')
        sys.exit(1)
except Exception as e:
    print(f'✗ Health check error: {e}')
    sys.exit(1)
"
