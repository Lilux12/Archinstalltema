"""Установка рабочего окружения GNOME.

Устанавливает пакеты GNOME и включает менеджер дисплеев GDM.
"""

from __future__ import annotations

import time

from ..constants import GNOME_PACKAGES
from ..exceptions import StageError
from ..utils.chroot import chroot_run, enable_service
from .base_stage import BaseStage


class GnomeStage(BaseStage):
    """Этап установки рабочего окружения GNOME.

    Устанавливает Xorg, GNOME Shell, GDM и вспомогательные
    приложения (Nautilus, Tweaks, расширения).
    """

    name = "Установка GNOME"
    weight = 4
    skippable = True

    def run(self) -> None:
        """Установить пакеты GNOME и включить GDM.

        Raises:
            StageError: При ошибке установки пакетов.
        """
        self.ui.set_stage(self.name)

        if self.config.demo_mode:
            self._run_demo()
            return

        # Установка пакетов GNOME
        packages_str = " ".join(GNOME_PACKAGES)
        self.ui.log_command(f"pacman -S --noconfirm {packages_str}")
        chroot_run(["pacman", "-S", "--noconfirm"] + GNOME_PACKAGES)
        self.ui.log_success(f"Пакеты GNOME установлены ({len(GNOME_PACKAGES)} шт.)")

        # Включение GDM (менеджер дисплеев)
        self.ui.log_command("systemctl enable gdm")
        enable_service("gdm.service")
        self.ui.log_success("GDM включён")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки GNOME."""
        packages_str = " ".join(GNOME_PACKAGES)
        self.ui.log_command(f"pacman -S --noconfirm {packages_str}")

        # Имитация установки пакетов по одному
        for i, pkg in enumerate(GNOME_PACKAGES, 1):
            self.ui.log_command(f"  Установка {pkg} ({i}/{len(GNOME_PACKAGES)})")
            time.sleep(0.3)

        self.ui.log_success(f"Пакеты GNOME установлены ({len(GNOME_PACKAGES)} шт.)")

        self.ui.log_command("systemctl enable gdm")
        time.sleep(0.2)
        self.ui.log_success("GDM включён")
