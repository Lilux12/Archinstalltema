"""Включение репозитория multilib.

Раскомментирует секцию [multilib] в /etc/pacman.conf
и обновляет базу данных пакетов.
"""

from __future__ import annotations

import re
import time

from ..constants import MOUNT_POINT
from ..exceptions import StageError
from ..utils.chroot import chroot_run
from .base_stage import BaseStage


class MultilibStage(BaseStage):
    """Этап включения репозитория multilib.

    Необходим для установки 32-битных библиотек (lib32-*),
    в частности для NVIDIA и Steam.
    """

    name = "Multilib-репозиторий"
    weight = 1
    skippable = True

    def run(self) -> None:
        """Включить multilib и обновить базу пакетов.

        Raises:
            StageError: При ошибке редактирования pacman.conf
                или обновления базы.
        """
        self.ui.set_stage(self.name)

        if self.config.demo_mode:
            self._run_demo()
            return

        # Путь к pacman.conf внутри целевой системы
        pacman_conf = MOUNT_POINT / "etc" / "pacman.conf"

        # Раскомментирование секции [multilib]
        self.ui.log_command("Раскомментирование [multilib] в pacman.conf")
        content = pacman_conf.read_text(encoding="utf-8")

        # Регулярное выражение для раскомментирования блока [multilib]
        # Ищем закомментированный блок:
        # #[multilib]
        # #Include = /etc/pacman.d/mirrorlist
        content = re.sub(
            r"#\s*\[multilib\]\s*\n#\s*Include\s*=\s*/etc/pacman\.d/mirrorlist",
            "[multilib]\nInclude = /etc/pacman.d/mirrorlist",
            content,
        )

        pacman_conf.write_text(content, encoding="utf-8")
        self.ui.log_success("[multilib] раскомментирован в pacman.conf")

        # Обновление базы данных пакетов
        self.ui.log_command("pacman -Syy")
        chroot_run(["pacman", "-Syy", "--noconfirm"])
        self.ui.log_success("База данных пакетов обновлена")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация включения multilib."""
        self.ui.log_command("Раскомментирование [multilib] в pacman.conf")
        time.sleep(0.3)
        self.ui.log_success("[multilib] раскомментирован в pacman.conf")

        self.ui.log_command("pacman -Syy")
        time.sleep(0.8)
        self.ui.log_success("База данных пакетов обновлена")
