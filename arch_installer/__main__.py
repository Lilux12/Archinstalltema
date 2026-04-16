"""Точка входа: python -m arch_installer.

Обрабатывает аргументы командной строки и запускает установщик.
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    """Обработка CLI-аргументов и запуск установщика."""
    parser = argparse.ArgumentParser(
        prog="arch-installer",
        description="Персональный TUI-установщик Arch Linux",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Демо-режим: UI без реальных команд",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Режим отладки с расширенным логированием",
    )
    parser.add_argument(
        "--lang",
        choices=["ru", "en"],
        default="ru",
        help="Язык интерфейса (по умолчанию: ru)",
    )

    args = parser.parse_args()

    from .config import InstallConfig
    from .main import run_installer

    config = InstallConfig(
        lang=args.lang,
        demo_mode=args.demo,
        debug=args.debug,
    )

    run_installer(config)


if __name__ == "__main__":
    main()
