"""Системная конфигурация внутри chroot.

Настраивает часовой пояс, локаль, консоль, имя хоста, hosts,
пароли root и пользователя, sudoers, сеть (NetworkManager).
"""

from __future__ import annotations

import re
import time

from ..constants import MOUNT_POINT, USER_GROUPS
from ..exceptions import StageError
from ..utils.chroot import chroot_run, enable_service, write_file_in_chroot
from .base_stage import BaseStage


class SystemConfigStage(BaseStage):
    """Этап системной конфигурации в chroot.

    Выполняет все базовые настройки операционной системы
    после pacstrap: локаль, часовой пояс, пользователи и т.д.
    """

    name = "Системная конфигурация"
    weight = 2
    skippable = False

    def run(self) -> None:
        """Настроить систему внутри chroot.

        Raises:
            StageError: При ошибке выполнения команд конфигурации.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        self._setup_timezone()
        self._setup_locale()
        self._setup_vconsole()
        self._setup_hostname()
        self._setup_hosts()
        self._setup_root_password()
        self._setup_user()
        self._setup_plugdev_group()
        self._setup_sudoers()
        self._enable_network()

        self.ui.log_success("Системная конфигурация завершена")

    def _setup_timezone(self) -> None:
        """Настройка часового пояса и аппаратных часов."""
        tz = self.config.timezone
        self.ui.log_command(f"ln -sf /usr/share/zoneinfo/{tz} /etc/localtime")
        chroot_run(["ln", "-sf", f"/usr/share/zoneinfo/{tz}", "/etc/localtime"])

        self.ui.log_command("hwclock --systohc")
        chroot_run(["hwclock", "--systohc"])
        self.ui.log_success(f"Часовой пояс: {tz}")

    def _setup_locale(self) -> None:
        """Настройка системной локали и генерация locale."""
        locale = self.config.locale

        # Раскомментируем нужную локаль в locale.gen
        locale_gen_path = MOUNT_POINT / "etc" / "locale.gen"
        self.ui.log_command(f"Раскомментирование {locale} в locale.gen")
        content = locale_gen_path.read_text(encoding="utf-8")
        # Раскомментируем и UTF-8 вариант
        content = re.sub(
            rf"^#\s*({re.escape(locale)}\s+UTF-8)",
            r"\1",
            content,
            flags=re.MULTILINE,
        )
        # Также раскомментируем en_US.UTF-8 как fallback
        content = re.sub(
            r"^#\s*(en_US\.UTF-8\s+UTF-8)",
            r"\1",
            content,
            flags=re.MULTILINE,
        )
        locale_gen_path.write_text(content, encoding="utf-8")

        # Генерация локалей
        self.ui.log_command("locale-gen")
        chroot_run(["locale-gen"])

        # Запись locale.conf
        self.ui.log_command(f"Запись /etc/locale.conf: LANG={locale}")
        write_file_in_chroot("/etc/locale.conf", f"LANG={locale}\n")
        self.ui.log_success(f"Локаль: {locale}")

    def _setup_vconsole(self) -> None:
        """Настройка консольной раскладки клавиатуры."""
        self.ui.log_command("Запись /etc/vconsole.conf")
        write_file_in_chroot("/etc/vconsole.conf", "KEYMAP=us\n")
        self.ui.log_success("Консольная раскладка: us")

    def _setup_hostname(self) -> None:
        """Настройка имени хоста."""
        hostname = self.config.hostname
        self.ui.log_command(f"Запись /etc/hostname: {hostname}")
        write_file_in_chroot("/etc/hostname", f"{hostname}\n")
        self.ui.log_success(f"Имя хоста: {hostname}")

    def _setup_hosts(self) -> None:
        """Настройка файла /etc/hosts."""
        hostname = self.config.hostname
        hosts_content = (
            "127.0.0.1   localhost\n"
            "::1         localhost\n"
            f"127.0.1.1   {hostname}.localdomain {hostname}\n"
        )
        self.ui.log_command("Запись /etc/hosts")
        write_file_in_chroot("/etc/hosts", hosts_content)
        self.ui.log_success("Файл hosts настроен")

    def _setup_root_password(self) -> None:
        """Установка пароля root."""
        self.ui.log_command("Установка пароля root")
        chroot_run(
            ["chpasswd"],
            input_data=f"root:{self.config.root_password}\n",
        )
        self.ui.log_success("Пароль root установлен")

    def _setup_user(self) -> None:
        """Создание пользователя и установка пароля."""
        username = self.config.username
        groups_str = ",".join(USER_GROUPS)

        # Создание пользователя с домашней директорией и группами
        self.ui.log_command(
            f"useradd -m -G {groups_str} -s /bin/bash {username}"
        )
        chroot_run([
            "useradd", "-m",
            "-G", groups_str,
            "-s", "/bin/bash",
            username,
        ])
        self.ui.log_success(f"Пользователь {username} создан")

        # Установка пароля пользователя
        self.ui.log_command(f"Установка пароля для {username}")
        chroot_run(
            ["chpasswd"],
            input_data=f"{username}:{self.config.user_password}\n",
        )
        self.ui.log_success(f"Пароль для {username} установлен")

    def _setup_plugdev_group(self) -> None:
        """Создание группы plugdev и добавление пользователя."""
        username = self.config.username
        self.ui.log_command("groupadd -f plugdev")
        chroot_run(["groupadd", "-f", "plugdev"])

        self.ui.log_command(f"usermod -aG plugdev {username}")
        chroot_run(["usermod", "-aG", "plugdev", username])
        self.ui.log_success(f"Пользователь {username} добавлен в группу plugdev")

    def _setup_sudoers(self) -> None:
        """Настройка sudo для группы wheel."""
        # Основной файл sudoers через drop-in для безопасности
        sudoers_content = (
            "## Разрешаем группе wheel использовать sudo\n"
            "%wheel ALL=(ALL:ALL) ALL\n"
        )
        self.ui.log_command("Запись /etc/sudoers.d/10-wheel")
        write_file_in_chroot("/etc/sudoers.d/10-wheel", sudoers_content)

        # NOPASSWD для pacman и yay (удобство обновлений)
        nopasswd_content = (
            "## Разрешаем pacman и yay без пароля для группы wheel\n"
            "%wheel ALL=(ALL) NOPASSWD: /usr/bin/pacman, /usr/bin/yay\n"
        )
        self.ui.log_command("Запись /etc/sudoers.d/20-pacman-nopasswd")
        write_file_in_chroot("/etc/sudoers.d/20-pacman-nopasswd", nopasswd_content)

        # Устанавливаем корректные права (440)
        chroot_run(["chmod", "440", "/etc/sudoers.d/10-wheel"])
        chroot_run(["chmod", "440", "/etc/sudoers.d/20-pacman-nopasswd"])

        # Проверяем синтаксис sudoers
        self.ui.log_command("visudo -c")
        chroot_run(["visudo", "-c"])
        self.ui.log_success("sudo настроен для группы wheel")

    def _enable_network(self) -> None:
        """Включение NetworkManager."""
        self.ui.log_command("systemctl enable NetworkManager")
        enable_service("NetworkManager.service")
        self.ui.log_success("NetworkManager включён")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация системной конфигурации."""
        steps = [
            ("Настройка часового пояса", f"Часовой пояс: {self.config.timezone}"),
            ("locale-gen", f"Локаль: {self.config.locale}"),
            ("Запись /etc/vconsole.conf", "Консольная раскладка: us"),
            ("Запись /etc/hostname", f"Имя хоста: {self.config.hostname}"),
            ("Запись /etc/hosts", "Файл hosts настроен"),
            ("Установка пароля root", "Пароль root установлен"),
            (
                f"useradd -m -G {','.join(USER_GROUPS)} {self.config.username or 'user'}",
                f"Пользователь {self.config.username or 'user'} создан",
            ),
            (
                f"Установка пароля для {self.config.username or 'user'}",
                f"Пароль для {self.config.username or 'user'} установлен",
            ),
            ("groupadd -f plugdev", "Группа plugdev создана"),
            ("Запись /etc/sudoers.d/10-wheel", "sudo настроен для группы wheel"),
            ("systemctl enable NetworkManager", "NetworkManager включён"),
        ]

        for cmd, success_msg in steps:
            self.ui.log_command(cmd)
            time.sleep(0.2)
            self.ui.log_success(success_msg)

        self.ui.log_success("Системная конфигурация завершена")
