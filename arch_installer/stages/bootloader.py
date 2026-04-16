"""Установка и настройка загрузчика GRUB.

Устанавливает GRUB для UEFI или BIOS, генерирует конфигурацию.
Поддерживает обнаружение других ОС через os-prober.
"""

from __future__ import annotations

import time

from ..exceptions import StageError
from ..utils.chroot import chroot_run
from .base_stage import BaseStage


class BootloaderStage(BaseStage):
    """Этап установки загрузчика GRUB.

    UEFI: grub-install --target=x86_64-efi с EFI-директорией /boot.
    BIOS: grub-install --target=i386-pc на указанный диск.
    """

    name = "Загрузчик"
    weight = 2
    skippable = False

    def run(self) -> None:
        """Установить GRUB и сгенерировать конфигурацию.

        Raises:
            StageError: При ошибке установки загрузчика.
        """
        self.ui.set_stage(self.name)

        if self.config.demo_mode:
            self._run_demo()
            return

        # Установка пакетов загрузчика
        self.ui.log_command("pacman -S --noconfirm grub efibootmgr os-prober")
        chroot_run([
            "pacman", "-S", "--noconfirm",
            "grub", "efibootmgr", "os-prober",
        ])
        self.ui.log_success("Пакеты загрузчика установлены")

        if self.config.is_uefi:
            self._install_uefi()
        else:
            self._install_bios()

        # Генерация конфигурации GRUB
        self.ui.log_command("grub-mkconfig -o /boot/grub/grub.cfg")
        chroot_run(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
        self.ui.log_success("Конфигурация GRUB сгенерирована")

    def _install_uefi(self) -> None:
        """Установка GRUB для UEFI-системы."""
        self.ui.log_command(
            "grub-install --target=x86_64-efi "
            "--efi-directory=/boot --bootloader-id=GRUB"
        )
        chroot_run([
            "grub-install",
            "--target=x86_64-efi",
            "--efi-directory=/boot",
            "--bootloader-id=GRUB",
        ])
        self.ui.log_success("GRUB установлен (UEFI)")

    def _install_bios(self) -> None:
        """Установка GRUB для BIOS-системы."""
        disk = self.config.disk
        self.ui.log_command(
            f"grub-install --target=i386-pc {disk}"
        )
        chroot_run([
            "grub-install",
            "--target=i386-pc",
            disk,
        ])
        self.ui.log_success("GRUB установлен (BIOS)")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки загрузчика."""
        self.ui.log_command("pacman -S --noconfirm grub efibootmgr os-prober")
        time.sleep(0.8)
        self.ui.log_success("Пакеты загрузчика установлены")

        if self.config.is_uefi:
            self.ui.log_command(
                "grub-install --target=x86_64-efi "
                "--efi-directory=/boot --bootloader-id=GRUB"
            )
            time.sleep(0.5)
            self.ui.log_success("GRUB установлен (UEFI)")
        else:
            disk = self.config.disk or "/dev/sda"
            self.ui.log_command(f"grub-install --target=i386-pc {disk}")
            time.sleep(0.5)
            self.ui.log_success("GRUB установлен (BIOS)")

        self.ui.log_command("grub-mkconfig -o /boot/grub/grub.cfg")
        time.sleep(0.6)
        self.ui.log_success("Конфигурация GRUB сгенерирована")
