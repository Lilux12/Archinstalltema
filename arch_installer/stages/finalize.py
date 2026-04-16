"""Финализация установки.

Сохраняет лог установки, собирает статистику (количество
пакетов, размер системы) ДО размонтирования, затем
выполняет umount -R /mnt.
"""

from __future__ import annotations

import time
from pathlib import Path

from ..constants import LOG_FILE, MOUNT_POINT
from ..exceptions import StageError
from ..utils.chroot import chroot_run
from ..utils.shell import run
from .base_stage import BaseStage


class FinalizeStage(BaseStage):
    """Этап финализации установки.

    Сохраняет лог установки в целевую систему, собирает
    итоговую статистику и размонтирует /mnt.
    """

    name = "Финализация"
    weight = 1
    skippable = False

    def run(self) -> None:
        """Завершить установку: сохранить лог, собрать стату, размонтировать.

        Raises:
            StageError: При критической ошибке финализации.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        # Сохранение лога установки в целевую систему
        self._save_install_log()

        # Сбор статистики ДО размонтирования
        self._collect_stats()

        # Размонтирование /mnt
        self._unmount()

        self.ui.log_success("Установка завершена успешно")

    def _save_install_log(self) -> None:
        """Копирование лога установки в целевую систему."""
        self.ui.log_command("Сохранение лога установки")

        # Копируем лог в /var/log/ целевой системы
        log_dest = MOUNT_POINT / "var" / "log" / "arch_install.log"
        log_dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            if LOG_FILE.exists():
                log_content = LOG_FILE.read_text(encoding="utf-8")
                log_dest.write_text(log_content, encoding="utf-8")
                self.ui.log_success(
                    f"Лог сохранён: /var/log/arch_install.log "
                    f"({len(log_content)} байт)"
                )
            else:
                self.ui.log_command("Лог-файл не найден, пропуск")
        except OSError as e:
            # Ошибка копирования лога не критична
            self.ui.log_error(f"Не удалось сохранить лог: {e}")

    def _collect_stats(self) -> None:
        """Сбор статистики установленной системы.

        Собирает количество пакетов и размер системы ДО
        размонтирования /mnt.
        """
        self.ui.log_command("Сбор статистики установки")

        # Количество установленных пакетов
        try:
            result = chroot_run(
                ["pacman", "-Q"],
                capture=True,
                stream_to_ui=False,
            )
            pkg_count = len(result.stdout.strip().splitlines())
            self.ui.log_success(f"Установлено пакетов: {pkg_count}")
        except Exception:
            self.ui.log_command("Не удалось подсчитать пакеты")

        # Размер системы
        try:
            result = run(
                ["du", "-sh", str(MOUNT_POINT)],
                capture=True,
                stream_to_ui=False,
            )
            size = result.stdout.split()[0]
            self.ui.log_success(f"Размер системы: {size}")
        except Exception:
            self.ui.log_command("Не удалось определить размер системы")

    def _unmount(self) -> None:
        """Рекурсивное размонтирование /mnt."""
        self.ui.log_command(f"umount -R {MOUNT_POINT}")

        # Синхронизация файловых систем перед размонтированием
        run(["sync"])

        # Рекурсивное размонтирование
        run(["umount", "-R", str(MOUNT_POINT)])
        self.ui.log_success(f"{MOUNT_POINT} размонтирован")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация финализации."""
        self.ui.log_command("Сохранение лога установки")
        time.sleep(0.3)
        self.ui.log_success("Лог сохранён: /var/log/arch_install.log (42 KiB)")

        self.ui.log_command("Сбор статистики установки")
        time.sleep(0.5)
        self.ui.log_success("Установлено пакетов: 1247")
        self.ui.log_success("Размер системы: 8.3 GiB")

        self.ui.log_command("umount -R /mnt")
        time.sleep(0.3)
        self.ui.log_success("/mnt размонтирован")

        self.ui.log_success("Установка завершена успешно")
