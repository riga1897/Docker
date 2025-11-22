"""Автоматическое исправление проблем в коде через Poetry."""
import subprocess
import sys


def main() -> None:
    """Точка входа для команды 'poetry run fix'."""
    result = subprocess.run(["bash", "scripts/fix.sh"], cwd=".")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
