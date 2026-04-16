"""Интерактивный мастер настройки установки Arch Linux.

Пошаговый визард, собирающий все необходимые параметры от пользователя:
язык интерфейса, целевой диск, имя пользователя, пароли, имя хоста,
часовой пояс. Результатом работы является заполненный InstallConfig.

Каждый шаг отображает заголовок «Шаг N из M • Название» и индикатор
прогресса из заполненных/пустых кружков (●●●○○○○○○).
"""

from __future__ import annotations

import getpass
import json
import subprocess
from typing import Any

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import InstallConfig
from ..constants import MIN_DISK_SIZE_GIB
from ..exceptions import UserAbort
from ..i18n import set_lang, t
from ..utils.validators import (
    validate_hostname,
    validate_password,
    validate_timezone,
    validate_username,
)
from .theme import (
    ARCH_BLUE,
    ERROR_RED,
    MUTED_GRAY,
    SUCCESS_GREEN,
    WARNING_AMBER,
    SYM_ARROW,
    SYM_CHECK,
    SYM_CIRCLE,
    SYM_CIRCLE_EMPTY,
    SYM_CROSS,
    SYM_WARN,
)

# ═══════════════════════════════════════════════════════════════
#  Константы визарда
# ═══════════════════════════════════════════════════════════════

# Общее количество шагов в визарде
_TOTAL_STEPS: int = 9

# Поддерживаемые языки
_LANGUAGES: list[tuple[str, str]] = [
    ("ru", "Русский"),
    ("en", "English"),
]

# Фейковые диски для демо-режима
_DEMO_DISKS: list[dict[str, Any]] = [
    {
        "name": "sda",
        "size": "500G",
        "size_bytes": 500_000_000_000,
        "model": "Samsung SSD 870 EVO",
        "type": "disk",
        "tran": "sata",
    },
    {
        "name": "nvme0n1",
        "size": "1T",
        "size_bytes": 1_000_000_000_000,
        "model": "WD Black SN850X",
        "type": "disk",
        "tran": "nvme",
    },
    {
        "name": "sdb",
        "size": "16G",
        "size_bytes": 16_000_000_000,
        "model": "USB Flash Drive",
        "type": "disk",
        "tran": "usb",
    },
]


# ═══════════════════════════════════════════════════════════════
#  Вспомогательные функции отрисовки
# ═══════════════════════════════════════════════════════════════


def _render_step_header(console: Console, step: int, title: str) -> None:
    """Отрисовать заголовок текущего шага с индикатором прогресса.

    Формат: «Шаг N из M • Название»
    Прогресс: ●●●○○○○○○
    """
    # Индикатор прогресса из кружков
    dots = (
        f"[{SUCCESS_GREEN}]{SYM_CIRCLE}[/]" * step
        + f"[{MUTED_GRAY}]{SYM_CIRCLE_EMPTY}[/]" * (_TOTAL_STEPS - step)
    )

    header_text = t("wizard.step", current=step, total=_TOTAL_STEPS)
    header_line = f"[bold {ARCH_BLUE}]{header_text} {SYM_ARROW} {title}[/]"

    console.print()
    console.print(Align.center(header_line))
    console.print(Align.center(dots))
    console.print()


