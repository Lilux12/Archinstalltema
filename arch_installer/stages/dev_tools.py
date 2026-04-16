"""Установка инструментов разработки.

Устанавливает компиляторы, языки программирования, виртуализацию,
Docker, отладчики и утилиты. Включает необходимые сервисы
и добавляет пользователя в группы разработчиков.
"""

from __future__ import annotations

import time

from ..constants import DEV_GROUPS, DEV_PACKAGES, DEV_SERVICES
from ..exceptions import StageError
from ..utils.chroot import chroot_run, enable_service
from .base_stage import BaseStage


class DevToolsStage(BaseStage):
    """Этап установки инструментов разработки.

    Устанавливает обширный набор dev-инструментов, включая
    языки (Python, Rust, Go, Node.js), компиляторы (GCC, Clang),
    виртуализацию (QEMU, libvirt) и контейнеризацию (Docker).
    """

    name = "Инструменты разработки"
    weight = 5
    skippable = True

    def run(self) -> None:
        """Установить dev-пакеты, включить сервисы, добавить группы.

        Raises:
            StageError: При ошибке установки пакетов или сервисов.
        """
        self.ui.set_stage(self.name)

        if self.config.demo_mode:
            self._run_demo()
            return

        # Установка пакетов разработки
        packages_str = " ".join(DEV_PACKAGES)
        self.ui.log_command(f"pacman -S --noconfirm {packages_str}")
        chroot_run(["pacman", "-S", "--noconfirm"] + DEV_PACKAGES)
        self.ui.log_success(f"Dev-пакеты установлены ({len(DEV_PACKAGES)} шт.)")

        # Включение сервисов (libvirtd, docker)
        for service in DEV_SERVICES:
            self.ui.log_command(f"systemctl enable {service}")
            enable_service(f"{service}.service")
            self.ui.log_success(f"Сервис {service} включён")

        # Добавление пользователя в группы разработчиков
        username = self.config.username
        for group in DEV_GROUPS:
            self.ui.log_command(f"usermod -aG {group} {username}")
            # Сначала создаём группу, если её нет
            chroot_run(["groupadd", "-f", group])
            chroot_run(["usermod", "-aG", group, username])
            self.ui.log_success(f"Пользователь {username} добавлен в группу {group}")

        self.ui.log_success("Инструменты разработки установлены")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки dev-инструментов."""
        packages_str = " ".join(DEV_PACKAGES[:5]) + " ..."
        self.ui.log_command(f"pacman -S --noconfirm {packages_str}")

        # Имитация установки пакетов (показываем каждый пятый)
        for i, pkg in enumerate(DEV_PACKAGES, 1):
            if i % 5 == 0 or i == len(DEV_PACKAGES):
                self.ui.log_command(
                    f"  Установка {pkg} ({i}/{len(DEV_PACKAGES)})"
                )
            time.sleep(0.1)

        self.ui.log_success(f"Dev-пакеты установлены ({len(DEV_PACKAGES)} шт.)")

        # Имитация включения сервисов
        for service in DEV_SERVICES:
            self.ui.log_command(f"systemctl enable {service}")
            time.sleep(0.2)
            self.ui.log_success(f"Сервис {service} включён")

        # Имитация добавления в группы
        username = self.config.username or "user"
        for group in DEV_GROUPS:
            self.ui.log_command(f"usermod -aG {group} {username}")
            time.sleep(0.1)

        groups_str = ", ".join(DEV_GROUPS)
        self.ui.log_success(
            f"Пользователь {username} добавлен в группы: {groups_str}"
        )

        self.ui.log_success("Инструменты разработки установлены")
