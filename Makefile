.PHONY: help test test-docker docker-up docker-down docker-restart docker-shell docker-logs check fix

help:
        @echo "Django LMS Project - Available commands:"
        @echo ""
        @echo "Testing:"
        @echo "  make test              Run all tests locally (265 tests: Django + pytest)"
        @echo "  make test-docker       Run all tests in Docker container"
        @echo ""
        @echo "Code Quality:"
        @echo "  make check             Run all quality checks (ruff, mypy, flake8, black, isort)"
        @echo "  make fix               Auto-fix code style issues (black, isort, ruff --fix)"
        @echo ""
        @echo "Docker Operations:"
        @echo "  make docker-up         Start all Docker containers (detached mode)"
        @echo "  make docker-down       Stop and remove all Docker containers"
        @echo "  make docker-restart    Restart all Docker containers"
        @echo "  make docker-shell      Open interactive shell in web container"
        @echo "  make docker-logs       Show logs from all containers (follow mode)"
        @echo "  make docker-logs-web   Show logs from web container only"
        @echo "  make docker-migrate    Run Django migrations in Docker"
        @echo "  make docker-fixtures   Load fixtures in Docker"
        @echo ""
        @echo "Development:"
        @echo "  make run               Run Django development server locally"
        @echo "  make migrate           Run Django migrations locally"
        @echo "  make migrations        Create new migrations locally"

# Тестирование
test:
        @echo "Running all tests locally..."
        ./scripts/unix/test_all.sh

test-docker:
        @echo "Running all tests in Docker..."
        docker-compose exec web ./scripts/unix/test_all.sh

# Качество кода
check:
        @echo "Running code quality checks..."
        poetry run python -m scripts.check

fix:
        @echo "Auto-fixing code style issues..."
        poetry run python -m scripts.fix

# Docker операции
docker-up:
        @echo "Starting Docker containers..."
        docker-compose up -d

docker-down:
        @echo "Stopping Docker containers..."
        docker-compose down

docker-restart:
        @echo "Restarting Docker containers..."
        docker-compose restart

docker-shell:
        @echo "Opening shell in web container..."
        docker-compose exec web bash

docker-logs:
        @echo "Showing logs from all containers (Ctrl+C to exit)..."
        docker-compose logs -f

docker-logs-web:
        @echo "Showing logs from web container (Ctrl+C to exit)..."
        docker-compose logs -f web

docker-migrate:
        @echo "Running migrations in Docker..."
        docker-compose exec web python manage.py migrate

docker-fixtures:
        @echo "Loading fixtures in Docker..."
        docker-compose exec web python manage.py loaddata lms/fixtures/courses.json
        docker-compose exec web python manage.py loaddata lms/fixtures/lessons.json
        docker-compose exec web python manage.py loaddata users/fixtures/payments.json

# Локальная разработка
run:
        @echo "Starting Django development server..."
        poetry run python manage.py runserver

migrate:
        @echo "Running migrations..."
        poetry run python manage.py migrate

migrations:
        @echo "Creating new migrations..."
        poetry run python manage.py makemigrations
