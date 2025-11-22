#!/bin/sh
# Healthcheck script для Django web приложения

set -e

# Проверяем доступность основного endpoint'а
if curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
    exit 0
fi

# Fallback проверки
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    exit 0
fi

# Последняя попытка - проверка что сервер вообще отвечает
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    exit 0
fi

echo "Web service health check failed"
exit 1
