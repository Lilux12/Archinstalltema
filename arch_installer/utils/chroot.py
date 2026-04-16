"""Вспомогательные функции для работы в окружении arch-chroot.

Упрощает выполнение команд, запись файлов и включение
systemd-сервисов внутри смонтированной целевой системы в /mnt.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from . import shell

logger = logging.getLogger("arch_installer.chroot")

# Корневая точка монтирования целевой системы
CHROOT_ROOT = Path("/mnt")


def chroot_run(
    cmd: list[str] | str,
    **kwargs: object,
) -> subprocess.CompletedProcess[str]:
    """Выполнить команду внутри arch-chroot /mnt.

    Обёртка над shell.run() с автоматическим добавлением
    флага chroot=True.

    Args:
        cmd: Команда в виде списка аргументов или строки.
        **kwargs: Дополнительные аргументы, передаваемые в shell.run()
                  (check, env, input_data, capture и др.).

    Returns:
        subprocess.CompletedProcess с результатом выполнения.

    Raises:
        StageError: Если команда завершилась с ошибкой и check=True.
    """
    logger.debug("chroot_run: %s", cmd)
    return shell.run(cmd, chroot=True, **kwargs)  # type: ignore[arg-type]


def write_file_in_chroot(path: str, content: str) -> None:
    """Записать файл в целевую файловую систему /mnt.

    Создаёт родительские директории при необходимости и записывает
    содержимое в указанный путь относительно /mnt.

    Args:
        path: Абсолютный путь к файлу внутри chroot
              (например, /etc/hostname). Будет записан в /mnt/etc/hostname.
        content: Текстовое содержимое файла.

    Raises:
        ValueError: Если путь не является абсолютным.
    """
    # Убираем ведущий слеш для корректной конкатенации
    if not path.startswith("/"):
        msg = f"Путь должен быть абсолютным, получен: {path}"
        raise ValueError(msg)

    # Убираем ведущий "/" чтобы Path / работал корректно
    relative = path.lstrip("/")
    target = CHROOT_ROOT / relative

    logger.info("Запись файла: %s", target)

    # Создаём родительские директории
    target.parent.mkdir(parents=True, exist_ok=True)

    # Записываем содержимое
    target.write_text(content, encoding="utf-8")

    logger.debug("Файл записан: %s (%d байт)", target, len(content.encode("utf-8")))


def enable_service(service: str) -> None:
    """Включить systemd-сервис в целевой системе.

    Выполняет `systemctl enable <service>` внутри arch-chroot.

    Args:
        service: Имя сервиса systemd (например, NetworkManager.service).

    Raises:
        StageError: Если команда systemctl завершилась с ошибкой.
    """
    logger.info("Включение сервиса: %s", service)
    chroot_run(["systemctl", "enable", service])
