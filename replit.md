# Django REST Framework Project

## Overview

This project is a Django application built with Django REST Framework, serving as a Learning Management System (LMS). It provides a scalable, maintainable, API-first architecture for educational platforms, managing users, courses, and lessons. The vision is to offer a robust foundation for diverse educational services, emphasizing automated code quality and comprehensive testing.

## User Preferences

- **Workflow Preferences**: I prefer an iterative development approach guided by the TDD (Test-Driven Development) cycle: RED-GREEN-REFACTOR.
- **Coding Style Preferences**: Adherence to strict code quality standards is crucial, including 100% type coverage with Mypy and comprehensive test coverage with Pytest. Architectural principles like ABC, composition, and dependency injection should be applied. **ОБЯЗАТЕЛЬНО**: Вся документация, комментарии и docstrings должны быть на русском языке (см. раздел "4. Язык документации и комментариев" в DEVELOPMENT.md).
- **Performance Requirements**: Все ViewSet'ы и Generic Views **ОБЯЗАНЫ** использовать `select_related()` и `prefetch_related()` для оптимизации запросов к базе данных. Проблема N+1 запросов недопустима. При создании нового ViewSet сразу добавляйте оптимизацию запросов. См. раздел "Оптимизация запросов к базе данных" в DEVELOPMENT.md.
- **Interaction Preferences**: I expect the agent to follow the TDD workflow diligently. Before committing, the agent should always run `poetry run fix` for auto-correction and `poetry run check` for full code quality verification. During development, the `watch` mode (`./scripts/watch.sh`) should be utilized for immediate feedback on code changes. When creating new applications, the agent should use `poetry run python manage.py startapp app_name` and remember to add it to `INSTALLED_APPS`. For model changes, `makemigrations` and `migrate` are essential. **Testing Structure**: The project uses dual testing approach per agreement: Django APITestCase tests in app folders (`lms/tests.py`, `users/tests.py`) for app-specific API testing (78 tests), and pytest tests in `tests/` folder for unit/integration testing of services, models, Celery tasks, permissions, serializers, and config utilities (205 tests). **NO API tests in pytest** — API testing is handled exclusively by Django tests. For combined coverage analysis, use: `coverage run --source='users,lms,config' manage.py test && coverage run --append --source='users,lms,config' -m pytest --no-cov && coverage report` to get **98.23% coverage** from all 283 tests. Important: use `--no-cov` flag to avoid conflict between coverage.py and pytest-cov plugin.
- **Documentation Adherence**: It's critical to consult `DEVELOPMENT.md` for universal development standards, `docs/lms_roadmap.md` for project-specific architecture and future plans, `docs/tasks.md` for current assignments, `docs/CI_CD.md` for Infrastructure as Code deployment guide, `docs/STAGING_TESTING.md` for local staging testing with Docker Desktop, and **`docs/DEPLOYMENT_STRATEGY.md` for the complete three-tier deployment strategy (Development → Staging → Production)**.

## System Architecture

The project is built on Django and Django REST Framework, with PostgreSQL. It focuses on `users/`, `lms/`, `config/`, and `tests/` directories for the LMS functionality.

### UI/UX Decisions

- **API Documentation**: OpenAPI 3.0 documentation via drf-spectacular, available at `/api/docs/` (Swagger UI) and `/api/redoc/`. Endpoints are documented with Russian descriptions, request/response examples, and parameter specifications.

### Technical Implementations

- **Core Technologies**: Python 3.12+, Django 5.2.7, Django REST Framework 3.16.1.
- **Dependency Management**: Poetry.
- **Authentication**: Session Authentication (Browsable API) and JWT Authentication (`djangorestframework-simplejwt`).
- **API Structure**: CRUD operations for Users, Courses, Lessons, Payments, and Subscriptions.
- **Data Models**:
    - **Users App**: Custom user model with email authentication and `Payment` model.
    - **LMS App**: `Course`, `Lesson`, and `Subscription` models with timestamps. `CourseSerializer` includes `lessons_count`, nested `lessons`, `is_subscribed`, and `owner` fields.
    - **Payment System**: `Payment` model tracks transactions via cash, transfer, or Stripe.
    - **Subscription System**: `Subscription` model for user-course relationships.
