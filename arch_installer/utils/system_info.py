"""Модуль сбора информации о системе.

Собирает данные об оборудовании и окружении перед началом
установки: режим загрузки (UEFI/BIOS), объём ОЗУ, наличие
интернета, модель процессора, видеокарта и прочее.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("arch_installer.system_info")


@dataclass
class SystemInfo:
    """Результат сбора информации о системе.

    Attributes:
        is_root: Запущен ли установщик от имени root.
        is_live_iso: Запущен ли установщик из live-ISO окружения.
        has_internet: Есть ли доступ к интернету.
        ram_gib: Объём оперативной памяти в гибибайтах (GiB).
        free_space_mib: Свободное место в корневой ФС live-ISO (MiB).
        is_uefi: Загружена ли система в режиме UEFI.
        cpu_model: Название модели процессора.
        gpu_model: Название модели видеокарты (или «Не определено»).
    """

    is_root: bool = False
    is_live_iso: bool = False
    has_internet: bool = False
    ram_gib: float = 0.0
    free_space_mib: int = 0
    is_uefi: bool = False
    cpu_model: str = "Не определено"
    gpu_model: str = "Не определено"


def _check_root() -> bool:
    """Проверить, запущен ли процесс от имени root.

    Returns:
        True, если текущий UID равен 0.
    """
    is_root = os.getuid() == 0
    logger.debug("Проверка root: uid=%d, is_root=%s", os.getuid(), is_root)
    return is_root


def _check_live_iso() -> bool:
    """Проверить, запущен ли установщик из live-ISO окружения.

    Признак live-ISO: наличие каталога /run/archiso или
    файла /etc/arch-release в сочетании с корневой ФС типа tmpfs/overlay.

    Returns:
        True, если обнаружено live-ISO окружение.
    """
    archiso_dir = Path("/run/archiso")
    if archiso_dir.is_dir():
        logger.debug("Обнаружен /run/archiso — live-ISO окружение")
        return True

    # Дополнительная проверка: корень на tmpfs/overlay
    try:
        result = subprocess.run(
            ["findmnt", "-n", "-o", "FSTYPE", "/"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        fstype = result.stdout.strip().lower()
        if fstype in ("tmpfs", "overlay", "airootfs"):
            logger.debug("Корневая ФС типа %s — live-ISO окружение", fstype)
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.debug("Не удалось определить тип корневой ФС: %s", exc)

    logger.debug("Live-ISO окружение не обнаружено")
    return False


def _check_internet() -> bool:
    """Проверить наличие интернет-соединения.

    Выполняет ping к нескольким надёжным серверам для
    минимизации ложноотрицательных результатов.

    Returns:
        True, если хотя бы один хост отвечает на ping.
    """
    hosts = ["archlinux.org", "1.1.1.1", "8.8.8.8"]

    for host in hosts:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", host],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.debug("Интернет доступен (ответ от %s)", host)
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            logger.debug("Ping %s не удался: %s", host, exc)
            continue

    logger.debug("Интернет недоступен — ни один хост не ответил")
    return False


def _check_ram() -> float:
    """Определить объём оперативной памяти в GiB.

    Читает общий объём ОЗУ из /proc/meminfo.

    Returns:
        Объём ОЗУ в гибибайтах, округлённый до одного знака.
    """
    meminfo_path = Path("/proc/meminfo")

    try:
        content = meminfo_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("MemTotal:"):
                # Формат: "MemTotal:       16384000 kB"
                parts = line.split()
                kb = int(parts[1])
                gib = round(kb / (1024 * 1024), 1)
                logger.debug("ОЗУ: %s KiB = %.1f GiB", kb, gib)
                return gib
    except (OSError, ValueError, IndexError) as exc:
        logger.warning("Не удалось определить объём ОЗУ: %s", exc)

    return 0.0


def _check_free_space() -> int:
    """Определить свободное место в корневой файловой системе (MiB).

    Используется для проверки, достаточно ли места в tmpfs
    live-ISO для работы установщика.

    Returns:
        Свободное место в мебибайтах.
    """
    try:
        result = subprocess.run(
            ["df", "--output=avail", "-BM", "/"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Вывод: заголовок + значение, например "  1234M"
        lines = result.stdout.strip().splitlines()
        if len(lines) >= 2:
            avail_str = lines[1].strip().rstrip("M")
            mib = int(avail_str)
            logger.debug("Свободное место в /: %d MiB", mib)
            return mib
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError,
            ValueError, IndexError) as exc:
        logger.warning("Не удалось определить свободное место: %s", exc)

    return 0


def _check_uefi() -> bool:
    """Проверить, загружена ли система в режиме UEFI.

    Признак UEFI: существование каталога /sys/firmware/efi.

    Returns:
        True, если система загружена в режиме UEFI.
    """
    efi_dir = Path("/sys/firmware/efi")
    is_uefi = efi_dir.is_dir()
    logger.debug("Режим загрузки: %s", "UEFI" if is_uefi else "BIOS/Legacy")
    return is_uefi


def _detect_cpu() -> str:
    """Определить модель процессора.

    Читает информацию из /proc/cpuinfo.

    Returns:
        Название модели CPU или «Не определено».
    """
    cpuinfo_path = Path("/proc/cpuinfo")

    try:
        content = cpuinfo_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("model name"):
                # Формат: "model name\t: Intel(R) Core(TM) i7-..."
                _, _, model = line.partition(":")
                cpu_model = model.strip()
                logger.debug("Процессор: %s", cpu_model)
                return cpu_model
    except (OSError, ValueError) as exc:
        logger.warning("Не удалось определить модель CPU: %s", exc)

    return "Не определено"


def _detect_gpu() -> str:
    """Определить модель видеокарты.

    Использует lspci для поиска VGA-совместимых контроллеров
    и 3D-ускорителей.

    Returns:
        Название модели GPU или «Не определено».
    """
    try:
        result = subprocess.run(
            ["lspci", "-nn"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            logger.debug("lspci завершился с кодом %d", result.returncode)
            return "Не определено"

        # Ищем строки с VGA или 3D controller
        for line in result.stdout.splitlines():
            lower = line.lower()
            if "vga compatible controller" in lower or "3d controller" in lower:
                # Формат: "01:00.0 VGA compatible controller [0300]: NVIDIA ... [10de:1c82]"
                _, _, description = line.partition(": ")
                if description:
                    # Убираем PCI ID в квадратных скобках в конце
                    gpu_model = description.rsplit(" [", 1)[0].strip()
                    logger.debug("Видеокарта: %s", gpu_model)
                    return gpu_model
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning("Не удалось определить модель GPU: %s", exc)

    return "Не определено"


def gather_system_info() -> SystemInfo:
    """Собрать полную информацию о системе.

    Выполняет все проверки оборудования и окружения,
    заполняет и возвращает датакласс SystemInfo.

    Returns:
        Заполненный экземпляр SystemInfo со всеми данными о системе.
    """
    logger.info("Сбор информации о системе...")

    info = SystemInfo(
        is_root=_check_root(),
        is_live_iso=_check_live_iso(),
        has_internet=_check_internet(),
        ram_gib=_check_ram(),
        free_space_mib=_check_free_space(),
        is_uefi=_check_uefi(),
        cpu_model=_detect_cpu(),
        gpu_model=_detect_gpu(),
    )

    logger.info(
        "Система: root=%s, live=%s, inet=%s, RAM=%.1f GiB, "
        "free=%d MiB, UEFI=%s, CPU=%s, GPU=%s",
        info.is_root,
        info.is_live_iso,
        info.has_internet,
        info.ram_gib,
        info.free_space_mib,
        info.is_uefi,
        info.cpu_model,
        info.gpu_model,
    )

    return info
