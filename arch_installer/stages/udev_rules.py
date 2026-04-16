"""Установка udev-правил для микроконтроллеров.

Копирует файл правил для USB-устройств (Arduino, STM32, ESP32
и др.) из ассетов и создаёт группу plugdev.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from ..constants import MOUNT_POINT
from ..exceptions import StageError
from ..utils.chroot import chroot_run
from .base_stage import BaseStage

# Путь к ассетам проекта
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


class UdevRulesStage(BaseStage):
    """Этап установки udev-правил для микроконтроллеров.

    Копирует правила доступа к USB-устройствам (отладчики,
    программаторы, платы разработки) и настраивает группу plugdev.
    """

    name = "Udev-правила микроконтроллеров"
    weight = 1
    skippable = True

    def run(self) -> None:
        """Скопировать udev-правила и настроить группу plugdev.

        Raises:
            StageError: При ошибке копирования файлов.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        # Путь к файлу правил в ассетах
        src = ASSETS_DIR / "udev" / "99-microcontrollers.rules"
        dst = MOUNT_POINT / "etc" / "udev" / "rules.d" / "99-microcontrollers.rules"

        # Создаём директорию назначения, если её нет
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Копируем файл правил
        self.ui.log_command(
            "Копирование 99-microcontrollers.rules -> /etc/udev/rules.d/"
        )
        shutil.copy2(src, dst)
        self.ui.log_success("Udev-правила скопированы")

        # Создаём группу plugdev (если ещё не создана)
        self.ui.log_command("groupadd -f plugdev")
        chroot_run(["groupadd", "-f", "plugdev"])
        self.ui.log_success("Группа plugdev создана")

        # Добавляем пользователя в группу plugdev
        username = self.config.username
        self.ui.log_command(f"usermod -aG plugdev {username}")
        chroot_run(["usermod", "-aG", "plugdev", username])
        self.ui.log_success(
            f"Пользователь {username} добавлен в группу plugdev"
        )

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки udev-правил."""
        self.ui.log_command(
            "Копирование 99-microcontrollers.rules -> /etc/udev/rules.d/"
        )
        time.sleep(0.3)
        self.ui.log_success("Udev-правила скопированы")

        self.ui.log_command("groupadd -f plugdev")
        time.sleep(0.2)
        self.ui.log_success("Группа plugdev создана")

        username = self.config.username or "user"
        self.ui.log_command(f"usermod -aG plugdev {username}")
        time.sleep(0.2)
        self.ui.log_success(
            f"Пользователь {username} добавлен в группу plugdev"
        )
