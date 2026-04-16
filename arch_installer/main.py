"""Оркестратор установки Arch Linux.

Управляет последовательностью этапов, обработкой ошибок
и передачей UI-объекта во все компоненты.
"""

from __future__ import annotations

import logging
import signal
import sys
import traceback
from typing import TYPE_CHECKING

from rich.console import Console

from .config import InstallConfig
from .constants import LOG_FILE, MOUNT_POINT, TOTAL_STAGES
from .exceptions import InstallerError, StageError, UserAbort
from .i18n import set_lang, t
from .stages import STAGE_ORDER
from .ui.banner import show_banner, wait_for_enter
from .ui.error_screen import show_error_screen
from .ui.progress import ProgressUI
from .ui.summary import show_final_screen
from .ui.theme import INSTALLER_THEME
from .ui.wizard import run_wizard
from .utils.logger import setup_logging
from .utils import shell as shell_mod

if TYPE_CHECKING:
    from .stages.base_stage import BaseStage

logger = logging.getLogger(__name__)


def _cleanup_mounts() -> None:
    """Размонтировать /mnt при аварийном выходе."""
    import subprocess

    if MOUNT_POINT.is_mount():
        logger.info("Размонтирование %s...", MOUNT_POINT)
        subprocess.run(
            ["umount", "-R", str(MOUNT_POINT)],
            capture_output=True,
        )


def _signal_handler(signum: int, frame: object) -> None:
    """Обработка Ctrl+C — корректный выход с откатом."""
    _cleanup_mounts()
    console = Console(theme=INSTALLER_THEME)
    console.print("\n[warning]Установка прервана пользователем.[/warning]")
    console.print(f"[muted]Лог сохранён: {LOG_FILE}[/muted]")
    sys.exit(130)


def run_installer(config: InstallConfig) -> None:
    """Главная точка входа установщика.

    Args:
        config: Конфигурация с начальными параметрами
                (demo_mode, debug, lang).
    """
    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Настраиваем логирование
    setup_logging(debug=config.debug)

    # Создаём консоль с темой
    console = Console(theme=INSTALLER_THEME)

    # Устанавливаем язык
    set_lang(config.lang)

    logger.info("Запуск Arch Installer (demo=%s, debug=%s)", config.demo_mode, config.debug)

    try:
        # Стартовый баннер
        show_banner(console)
        wait_for_enter(console)

        # Визард — заполняет конфигурацию
        config = run_wizard(console, config)
        set_lang(config.lang)

        logger.info("Конфигурация: disk=%s, user=%s, uefi=%s", config.disk, config.username, config.is_uefi)

        # Создаём UI прогресса
        progress_ui = ProgressUI(total_stages=TOTAL_STAGES)

        # Привязываем UI к модулю shell
        shell_mod.set_ui(progress_ui)

        # Создаём экземпляры этапов
        stages: list[BaseStage] = []
        for stage_cls in STAGE_ORDER:
            stages.append(stage_cls(config=config, ui=progress_ui))

        # Запускаем все этапы
        progress_ui.start()

        completed_stages = 0
        elapsed_total = 0.0

        try:
            for i, stage in enumerate(stages):
                stage_num = i + 2  # Этапы 2-14 (0=preflight, 1=wizard уже выполнены)
                stage_name = t(f"stage.{stage_num}")
                progress_ui.set_stage(stage_num, stage_name)

                logger.info("Начало этапа %d: %s", stage_num, stage_name)

                while True:
                    try:
                        stage.run()
                        completed_stages += 1
                        logger.info("Этап %d завершён: %s", stage_num, stage_name)
                        break

                    except StageError as e:
                        logger.error("Ошибка на этапе %d: %s", stage_num, e)

                        # Останавливаем live-дисплей для диалога ошибки
                        progress_ui.stop()

                        # Читаем последние строки лога
                        log_lines = _read_last_log_lines(10)

                        action = show_error_screen(
                            console=console,
                            stage_name=stage_name,
                            error_msg=str(e),
                            log_lines=log_lines,
                            skippable=stage.skippable,
                        )

                        if action == "retry":
                            logger.info("Повтор этапа %d", stage_num)
                            progress_ui.start()
                            continue
                        elif action == "skip":
                            logger.warning("Этап %d пропущен", stage_num)
                            progress_ui.start()
                            break
                        else:  # abort
                            raise UserAbort("Пользователь прервал установку")

        finally:
            elapsed_total = progress_ui.get_elapsed()
            progress_ui.stop()

        # Финальный экран
        package_count = _get_package_count(config)
        system_size = _get_system_size(config)

        action = show_final_screen(
            console=console,
            elapsed_seconds=elapsed_total,
            package_count=package_count,
            system_size=system_size,
        )

        if action == "reboot" and not config.demo_mode:
            import subprocess
            subprocess.run(["reboot"])

    except UserAbort:
        _cleanup_mounts()
        console.print("\n[warning]Установка отменена.[/warning]")
        console.print(f"[muted]Лог сохранён: {LOG_FILE}[/muted]")
        sys.exit(1)

    except InstallerError as e:
        logger.critical("Критическая ошибка: %s", e, exc_info=True)
        _cleanup_mounts()
        console.print(f"\n[error]Критическая ошибка: {e}[/error]")
        console.print(f"[muted]Подробности в логе: {LOG_FILE}[/muted]")
        sys.exit(1)

    except Exception as e:
        logger.critical("Непредвиденная ошибка: %s", e, exc_info=True)
        _cleanup_mounts()
        console.print(f"\n[error]Непредвиденная ошибка: {e}[/error]")
        console.print(f"[muted]Traceback сохранён в: {LOG_FILE}[/muted]")
        traceback.print_exc()
        sys.exit(1)


def _read_last_log_lines(n: int) -> list[str]:
    """Прочитать последние N строк из лог-файла."""
    try:
        text = LOG_FILE.read_text(encoding="utf-8")
        lines = text.strip().splitlines()
        return lines[-n:]
    except (OSError, ValueError):
        return []


def _get_package_count(config: InstallConfig) -> int:
    """Получить количество установленных пакетов."""
    if config.demo_mode:
        return 1247

    import subprocess

    try:
        result = subprocess.run(
            ["arch-chroot", str(MOUNT_POINT), "pacman", "-Q"],
            capture_output=True,
            text=True,
        )
        return len(result.stdout.strip().splitlines())
    except Exception:
        return 0


def _get_system_size(config: InstallConfig) -> str:
    """Получить размер установленной системы."""
    if config.demo_mode:
        return "8.3 GiB"

    import subprocess

    try:
        result = subprocess.run(
            ["du", "-sh", str(MOUNT_POINT)],
            capture_output=True,
            text=True,
        )
        return result.stdout.split()[0]
    except Exception:
        return "N/A"
