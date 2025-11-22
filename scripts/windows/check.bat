@echo off
REM Скрипт для запуска всех проверок качества кода
REM Использование: scripts\windows\check.bat или poetry run check

echo 🔍 Запуск проверок качества кода...
echo.

echo 1️⃣  Ruff (быстрая проверка багов и стиля)...
poetry run ruff check users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Ruff: OK
echo.

echo 2️⃣  Mypy (проверка типов)...
poetry run mypy users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Mypy: OK
echo.

echo 3️⃣  Black (проверка форматирования)...
poetry run black --check users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Black: OK
echo.

echo 4️⃣  Isort (проверка сортировки импортов)...
poetry run isort --check-only users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Isort: OK
echo.

echo 5️⃣  Flake8 (дополнительные проверки)...
poetry run flake8 users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Flake8: OK
echo.

echo 6️⃣  Django system check...
poetry run python manage.py check
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Django check: OK
echo.

echo 🎉 Все проверки пройдены успешно!
