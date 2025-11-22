"""Запуск всех проверок качества кода через Poetry."""
import subprocess
import sys


def main() -> None:
    """Точка входа для команды 'poetry run check'."""
    result = subprocess.run(["bash", "scripts/check.sh"], cwd=".")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
