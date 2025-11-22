# 📜 Скрипты проекта

Эта директория содержит скрипты для автоматизации разработки, упорядоченные по платформам.

## 📁 Структура

```
scripts/
├── unix/          # Скрипты для Linux/Mac/WSL (bash)
│   ├── test_all.sh   # Запуск всех тестов + coverage
│   ├── check.sh      # Проверка качества кода
│   ├── fix.sh        # Автоисправление кода
│   └── watch.sh      # Watch-режим (автопроверка при изменении)
│
├── windows/       # Скрипты для Windows
│   ├── test_all.bat  # CMD версия
│   ├── test_all.ps1  # PowerShell версия
│   ├── check.bat     # CMD версия
│   ├── check.ps1     # PowerShell версия
│   ├── fix.bat       # CMD версия
│   └── fix.ps1       # PowerShell версия
│
└── Python модули (используются Poetry)
    ├── check.py      # Модуль для poetry run check
    └── fix.py        # Модуль для poetry run fix
```

---

## 🚀 Использование

### 🐧 Linux / macOS / WSL

```bash
# Все тесты (265 тестов + coverage)
./scripts/unix/test_all.sh

# Проверка качества кода
./scripts/unix/check.sh

# Автоисправление кода
./scripts/unix/fix.sh

# Watch-режим (автопроверка при изменении файлов)
./scripts/unix/watch.sh
```

### 🪟 Windows CMD

```cmd
REM Все тесты
scripts\windows\test_all.bat

REM Проверка качества кода
scripts\windows\check.bat

REM Автоисправление кода
scripts\windows\fix.bat
```

### 🪟 Windows PowerShell

```powershell
# Все тесты
.\scripts\windows\test_all.ps1

# Проверка качества кода
.\scripts\windows\check.ps1

# Автоисправление кода
.\scripts\windows\fix.ps1
```

### 📦 Через Poetry (кросс-платформенно)

```bash
# Все тесты (работает на всех ОС через Python)
# Примечание: использует Python модули, которые вызывают нужные команды
poetry run check  # Проверка качества
poetry run fix    # Автоисправление
```

### 🛠️ Через Makefile (только Linux/Mac/WSL)

```bash
make test           # Все тесты локально
make test-docker    # Тесты в Docker
make check          # Проверка качества кода
make fix            # Автоисправление
```

---

## 📋 Описание скриптов

### 🧪 test_all

**Что делает:**
1. Запускает Django APITestCase тесты (78 тестов)
2. Запускает pytest-django тесты (187 тестов)
3. Генерирует комбинированный coverage отчёт (87.68%)
4. Создаёт HTML отчёт в `htmlcov/index.html`

**Версии:**
- `unix/test_all.sh` — для Linux/Mac/WSL
- `windows/test_all.bat` — для Windows CMD
- `windows/test_all.ps1` — для Windows PowerShell

### ✅ check

**Что делает:**
1. Ruff — быстрая проверка багов и стиля
2. Mypy — проверка типов (100% type coverage)
3. Black — проверка форматирования (119 символов/строка)
4. Isort — проверка сортировки импортов
5. Flake8 — дополнительные проверки
6. Django system check

**Версии:**
- `unix/check.sh` — для Linux/Mac/WSL
- `windows/check.bat` — для Windows CMD
- `windows/check.ps1` — для Windows PowerShell
- `check.py` — Python модуль (через `poetry run check`)

### 🔧 fix

**Что делает:**
1. Ruff — автоисправление проблем
2. Black — автоформатирование кода
3. Isort — автосортировка импортов

**Версии:**
- `unix/fix.sh` — для Linux/Mac/WSL
- `windows/fix.bat` — для Windows CMD
- `windows/fix.ps1` — для Windows PowerShell
- `fix.py` — Python модуль (через `poetry run fix`)

### 👀 watch (только Unix)

**Что делает:**
- Отслеживает изменения в `users/`, `lms/`, `config/`
- Автоматически запускает ruff и mypy при сохранении файлов
- Требует `inotify-tools` (устанавливается автоматически)

**Версии:**
- `unix/watch.sh` — для Linux/Mac/WSL
- ⚠️ **Нет Windows версии** (требует inotify-tools, специфичная для Unix)

---

## 🔑 Рекомендации

### Для разработчиков на Windows:

**PowerShell (рекомендуется):**
```powershell
.\scripts\windows\test_all.ps1  # Цветной вывод
.\scripts\windows\check.ps1
.\scripts\windows\fix.ps1
```

**CMD (базовый):**
```cmd
scripts\windows\test_all.bat
scripts\windows\check.bat
scripts\windows\fix.bat
```

**Poetry (универсально):**
```bash
poetry run check
poetry run fix
```

### Для разработчиков на Linux/Mac:

**Bash скрипты (рекомендуется):**
```bash
./scripts/unix/test_all.sh
./scripts/unix/check.sh
./scripts/unix/fix.sh
./scripts/unix/watch.sh  # Bonus: автопроверка при изменении
```

**Makefile (ещё короче):**
```bash
make test
make check
make fix
```

### Для работы в Docker:

```bash
# Через Makefile (все ОС, если установлен make)
make test-docker

# Напрямую
docker-compose exec web ./scripts/unix/test_all.sh
docker-compose exec web ./scripts/unix/check.sh
```

---

## ⚠️ Важно

1. **Unix скрипты** (`*.sh`) требуют прав на выполнение:
   ```bash
   chmod +x scripts/unix/*.sh
   ```

2. **PowerShell скрипты** могут требовать разрешения на выполнение:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Python модули** (`check.py`, `fix.py`) используются автоматически через Poetry команды.

4. **Watch режим** (`watch.sh`) доступен **только на Unix** системах.

---

## 🎯 Быстрый выбор

| Ваша ОС | Рекомендуемый способ |
|---------|---------------------|
| **Windows** | `.\scripts\windows\*.ps1` (PowerShell) |
| **Linux/Mac** | `./scripts/unix/*.sh` (bash) или `make` |
| **WSL** | `./scripts/unix/*.sh` (bash) |
| **Docker** | `make test-docker` или `docker-compose exec web ./scripts/unix/*.sh` |
| **Любая** | `poetry run check` / `poetry run fix` (через Python) |
