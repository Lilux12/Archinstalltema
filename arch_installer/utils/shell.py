"""Модуль запуска shell-команд.

Обеспечивает выполнение команд с потоковым выводом в UI,
логированием и обработкой ошибок. Поддерживает режим
arch-chroot для работы внутри смонтированной системы.
"""

from __future__ import annotations

import logging
import re
import shlex
import subprocess
from typing import TYPE_CHECKING, Any

from ..exceptions import StageError

if TYPE_CHECKING:
    pass

logger = logging.getLogger("arch_installer.shell")

# Глобальная ссылка на объект UI для потокового вывода
_ui: Any | None = None

# Регулярные выражения для разбора вывода pacman
_RE_PACMAN_INSTALLING = re.compile(r"installing (\S+) \((\S+)\)")
_RE_PACMAN_TOTAL = re.compile(r"Packages \((\d+)\)")
_RE_PACMAN_PROGRESS = re.compile(r"\((\d+)/(\d+)\)")


def set_ui(ui: Any | None) -> None:
    """Установить объект UI для потокового вывода команд.

    Args:
        ui: Объект прогресс-панели с методами log() и update_progress(),
            или None для отключения вывода в UI.
    """
    global _ui  # noqa: PLW0603
    _ui = ui


def _format_cmd(cmd: list[str] | str) -> str:
    """Преобразовать команду в строку для логирования.

    Args:
        cmd: Команда в виде списка аргументов или строки.

    Returns:
        Строковое представление команды.
    """
    if isinstance(cmd, list):
        return " ".join(shlex.quote(arg) for arg in cmd)
    return cmd


def _build_cmd(
    cmd: list[str] | str,
    *,
    chroot: bool = False,
) -> list[str] | str:
    """Собрать итоговую команду с учётом режима chroot.

    Args:
        cmd: Исходная команда.
        chroot: Если True, оборачивает команду в arch-chroot /mnt.

    Returns:
        Готовая к выполнению команда.
    """
    if not chroot:
        return cmd

    if isinstance(cmd, list):
        return ["arch-chroot", "/mnt", *cmd]

    # Для строковой команды — оборачиваем через sh -c
    return f"arch-chroot /mnt {cmd}"


def _parse_pacman_output(line: str) -> None:
    """Разобрать строку вывода pacman и обновить прогресс в UI.

    Распознаёт общее количество пакетов, текущий прогресс установки
    и имя устанавливаемого пакета.

    Args:
        line: Строка из stdout/stderr pacman.
    """
    if _ui is None:
        return

    # Общее количество пакетов — запоминаем для update_packages
    match_total = _RE_PACMAN_TOTAL.search(line)
    if match_total:
        total = int(match_total.group(1))
        if hasattr(_ui, "update_packages"):
            _ui.update_packages(0, total)

    # Прогресс (N/M)
    match_progress = _RE_PACMAN_PROGRESS.search(line)
    if match_progress:
        current = int(match_progress.group(1))
        total = int(match_progress.group(2))
        if hasattr(_ui, "update_packages"):
            _ui.update_packages(current, total)

    # Имя устанавливаемого пакета
    match_install = _RE_PACMAN_INSTALLING.search(line)
    if match_install:
        pkg_name = match_install.group(1)
        if hasattr(_ui, "update_operation"):
            _ui.update_operation(f"Установка {pkg_name}")


def _stream_process(
    cmd: list[str] | str,
    *,
    env: dict[str, str] | None = None,
    input_data: str | None = None,
    stream_to_ui: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Запустить процесс с потоковым чтением вывода.

    Читает stdout и stderr построчно, логирует каждую строку
    и пытается распарсить прогресс pacman.

    Args:
        cmd: Команда для выполнения.
        env: Дополнительные переменные окружения.
        input_data: Данные для передачи на stdin процесса.
        stream_to_ui: Если True, выводить строки в UI.

    Returns:
        CompletedProcess с собранным выводом.
    """
    use_shell = isinstance(cmd, str)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE if input_data else None,
        text=True,
        shell=use_shell,  # noqa: S603
        env=env,
        bufsize=1,
    )

    stdout_lines: list[str] = []

    # Если есть данные для stdin — отправляем и закрываем
    if input_data and proc.stdin:
        proc.stdin.write(input_data)
        proc.stdin.close()

    # Читаем вывод построчно
    if proc.stdout:
        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n")
            stdout_lines.append(line)

            # Логируем в файл на уровне DEBUG
            logger.debug("  | %s", line)

            if stream_to_ui:
                # Пытаемся распарсить вывод pacman
                _parse_pacman_output(line)

                # Отправляем строку в UI (экранируем Rich-разметку
                # из вывода команды, чтобы [текст] не вызывал MarkupError)
                if _ui is not None and hasattr(_ui, "log_info"):
                    _ui.log_info(line)

    returncode = proc.wait()

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=returncode,
        stdout="\n".join(stdout_lines),
        stderr="",
    )


def run(
    cmd: list[str] | str,
    *,
    chroot: bool = False,
    stream_to_ui: bool = True,
    check: bool = True,
    env: dict[str, str] | None = None,
    input_data: str | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Выполнить shell-команду с логированием и обработкой ошибок.

    Основная точка входа для запуска внешних процессов.
    Поддерживает потоковый вывод в UI, режим chroot и
    захват вывода для дальнейшей обработки.

    Args:
        cmd: Команда в виде списка аргументов или строки.
        chroot: Если True, выполняет через arch-chroot /mnt.
        stream_to_ui: Если True, строки stdout выводятся в UI.
        check: Если True, при ненулевом коде возврата бросает StageError.
        env: Дополнительные переменные окружения.
        input_data: Данные для передачи на stdin.
        capture: Если True, используется subprocess.run вместо Popen
                 (без потокового вывода, для захвата результата).

    Returns:
        subprocess.CompletedProcess с результатом выполнения.

    Raises:
        StageError: Если check=True и команда завершилась с ошибкой.
    """
    # Собираем итоговую команду
    final_cmd = _build_cmd(cmd, chroot=chroot)
    cmd_str = _format_cmd(final_cmd)

    # Логируем запуск команды
    logger.info("$ %s", cmd_str)

    if capture and not stream_to_ui:
        # Простой режим: захват вывода без потоковой передачи
        use_shell = isinstance(final_cmd, str)
        result = subprocess.run(
            final_cmd,
            capture_output=True,
            text=True,
            shell=use_shell,  # noqa: S603
            env=env,
            input=input_data,
        )
    else:
        # Потоковый режим: построчное чтение вывода
        result = _stream_process(
            final_cmd,
            env=env,
            input_data=input_data,
            stream_to_ui=stream_to_ui,
        )

    # Проверяем код возврата
    if check and result.returncode != 0:
        error_output = result.stderr or result.stdout or ""
        # Берём последние строки вывода для контекста ошибки
        tail = "\n".join(error_output.strip().splitlines()[-10:])
        raise StageError(
            cmd_str,
            f"Команда завершилась с ошибкой (код {result.returncode}):\n{tail}",
        )

    return result
