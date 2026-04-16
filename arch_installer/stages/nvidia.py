"""Установка проприетарного драйвера NVIDIA.

Устанавливает пакеты NVIDIA, настраивает mkinitcpio
(модули, хуки), создаёт конфигурации modprobe,
черный список nouveau и pacman-хук для обновлений.
"""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path

from ..constants import MOUNT_POINT, NVIDIA_PACKAGES
from ..exceptions import StageError
from ..utils.chroot import chroot_run, write_file_in_chroot
from .base_stage import BaseStage

# Путь к ассетам проекта (относительно корня репозитория)
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


class NvidiaStage(BaseStage):
    """Этап установки драйвера NVIDIA.

    Устанавливает проприетарный драйвер NVIDIA, настраивает
    загрузку модулей в initramfs и блокирует nouveau.
    """

    name = "Драйвер NVIDIA"
    weight = 3
    skippable = True

    def run(self) -> None:
        """Установить и настроить драйвер NVIDIA.

        Raises:
            StageError: При ошибке установки или конфигурации.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        # Установка пакетов NVIDIA
        packages_str = " ".join(NVIDIA_PACKAGES)
        self.ui.log_command(f"pacman -S --noconfirm {packages_str}")
        chroot_run(["pacman", "-S", "--noconfirm"] + NVIDIA_PACKAGES)
        self.ui.log_success("Пакеты NVIDIA установлены")

        # Добавление модулей NVIDIA в mkinitcpio.conf
        self._configure_mkinitcpio()

        # Создание конфигурации modprobe для NVIDIA
        self._create_nvidia_modprobe()

        # Блокировка драйвера nouveau
        self._blacklist_nouveau()

        # Копирование pacman-хука для автообновления initramfs
        self._install_nvidia_hook()

        # Пересборка initramfs
        self.ui.log_command("mkinitcpio -P")
        chroot_run(["mkinitcpio", "-P"])
        self.ui.log_success("initramfs пересобран")

    def _configure_mkinitcpio(self) -> None:
        """Настройка mkinitcpio.conf: добавление модулей NVIDIA, удаление kms."""
        mkinitcpio_conf = MOUNT_POINT / "etc" / "mkinitcpio.conf"
        self.ui.log_command("Настройка mkinitcpio.conf (MODULES и HOOKS)")

        content = mkinitcpio_conf.read_text(encoding="utf-8")

        # Добавляем модули NVIDIA в строку MODULES
        nvidia_modules = "nvidia nvidia_modeset nvidia_uvm nvidia_drm"

        def _replace_modules(m: re.Match[str]) -> str:
            """Вставить nvidia-модули в MODULES=(...)."""
            existing = m.group(1).strip()
            if existing:
                return f"MODULES=({existing} {nvidia_modules})"
            return f"MODULES=({nvidia_modules})"

        content = re.sub(
            r'^MODULES=\(([^)]*)\)',
            _replace_modules,
            content,
            flags=re.MULTILINE,
        )

        # Удаляем kms из HOOKS (несовместим с NVIDIA) и нормализуем пробелы
        def _remove_kms(m: re.Match[str]) -> str:
            """Удалить kms из списка HOOKS."""
            hooks = m.group(1)
            hooks = re.sub(r'\bkms\b', '', hooks)
            hooks = re.sub(r'\s+', ' ', hooks).strip()
            return f"HOOKS=({hooks})"

        content = re.sub(
            r'^HOOKS=\(([^)]*)\)',
            _remove_kms,
            content,
            flags=re.MULTILINE,
        )

        mkinitcpio_conf.write_text(content, encoding="utf-8")
        self.ui.log_success(
            "MODULES: добавлены nvidia-модули, kms удалён из HOOKS"
        )

    def _create_nvidia_modprobe(self) -> None:
        """Создание конфигурации modprobe для NVIDIA DRM."""
        nvidia_conf = (
            "# Включаем модесеттинг NVIDIA для Wayland и DRM\n"
            "options nvidia_drm modeset=1\n"
            "options nvidia_drm fbdev=1\n"
            "options nvidia NVreg_PreserveVideoMemoryAllocations=1\n"
        )
        self.ui.log_command("Запись /etc/modprobe.d/nvidia.conf")
        write_file_in_chroot("/etc/modprobe.d/nvidia.conf", nvidia_conf)
        self.ui.log_success("Конфигурация modprobe NVIDIA создана")

    def _blacklist_nouveau(self) -> None:
        """Блокировка драйвера nouveau."""
        blacklist_content = (
            "# Блокируем открытый драйвер nouveau (конфликт с NVIDIA)\n"
            "blacklist nouveau\n"
            "options nouveau modeset=0\n"
        )
        self.ui.log_command("Запись /etc/modprobe.d/blacklist-nouveau.conf")
        write_file_in_chroot(
            "/etc/modprobe.d/blacklist-nouveau.conf",
            blacklist_content,
        )
        self.ui.log_success("Драйвер nouveau заблокирован")

    def _install_nvidia_hook(self) -> None:
        """Копирование pacman-хука NVIDIA из ассетов."""
        src = ASSETS_DIR / "pacman" / "nvidia.hook"
        dst = MOUNT_POINT / "etc" / "pacman.d" / "hooks" / "nvidia.hook"

        self.ui.log_command("Копирование nvidia.hook в /etc/pacman.d/hooks/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        self.ui.log_success("Pacman-хук NVIDIA установлен")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки NVIDIA."""
        packages_str = " ".join(NVIDIA_PACKAGES)
        self.ui.log_command(f"pacman -S --noconfirm {packages_str}")
        for i, pkg in enumerate(NVIDIA_PACKAGES, 1):
            self.ui.log_command(f"  Установка {pkg} ({i}/{len(NVIDIA_PACKAGES)})")
            time.sleep(0.3)
        self.ui.log_success("Пакеты NVIDIA установлены")

        self.ui.log_command("Настройка mkinitcpio.conf (MODULES и HOOKS)")
        time.sleep(0.3)
        self.ui.log_success(
            "MODULES: добавлены nvidia-модули, kms удалён из HOOKS"
        )

        self.ui.log_command("Запись /etc/modprobe.d/nvidia.conf")
        time.sleep(0.2)
        self.ui.log_success("Конфигурация modprobe NVIDIA создана")

        self.ui.log_command("Запись /etc/modprobe.d/blacklist-nouveau.conf")
        time.sleep(0.2)
        self.ui.log_success("Драйвер nouveau заблокирован")

        self.ui.log_command("Копирование nvidia.hook в /etc/pacman.d/hooks/")
        time.sleep(0.2)
        self.ui.log_success("Pacman-хук NVIDIA установлен")

        self.ui.log_command("mkinitcpio -P")
        time.sleep(1.0)
        self.ui.log_success("initramfs пересобран")
