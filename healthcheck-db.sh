#!/bin/sh
# Healthcheck script для проверки состояния БД и миграций

set -e

# Проверяем что можем подключиться к БД и выполнить запрос
python3 -c "
import django
from django.core.management import execute_from_command_line
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1;')
    print('✓ Database connection successful')

    # Проверяем что все миграции применены
    from django.core.management import execute_from_command_line
    from django.db.migrations.executor import MigrationExecutor
    from django.db import connections, DEFAULT_DB_ALIAS

    connection = connections[DEFAULT_DB_ALIAS]
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

    if plan:
        print('✗ Pending migrations found')
        sys.exit(1)
    else:
        print('✓ All migrations applied')
        sys.exit(0)

except Exception as e:
    print(f'✗ Database health check failed: {e}')
    sys.exit(1)
"
