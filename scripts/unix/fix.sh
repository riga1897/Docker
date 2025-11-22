#!/bin/bash
# Скрипт для автоматического исправления проблем в коде
# Использование: ./scripts/fix.sh или poetry run fix

set -e

echo "🔧 Автоматическое исправление кода..."
echo ""

echo "1️⃣  Ruff (автоисправление)..."
poetry run ruff check --fix users/ lms/ config/
echo "✅ Ruff: исправлено"
echo ""

echo "2️⃣  Black (форматирование)..."
poetry run black users/ lms/ config/
echo "✅ Black: отформатировано"
echo ""

echo "3️⃣  Isort (сортировка импортов)..."
poetry run isort users/ lms/ config/
echo "✅ Isort: отсортировано"
echo ""

echo "🎉 Код автоматически исправлен!"
echo ""
echo "💡 Теперь запустите: poetry run check"
