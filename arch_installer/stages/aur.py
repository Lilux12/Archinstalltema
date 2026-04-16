"""Установка AUR-хелпера yay и настройка автообновлений.

Собирает yay из AUR от имени пользователя, копирует systemd
timer/service файлы для еженедельного обновления системы.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from ..constants import MOUNT_POINT
from ..exceptions import StageError
from ..utils.chroot import chroot_run, enable_service
from ..utils.shell import run
from .base_stage import BaseStage

# Путь к ассетам проекта
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


class AurStage(BaseStage):
    """Этап установки AUR-хелпера yay и автообновлений.

    Клонирует и собирает yay из AUR от имени созданного
    пользователя. Настраивает systemd-таймер для еженедельного
    обновления всех пакетов (pacman + AUR).
    """

    name = "AUR helper и авто-обновления"
    weight = 3
    skippable = True

    def run(self) -> None:
        """Установить yay и настроить автообновление.

        Raises:
            StageError: При ошибке сборки yay или настройки таймера.
        """
        self.ui.set_stage(self.name)

        if self.config.demo_mode:
            self._run_demo()
            return

        username = self.config.username

        # Установка yay из AUR
        self._install_yay(username)

        # Настройка systemd-таймера для автообновлений
        self._setup_auto_update(username)

        self.ui.log_success("AUR helper и автообновления настроены")

    def _install_yay(self, username: str) -> None:
        """Сборка и установка yay из AUR.

        Клонирует репозиторий yay, собирает пакет от имени
        пользователя и устанавливает его.

        Args:
            username: Имя пользователя для сборки пакета.
        """
        # Временная настройка sudo без пароля для сборки
        # (необходимо для makepkg, который не работает от root)
        self.ui.log_command("Временная настройка sudo для сборки yay")
        tmp_sudoers = MOUNT_POINT / "etc" / "sudoers.d" / "99-yay-build"
        tmp_sudoers.parent.mkdir(parents=True, exist_ok=True)
        tmp_sudoers.write_text(
            f"{username} ALL=(ALL) NOPASSWD: ALL\n",
            encoding="utf-8",
        )
        tmp_sudoers.chmod(0o440)

        try:
            # Клонирование репозитория yay
            self.ui.log_command("git clone https://aur.archlinux.org/yay.git")
            chroot_run(
                f"su - {username} -c 'cd /tmp && git clone https://aur.archlinux.org/yay.git'"
            )
            self.ui.log_success("Репозиторий yay склонирован")

            # Сборка и установка yay
            self.ui.log_command("makepkg -si --noconfirm (yay)")
            chroot_run(
                f"su - {username} -c 'cd /tmp/yay && makepkg -si --noconfirm'"
            )
            self.ui.log_success("yay установлен")

            # Очистка директории сборки
            self.ui.log_command("Очистка /tmp/yay")
            chroot_run(["rm", "-rf", "/tmp/yay"])

        finally:
            # Удаляем временную запись sudoers
            if tmp_sudoers.exists():
                tmp_sudoers.unlink()
                self.ui.log_success("Временная запись sudoers удалена")

    def _setup_auto_update(self, username: str) -> None:
        """Настройка systemd-таймера для автообновлений.

        Копирует service и timer файлы из ассетов, заменяет
        плейсхолдер USERNAME_PLACEHOLDER на реальное имя
        пользователя и включает таймер.

        Args:
            username: Имя пользователя для подстановки в service.
        """
        systemd_dir = MOUNT_POINT / "etc" / "systemd" / "system"
        systemd_dir.mkdir(parents=True, exist_ok=True)

        # Копирование и настройка service-файла
        service_src = ASSETS_DIR / "systemd" / "system-update.service"
        service_dst = systemd_dir / "system-update.service"

        self.ui.log_command("Копирование system-update.service")
        service_content = service_src.read_text(encoding="utf-8")
        # Замена плейсхолдера на реальное имя пользователя
        service_content = service_content.replace(
            "USERNAME_PLACEHOLDER", username
        )
        service_dst.write_text(service_content, encoding="utf-8")
        self.ui.log_success("system-update.service настроен")

        # Копирование timer-файла
        timer_src = ASSETS_DIR / "systemd" / "system-update.timer"
        timer_dst = systemd_dir / "system-update.timer"

        self.ui.log_command("Копирование system-update.timer")
        shutil.copy2(timer_src, timer_dst)
        self.ui.log_success("system-update.timer скопирован")

        # Включение таймера
        self.ui.log_command("systemctl enable system-update.timer")
        enable_service("system-update.timer")
        self.ui.log_success("Таймер автообновления включён (каждое воскресенье 03:00)")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки yay и автообновлений."""
        username = self.config.username or "user"

        self.ui.log_command("Временная настройка sudo для сборки yay")
        time.sleep(0.2)
        self.ui.log_success("Временная запись sudoers создана")

        self.ui.log_command("git clone https://aur.archlinux.org/yay.git")
        time.sleep(0.8)
        self.ui.log_success("Репозиторий yay склонирован")

        self.ui.log_command("makepkg -si --noconfirm (yay)")
        time.sleep(1.5)
        self.ui.log_success("yay установлен")

        self.ui.log_command("Очистка /tmp/yay")
        time.sleep(0.2)
        self.ui.log_success("Временная запись sudoers удалена")

        self.ui.log_command("Копирование system-update.service")
        time.sleep(0.2)
        self.ui.log_success(f"system-update.service настроен (User={username})")

        self.ui.log_command("Копирование system-update.timer")
        time.sleep(0.2)
        self.ui.log_success("system-update.timer скопирован")

        self.ui.log_command("systemctl enable system-update.timer")
        time.sleep(0.2)
        self.ui.log_success("Таймер автообновления включён (каждое воскресенье 03:00)")

        self.ui.log_success("AUR helper и автообновления настроены")
