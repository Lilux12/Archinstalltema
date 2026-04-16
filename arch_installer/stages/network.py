"""Настройка сети и DNS.

Конфигурация NetworkManager для использования пользовательских
DNS-серверов, отключение systemd-resolved, настройка resolv.conf.
"""

from __future__ import annotations

import time

from ..constants import DNS_SERVERS, MOUNT_POINT
from ..exceptions import StageError
from ..utils.chroot import chroot_run, write_file_in_chroot
from .base_stage import BaseStage


class NetworkStage(BaseStage):
    """Этап настройки сети и DNS.

    Настраивает NetworkManager на использование заданных
    DNS-серверов, отключает systemd-resolved и создаёт
    корректный resolv.conf.
    """

    name = "Сеть и DNS"
    weight = 1
    skippable = True

    def run(self) -> None:
        """Настроить DNS и сетевые параметры.

        Raises:
            StageError: При ошибке конфигурации сети.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        # Создание конфигурации DNS для NetworkManager
        self._create_nm_dns_config()

        # Отключение и маскирование systemd-resolved
        self._disable_resolved()

        # Настройка resolv.conf
        self._setup_resolv_conf()

        self.ui.log_success("Сеть и DNS настроены")

    def _create_nm_dns_config(self) -> None:
        """Создание drop-in конфигурации DNS для NetworkManager."""
        # Разделяем IPv4 и IPv6 DNS-серверы
        ipv4_servers = [s for s in DNS_SERVERS if ":" not in s]
        ipv6_servers = [s for s in DNS_SERVERS if ":" in s]

        dns_conf = (
            "# Пользовательские DNS-серверы\n"
            "[global-dns-domain-*]\n"
            f"servers={';'.join(ipv4_servers + ipv6_servers)};\n"
        )

        conf_dir = "/etc/NetworkManager/conf.d"
        self.ui.log_command(f"Запись {conf_dir}/dns.conf")
        write_file_in_chroot(f"{conf_dir}/dns.conf", dns_conf)
        self.ui.log_success("Конфигурация DNS для NetworkManager создана")

    def _disable_resolved(self) -> None:
        """Отключение и маскирование systemd-resolved."""
        self.ui.log_command("systemctl disable systemd-resolved")
        chroot_run(
            ["systemctl", "disable", "systemd-resolved"],
            check=False,  # Может быть уже отключён
        )

        self.ui.log_command("systemctl mask systemd-resolved")
        chroot_run(["systemctl", "mask", "systemd-resolved"])
        self.ui.log_success("systemd-resolved отключён и замаскирован")

    def _setup_resolv_conf(self) -> None:
        """Настройка /etc/resolv.conf с пользовательскими DNS."""
        # Удаляем существующий симлинк или файл resolv.conf
        resolv_path = MOUNT_POINT / "etc" / "resolv.conf"
        self.ui.log_command("Настройка /etc/resolv.conf")

        # Удаляем симлинк на systemd-resolved (если есть)
        if resolv_path.is_symlink():
            resolv_path.unlink()

        # Формируем содержимое resolv.conf
        lines = ["# DNS-серверы (настроено установщиком)\n"]
        for server in DNS_SERVERS:
            lines.append(f"nameserver {server}\n")

        resolv_path.write_text("".join(lines), encoding="utf-8")
        self.ui.log_success("resolv.conf настроен")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация настройки сети."""
        self.ui.log_command("Запись /etc/NetworkManager/conf.d/dns.conf")
        time.sleep(0.3)
        self.ui.log_success("Конфигурация DNS для NetworkManager создана")

        self.ui.log_command("systemctl disable systemd-resolved")
        time.sleep(0.2)
        self.ui.log_command("systemctl mask systemd-resolved")
        time.sleep(0.2)
        self.ui.log_success("systemd-resolved отключён и замаскирован")

        self.ui.log_command("Настройка /etc/resolv.conf")
        time.sleep(0.3)
        dns_list = ", ".join(DNS_SERVERS[:2])
        self.ui.log_success(f"resolv.conf настроен ({dns_list}, ...)")

        self.ui.log_success("Сеть и DNS настроены")
