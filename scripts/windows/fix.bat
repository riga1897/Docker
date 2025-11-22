@echo off
REM Скрипт для автоматического исправления проблем в коде
REM Использование: scripts\windows\fix.bat или poetry run fix

echo 🔧 Автоматическое исправление кода...
echo.

echo 1️⃣  Ruff (автоисправление)...
poetry run ruff check --fix users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Ruff: исправлено
echo.

echo 2️⃣  Black (форматирование)...
poetry run black users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Black: отформатировано
echo.

echo 3️⃣  Isort (сортировка импортов)...
poetry run isort users/ lms/ config/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Isort: отсортировано
echo.

echo 🎉 Код автоматически исправлен!
echo.
echo 💡 Теперь запустите: poetry run check