def _prompt(console: Console, prompt_text: str, default: str = "") -> str:
    """Запросить ввод у пользователя с обработкой Ctrl+C.

    Args:
        console: Rich-консоль для вывода.
        prompt_text: Текст подсказки.
        default: Значение по умолчанию (показывается в скобках).

    Returns:
        Введённое значение или значение по умолчанию.

    Raises:
        UserAbort: При нажатии Ctrl+C.
    """
    suffix = f" [{default}]" if default else ""
    try:
        value = console.input(f"  {SYM_ARROW} {prompt_text}{suffix}: ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print()
        raise UserAbort("Установка прервана пользователем")
    return value if value else default


def _prompt_password(console: Console, prompt_text: str) -> str:
    """Запросить пароль (скрытый ввод) с обработкой Ctrl+C.

    Args:
        console: Rich-консоль для вывода.
        prompt_text: Текст подсказки.

    Returns:
        Введённый пароль.

    Raises:
        UserAbort: При нажатии Ctrl+C.
    """
    try:
        value = getpass.getpass(f"  {SYM_ARROW} {prompt_text}: ")
    except (KeyboardInterrupt, EOFError):
        console.print()
        raise UserAbort("Установка прервана пользователем")
    return value


def _show_error(console: Console, message: str) -> None:
    """Показать сообщение об ошибке валидации."""
    console.print(f"  [{ERROR_RED}]{SYM_CROSS} {message}[/]")
    console.print()


def _show_warning(console: Console, message: str) -> None:
    """Показать предупреждение."""
    console.print(f"  [{WARNING_AMBER}]{SYM_WARN} {message}[/]")


def _show_success(console: Console, message: str) -> None:
    """Показать сообщение об успешном действии."""
    console.print(f"  [{SUCCESS_GREEN}]{SYM_CHECK} {message}[/]")


# ═══════════════════════════════════════════════════════════════
#  Получение списка дисков
# ═══════════════════════════════════════════════════════════════


def _get_disks(demo_mode: bool) -> list[dict[str, Any]]:
    """Получить список доступных дисков для установки.

    В демо-режиме возвращает фейковые диски. В рабочем режиме
    вызывает lsblk --json для получения реальных устройств.

    Фильтрация:
    - Исключаются loop-устройства и cd-rom
    - Исключаются диски размером менее MIN_DISK_SIZE_GIB

    Args:
        demo_mode: Включён ли демо-режим.

    Returns:
        Список словарей с информацией о дисках.
    """
    if demo_mode:
        return _DEMO_DISKS

    try:
        result = subprocess.run(
            [
                "lsblk",
                "--json",
                "--bytes",
                "--output", "NAME,SIZE,TYPE,MODEL,TRAN",
                "--nodeps",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    disks: list[dict[str, Any]] = []
    min_size_bytes = MIN_DISK_SIZE_GIB * (1024 ** 3)

    for device in data.get("blockdevices", []):
        dev_type = (device.get("type") or "").lower()

        # Исключаем loop-устройства и cd-rom
        if dev_type in ("loop", "rom"):
            continue

        # Только настоящие диски
        if dev_type != "disk":
            continue

        size_bytes = device.get("size", 0)
        if isinstance(size_bytes, str):
            try:
                size_bytes = int(size_bytes)
            except ValueError:
                continue

        # Фильтруем диски меньше минимального размера
        if size_bytes < min_size_bytes:
            continue

        # Форматируем размер в человекочитаемый вид
        size_gib = size_bytes / (1024 ** 3)
        if size_gib >= 1024:
            size_str = f"{size_gib / 1024:.1f} TiB"
        else:
            size_str = f"{size_gib:.1f} GiB"

        disks.append({
            "name": device.get("name", ""),
            "size": size_str,
            "size_bytes": size_bytes,
            "model": (device.get("model") or "Unknown").strip(),
            "type": dev_type,
            "tran": (device.get("tran") or "").lower(),
        })

    return disks


# ═══════════════════════════════════════════════════════════════
#  Шаги визарда
# ═══════════════════════════════════════════════════════════════


def _step_language(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 1: Выбор языка интерфейса."""
    _render_step_header(console, 1, t("wizard.language"))

    for idx, (code, name) in enumerate(_LANGUAGES, start=1):
        # Текущий язык отмечен заполненным кружком
        marker = (
            f"[{SUCCESS_GREEN}]{SYM_CIRCLE}[/]"
            if code == config.lang
            else f"[{MUTED_GRAY}]{SYM_CIRCLE_EMPTY}[/]"
        )
        console.print(f"    {marker} {idx}. {name} ({code})")

    console.print()

    while True:
        choice = _prompt(console, "Выберите язык / Select language", "1")
        if choice in ("1", "2"):
            lang_code = _LANGUAGES[int(choice) - 1][0]
            config.lang = lang_code
            set_lang(lang_code)
            _show_success(console, f"{_LANGUAGES[int(choice) - 1][1]}")
            return config
        _show_error(console, "Введите 1 или 2 / Enter 1 or 2")


def _step_disk(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 2: Выбор диска для установки."""
    _render_step_header(console, 2, t("wizard.disk"))

    disks = _get_disks(config.demo_mode)

    if not disks:
        _show_error(console, "Не найдено подходящих дисков для установки")
        raise UserAbort("Нет доступных дисков")

    # Таблица с дисками
    table = Table(
        show_header=True,
        header_style=f"bold {ARCH_BLUE}",
        border_style=MUTED_GRAY,
        pad_edge=True,
        padding=(0, 1),
    )
    table.add_column("#", justify="center", width=3)
    table.add_column("Устройство", min_width=12)
    table.add_column("Размер", justify="right", min_width=10)
    table.add_column("Модель", min_width=20)
    table.add_column("Интерфейс", min_width=8)

    for idx, disk in enumerate(disks, start=1):
        table.add_row(
            str(idx),
            f"/dev/{disk['name']}",
            disk["size"],
            disk["model"],
            disk.get("tran", "—").upper() or "—",
        )

    console.print(Align.center(table))
    console.print()

    while True:
        choice = _prompt(console, t("wizard.disk"))
        if not choice:
            _show_error(console, "Необходимо выбрать диск")
            continue

        try:
            idx = int(choice)
        except ValueError:
            _show_error(console, "Введите номер диска")
            continue

        if 1 <= idx <= len(disks):
            selected = disks[idx - 1]
            config.disk = f"/dev/{selected['name']}"
            _show_success(
                console,
                f"/dev/{selected['name']} ({selected['model']}, {selected['size']})",
            )
            # Сохраняем информацию о диске для предупреждения
            config._disk_model = selected["model"]  # type: ignore[attr-defined]
            config._disk_size = selected["size"]  # type: ignore[attr-defined]
            return config

        _show_error(console, f"Введите число от 1 до {len(disks)}")


def _step_disk_warning(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 3: Предупреждение об уничтожении данных на диске."""
    _render_step_header(console, 3, f"{SYM_WARN} WARNING")

    # Извлекаем метаданные диска
    disk_model = getattr(config, "_disk_model", "Unknown")
    disk_size = getattr(config, "_disk_size", "Unknown")

    warning_text = t(
        "wizard.disk_warning",
        disk=config.disk,
        model=disk_model,
        size=disk_size,
    )

    warning_panel = Panel(
        Align.center(Text.from_markup(f"[bold {ERROR_RED}]{warning_text}[/]")),
        border_style=f"bold {ERROR_RED}",
        padding=(1, 2),
    )
    console.print(Align.center(warning_panel, width=70))
    console.print()

    while True:
        confirmation = _prompt(console, "")
        if confirmation == "YES":
            _show_success(console, "Подтверждено")
            return config
        if confirmation.upper() == "YES" and confirmation != "YES":
            # Пользователь ввёл yes/Yes — напоминаем про заглавные
            _show_warning(console, "Введите YES заглавными буквами")
        else:
            _show_error(console, "Для подтверждения введите YES")


def _step_username(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 4: Ввод имени пользователя."""
    _render_step_header(console, 4, t("wizard.username"))

    while True:
        username = _prompt(console, t("wizard.username"))
        if not username:
            _show_error(console, "Имя пользователя не может быть пустым")
            continue

        ok, msg = validate_username(username)
        if ok:
            config.username = username
            _show_success(console, f"Пользователь: {username}")
            return config

        _show_error(console, msg)


def _step_user_password(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 5: Ввод пароля пользователя (скрытый ввод с подтверждением)."""
    _render_step_header(console, 5, t("wizard.password"))

    while True:
        password = _prompt_password(console, t("wizard.password"))
        if not password:
            _show_error(console, "Пароль не может быть пустым")
            continue

        ok, msg = validate_password(password)
        if not ok:
            _show_error(console, msg)
            continue

        # Подтверждение пароля
        confirm = _prompt_password(console, "Повторите пароль")
        if password != confirm:
            _show_error(console, "Пароли не совпадают")
            continue

        config.user_password = password
        _show_success(console, "Пароль пользователя установлен")
        return config


def _step_root_password(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 6: Ввод пароля root (скрытый ввод с подтверждением)."""
    _render_step_header(console, 6, t("wizard.root_password"))

    while True:
        password = _prompt_password(console, t("wizard.root_password"))
        if not password:
            _show_error(console, "Пароль root не может быть пустым")
            continue

        ok, msg = validate_password(password)
        if not ok:
            _show_error(console, msg)
            continue

        # Подтверждение пароля
        confirm = _prompt_password(console, "Повторите пароль root")
        if password != confirm:
            _show_error(console, "Пароли не совпадают")
            continue

        # Предупреждение, если пароль root совпадает с паролем пользователя
        if password == config.user_password:
            _show_warning(
                console,
                "Пароль root совпадает с паролем пользователя. "
                "Рекомендуется использовать разные пароли.",
            )
            console.print()
            use_same = _prompt(console, "Оставить одинаковые пароли? (y/n)", "y")
            if use_same.lower() != "y":
                continue

        config.root_password = password
        _show_success(console, "Пароль root установлен")
        return config


def _step_hostname(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 7: Ввод имени хоста."""
    _render_step_header(console, 7, t("wizard.hostname"))

    while True:
        hostname = _prompt(console, t("wizard.hostname"), config.hostname)
        if not hostname:
            _show_error(console, "Имя хоста не может быть пустым")
            continue

        ok, msg = validate_hostname(hostname)
        if ok:
            config.hostname = hostname
            _show_success(console, f"Хост: {hostname}")
            return config

        _show_error(console, msg)


def _step_timezone(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 8: Ввод часового пояса."""
    _render_step_header(console, 8, t("wizard.timezone"))

    # Подсказка о формате
    console.print(
        f"    [{MUTED_GRAY}]Формат: Region/City "
        f"(например, Europe/Moscow, US/Eastern)[/]"
    )
    console.print()

    while True:
        timezone = _prompt(console, t("wizard.timezone"), config.timezone)
        if not timezone:
            _show_error(console, "Часовой пояс не может быть пустым")
            continue

        # В демо-режиме пропускаем проверку файла zoneinfo
        if config.demo_mode:
            config.timezone = timezone
            _show_success(console, f"Часовой пояс: {timezone}")
            return config

        ok, msg = validate_timezone(timezone)
        if ok:
            config.timezone = timezone
            _show_success(console, f"Часовой пояс: {timezone}")
            return config

        _show_error(console, msg)


def _step_summary(console: Console, config: InstallConfig) -> InstallConfig:
    """Шаг 9: Итоговый экран с параметрами и подтверждение."""
    _render_step_header(console, 9, t("wizard.summary"))

    # Определяем режим загрузки
    boot_mode = "UEFI" if config.is_uefi else "BIOS (Legacy)"

    # Маскируем пароли
    user_pw_masked = "*" * len(config.user_password) if config.user_password else "—"
    root_pw_masked = "*" * len(config.root_password) if config.root_password else "—"

    # Таблица параметров
    table = Table(
        show_header=False,
        border_style=ARCH_BLUE,
        pad_edge=True,
        padding=(0, 2),
        title=f"[bold {ARCH_BLUE}]{t('wizard.summary')}[/]",
        title_justify="center",
        min_width=50,
    )
    table.add_column("Параметр", style=f"bold {ARCH_BLUE}", min_width=22)
    table.add_column("Значение", min_width=25)

    rows = [
        (t("wizard.language"), config.lang.upper()),
        (t("wizard.disk"), config.disk),
        (t("wizard.username"), config.username),
        (t("wizard.password"), user_pw_masked),
        (t("wizard.root_password"), root_pw_masked),
        (t("wizard.hostname"), config.hostname),
        (t("wizard.timezone"), config.timezone),
        ("Локаль", config.locale),
        ("Режим загрузки", boot_mode),
    ]

    if config.demo_mode:
        rows.append(("Демо-режим", f"[{WARNING_AMBER}]Да[/]"))

    for param, value in rows:
        table.add_row(param, value)

    console.print(Align.center(table))
    console.print()

    # Подтверждение
    while True:
        answer = _prompt(console, f"{t('wizard.confirm')} (y/n)", "y")
        if answer.lower() in ("y", "yes", "д", "да"):
            _show_success(console, "Параметры подтверждены. Начинаем установку...")
            return config
        if answer.lower() in ("n", "no", "н", "нет"):
            raise UserAbort(
                "Пользователь отменил установку на этапе подтверждения"
            )
        _show_error(console, "Введите y (да) или n (нет)")


# ═══════════════════════════════════════════════════════════════
#  Основная функция визарда
# ═══════════════════════════════════════════════════════════════


def run_wizard(console: Console, config: InstallConfig) -> InstallConfig:
    """Запустить интерактивный мастер настройки установки.

    Последовательно проводит пользователя через все шаги настройки,
    валидирует ввод и возвращает заполненный InstallConfig.

    Args:
        console: Rich-консоль для ввода/вывода.
        config: Начальная конфигурация (может содержать значения по умолчанию).

    Returns:
        Заполненный InstallConfig с подтверждёнными параметрами.

    Raises:
        UserAbort: Если пользователь прервал визард (Ctrl+C или отказ).
    """
    # Последовательность шагов визарда
    steps = [
        _step_language,
        _step_disk,
        _step_disk_warning,
        _step_username,
        _step_user_password,
        _step_root_password,
        _step_hostname,
        _step_timezone,
        _step_summary,
    ]

    try:
        for step_fn in steps:
            console.clear()
            config = step_fn(console, config)
    except KeyboardInterrupt:
        console.print()
        raise UserAbort("Установка прервана пользователем (Ctrl+C)")

    return config
