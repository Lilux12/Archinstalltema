"""Установка базовой системы Arch Linux.

Синхронизация времени, настройка зеркал через reflector,
установка базовых пакетов через pacstrap, генерация fstab.
"""

from __future__ import annotations

import time

from ..constants import BASE_PACKAGES, MOUNT_POINT
from ..exceptions import StageError
from ..utils.shell import run
from .base_stage import BaseStage


class BaseInstallStage(BaseStage):
    """Этап установки базовой системы.

    Выполняет pacstrap с базовыми пакетами и генерирует fstab.
    """

    name = "Установка базовой системы"
    weight = 5
    skippable = False

    def run(self) -> None:
        """Установить базовую систему через pacstrap.

        Raises:
            StageError: При ошибке установки пакетов.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        # Синхронизация системных часов по NTP
        self.ui.log_command("timedatectl set-ntp true")
        run(["timedatectl", "set-ntp", "true"])
        self.ui.log_success("NTP-синхронизация включена")

        # Установка reflector (может отсутствовать в live-ISO)
        self.ui.log_command("pacman -Sy --noconfirm reflector")
        run(["pacman", "-Sy", "--noconfirm", "reflector"])
        self.ui.log_success("reflector установлен")

        # Настройка зеркал через reflector для ускорения загрузки
        self.ui.log_command("reflector — выбор быстрых зеркал")
        run([
            "reflector",
            "--country", "Russia,Germany,Finland",
            "--protocol", "https",
            "--sort", "rate",
            "--latest", "10",
            "--save", "/etc/pacman.d/mirrorlist",
        ])
        self.ui.log_success("Зеркала обновлены через reflector")

        # Установка базовых пакетов через pacstrap
        packages_str = " ".join(BASE_PACKAGES)
        self.ui.log_command(f"pacstrap -K /mnt {packages_str}")
        run(["pacstrap", "-K", str(MOUNT_POINT)] + BASE_PACKAGES)
        self.ui.log_success("Базовые пакеты установлены")

        # Генерация fstab на основе UUID
        self.ui.log_command("genfstab -U /mnt >> /mnt/etc/fstab")
        result = run(
            ["genfstab", "-U", str(MOUNT_POINT)],
            capture=True,
            stream_to_ui=False,
        )
        fstab_path = MOUNT_POINT / "etc" / "fstab"
        fstab_path.write_text(result.stdout, encoding="utf-8")
        self.ui.log_success("fstab сгенерирован")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки базовой системы."""
        # Имитация NTP
        self.ui.log_command("timedatectl set-ntp true")
        time.sleep(0.3)
        self.ui.log_success("NTP-синхронизация включена")

        # Имитация reflector
        self.ui.log_command("reflector — выбор быстрых зеркал")
        time.sleep(1.0)
        self.ui.log_success("Зеркала обновлены через reflector")

        # Имитация pacstrap
        packages_str = " ".join(BASE_PACKAGES)
        self.ui.log_command(f"pacstrap -K /mnt {packages_str}")

        # Имитация установки пакетов по одному
        for i, pkg in enumerate(BASE_PACKAGES, 1):
            self.ui.log_command(f"  Установка {pkg} ({i}/{len(BASE_PACKAGES)})")
            time.sleep(0.3)

        self.ui.log_success(f"Базовые пакеты установлены ({len(BASE_PACKAGES)} шт.)")

        # Имитация fstab
        self.ui.log_command("genfstab -U /mnt >> /mnt/etc/fstab")
        time.sleep(0.3)
        self.ui.log_success("fstab сгенерирован")