- **Validators**: Custom YouTube URL validator.
- **Pagination**: `LMSPaginator` with configurable page size.
- **Permissions**: Custom permissions (`IsNotModerator`, `IsModeratorOrOwner`, `IsSelf`, `IsOwner`) based on user roles.
- **Code Quality**: Ruff, Black, isort, Mypy, Flake8 integrated, achieving 100% type coverage.
- **Testing**: Dual testing strategy (Django APITestCase for API, Pytest for unit/integration) with 98.23% code coverage across 283 tests.
- **Security**: Production-ready HTTPS configuration with environment-configurable settings for SSL, HSTS, and secure cookies.
- **CORS Configuration**: `django-cors-headers` for development and local environments.
- **Celery Integration**: Asynchronous tasks for email notifications and periodic user management, using Redis as a message broker.

### System Design Choices

- **API-First Approach**: Emphasizes a robust RESTful API.
- **Modular Structure**: Code organized into distinct Django applications.
- **Service Layer Pattern**: All business logic is encapsulated in service files, with ViewSets handling HTTP orchestration.
- **Automated Code Quality**: Scripts (`check.sh`, `fix.sh`, `watch.sh`) enforce code standards.
- **Comprehensive Testing**: TDD-focused approach with dual testing strategy.
- **Configuration**: Django settings in `config/`, environment variables via `.env`.
- **Three-Tier Deployment Strategy**:
    1.  **Development**: Local/cloud development environment (examples: Replit with Nix, VSCode/PyCharm locally), local PostgreSQL/Redis, port 5000.
    2.  **Staging**: Local Docker-based testing with live reload (examples: Windows/Mac/Linux + Docker Desktop), port 8000. Validates Docker builds and production configuration locally.
    3.  **Production**: VPS deployment via GitHub Actions CI/CD with Gunicorn, port 8000.
    - **Key Insight**: Development uses local services (localhost); Staging bridges local development with production's Docker service names (db, redis).
- **Docker Containerization**: Multi-stage production-ready setup with 5 services (web, db, redis, celery_worker, celery_beat) and dual compose configurations (`docker-compose.yml` for staging, `docker-compose.prod.yml` for production). Includes security measures and optimized `.dockerignore` for dev-specific files.
- **CI/CD Pipeline**: Full GitHub Actions automation using Infrastructure as Code.
    - **Jobs**: Test (265 tests, 98.22% coverage), Lint (comprehensive checks, 100% type coverage), Build & Push (Docker image to GHCR), Deploy (automated deployment to VPS via `docker-compose.prod.yml`).
    - **Production Secrets Management**: Automatic `.env` generation via `scripts/generate-production-env.sh` integrating GitHub Secrets (e.g., Stripe keys, server IP) for secure deployment.

### Feature Specifications

- **Users App**: Custom user model, payment tracking.
- **LMS App**: Core models for courses, lessons, subscriptions. Courses display nested lesson data, subscription status, and lesson count.
- **Subscription System**: API endpoint to toggle course subscriptions.
- **Payment System**: Supports cash, bank transfer, and Stripe integration for checkout and status checks.
- **Permissions System**: Custom permissions for users, moderators, and owners.
- **Celery Integration**: Asynchronous email notifications and periodic user blocking.

## External Dependencies

- **PostgreSQL**: Primary database.
- **Redis**: Message broker for Celery (local development).
- **Django REST Framework Simple JWT**: JWT authentication.
- **django-cors-headers**: CORS middleware.
- **Stripe**: Payment processing.
- **drf-spectacular**: OpenAPI 3.0 documentation.
- **Poetry**: Dependency management.