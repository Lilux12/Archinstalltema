"""Разметка и форматирование диска.

Создаёт таблицу разделов (GPT для UEFI, MBR для BIOS),
форматирует разделы и монтирует их в /mnt.
"""

from __future__ import annotations

import time
from pathlib import Path

from ..constants import MOUNT_POINT
from ..exceptions import StageError
from ..utils.shell import run
from .base_stage import BaseStage


class DiskStage(BaseStage):
    """Этап разметки и форматирования диска.

    UEFI: GPT с EFI-разделом (1 GiB) и корневым разделом (ext4).
    BIOS: MBR с единственным загрузочным разделом (ext4).
    """

    name = "Разметка диска"
    weight = 2
    skippable = False

    def run(self) -> None:
        """Выполнить разметку, форматирование и монтирование диска.

        Raises:
            StageError: При ошибке разметки или монтирования.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        disk = self.config.disk  # например, /dev/sda

        if self.config.is_uefi:
            self._partition_uefi(disk)
        else:
            self._partition_bios(disk)

        # Проверяем результат через lsblk
        self.ui.log_command(f"lsblk {disk}")
        run(["lsblk", "-f", disk])
        self.ui.log_success("Разметка диска завершена")

    def _partition_uefi(self, disk: str) -> None:
        """Разметка диска для режима UEFI (GPT).

        Создаёт два раздела:
        - Раздел 1: EFI System Partition (1 GiB, FAT32)
        - Раздел 2: Корневой раздел (оставшееся место, ext4)

        Args:
            disk: Путь к блочному устройству (/dev/sdX).
        """
        # Определяем имена разделов (nvme vs sd)
        part1, part2 = self._partition_names(disk, 1), self._partition_names(disk, 2)

        # Очистка таблицы разделов
        self.ui.log_command(f"sgdisk --zap-all {disk}")
        run(["sgdisk", "--zap-all", disk])

        # Создание EFI-раздела (1 GiB, тип ef00)
        self.ui.log_command(f"sgdisk -n 1:0:+1GiB -t 1:ef00 {disk}")
        run(["sgdisk", "-n", "1:0:+1GiB", "-t", "1:ef00", disk])

        # Создание корневого раздела (всё оставшееся место, тип 8300)
        self.ui.log_command(f"sgdisk -n 2:0:0 -t 2:8300 {disk}")
        run(["sgdisk", "-n", "2:0:0", "-t", "2:8300", disk])

        # Форматирование EFI-раздела в FAT32
        self.ui.log_command(f"mkfs.fat -F32 -n EFI {part1}")
        run(["mkfs.fat", "-F32", "-n", "EFI", part1])

        # Форматирование корневого раздела в ext4
        self.ui.log_command(f"mkfs.ext4 -L root {part2}")
        run(["mkfs.ext4", "-F", "-L", "root", part2])

        # Монтирование корневого раздела
        self.ui.log_command(f"mount {part2} {MOUNT_POINT}")
        run(["mount", part2, str(MOUNT_POINT)])

        # Монтирование EFI-раздела в /mnt/boot
        boot_dir = MOUNT_POINT / "boot"
        self.ui.log_command(f"mount --mkdir {part1} {boot_dir}")
        run(["mount", "--mkdir", part1, str(boot_dir)])

    def _partition_bios(self, disk: str) -> None:
        """Разметка диска для режима BIOS (MBR).

        Создаёт один загрузочный раздел на весь диск (ext4).

        Args:
            disk: Путь к блочному устройству (/dev/sdX).
        """
        part1 = self._partition_names(disk, 1)

        # Создание MBR-таблицы разделов
        self.ui.log_command(f"parted -s {disk} mklabel msdos")
        run(["parted", "-s", disk, "mklabel", "msdos"])

        # Создание единственного раздела на весь диск
        self.ui.log_command(f"parted -s {disk} mkpart primary ext4 1MiB 100%")
        run(["parted", "-s", disk, "mkpart", "primary", "ext4", "1MiB", "100%"])

        # Установка флага boot
        self.ui.log_command(f"parted -s {disk} set 1 boot on")
        run(["parted", "-s", disk, "set", "1", "boot", "on"])

        # Форматирование в ext4
        self.ui.log_command(f"mkfs.ext4 -L root {part1}")
        run(["mkfs.ext4", "-F", "-L", "root", part1])

        # Монтирование
        self.ui.log_command(f"mount {part1} {MOUNT_POINT}")
        run(["mount", part1, str(MOUNT_POINT)])

    @staticmethod
    def _partition_names(disk: str, num: int) -> str:
        """Получить имя раздела по номеру.

        Для NVMe-дисков добавляется 'p' перед номером раздела
        (например, /dev/nvme0n1p1), для остальных — просто номер
        (например, /dev/sda1).

        Args:
            disk: Путь к блочному устройству.
            num: Номер раздела.

        Returns:
            Путь к разделу.
        """
        # NVMe-диски используют формат /dev/nvme0n1p1
        if "nvme" in disk or "mmcblk" in disk:
            return f"{disk}p{num}"
        return f"{disk}{num}"

    def rollback(self) -> None:
        """Откат: размонтирование /mnt."""
        try:
            run(["umount", "-R", str(MOUNT_POINT)], check=False)
        except Exception:
            pass

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация разметки диска."""
        disk = self.config.disk or "/dev/sda"

        if self.config.is_uefi:
            self.ui.log_command(f"sgdisk --zap-all {disk}")
            time.sleep(0.3)
            self.ui.log_success("Таблица разделов очищена")

            self.ui.log_command(f"sgdisk -n 1:0:+1GiB -t 1:ef00 {disk}")
            time.sleep(0.2)
            self.ui.log_success("EFI-раздел создан (1 GiB)")

            self.ui.log_command(f"sgdisk -n 2:0:0 -t 2:8300 {disk}")
            time.sleep(0.2)
            self.ui.log_success("Корневой раздел создан")

            self.ui.log_command(f"mkfs.fat -F32 -n EFI {disk}1")
            time.sleep(0.4)
            self.ui.log_success("EFI-раздел отформатирован (FAT32)")

            self.ui.log_command(f"mkfs.ext4 -L root {disk}2")
            time.sleep(0.5)
            self.ui.log_success("Корневой раздел отформатирован (ext4)")

            self.ui.log_command(f"mount {disk}2 /mnt")
            time.sleep(0.2)
            self.ui.log_success("Корневой раздел смонтирован")

            self.ui.log_command(f"mount --mkdir {disk}1 /mnt/boot")
            time.sleep(0.2)
            self.ui.log_success("EFI-раздел смонтирован")
        else:
            self.ui.log_command(f"parted -s {disk} mklabel msdos")
            time.sleep(0.3)
            self.ui.log_success("MBR-таблица создана")

            self.ui.log_command(f"parted -s {disk} mkpart primary ext4 1MiB 100%")
            time.sleep(0.2)
            self.ui.log_success("Раздел создан")

            self.ui.log_command(f"mkfs.ext4 -L root {disk}1")
            time.sleep(0.5)
            self.ui.log_success("Раздел отформатирован (ext4)")

            self.ui.log_command(f"mount {disk}1 /mnt")
            time.sleep(0.2)
            self.ui.log_success("Раздел смонтирован")

        self.ui.log_command(f"lsblk {disk}")
        time.sleep(0.3)
        self.ui.log_success("Разметка диска завершена")
