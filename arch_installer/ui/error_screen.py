"""Экран ошибки установки Arch Linux.

Отображает информацию об ошибке, произошедшей на конкретном этапе
установки, и предлагает пользователю варианты действий: повторить
этап, пропустить его или прервать установку.

╔═══════════════════════════════════════════╗
║  ✗ ОШИБКА НА ЭТАПЕ: ...                   ║
║                                            ║
║  Описание ошибки...                        ║
║                                            ║
║  Последние 10 строк лога:                  ║
║  > строка 1                                ║
║  > строка 2                                ║
║  ...                                       ║
║                                            ║
║  [R] Повторить  [S] Пропустить  [A] Выйти ║
╚═══════════════════════════════════════════╝
"""

from __future__ import annotations

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..i18n import t
from .theme import (
    ARCH_BLUE,
    ERROR_RED,
    MUTED_GRAY,
    SUCCESS_GREEN,
    WARNING_AMBER,
    SYM_ARROW,
    SYM_CROSS,
)

# ═══════════════════════════════════════════════════════════════
#  Константы модуля
# ═══════════════════════════════════════════════════════════════

# Максимальное число строк лога, показываемых на экране ошибки
_MAX_VISIBLE_LOG_LINES: int = 10


# ═══════════════════════════════════════════════════════════════
#  Основная функция экрана ошибки
# ═══════════════════════════════════════════════════════════════


def show_error_screen(
    console: Console,
    stage_name: str,
    error_msg: str,
    log_lines: list[str] | None = None,
    skippable: bool = True,
) -> str:
    """Показать экран ошибки установки с вариантами действий.

    Отображает панель с красной рамкой, содержащую:
    - Название этапа, на котором произошла ошибка
    - Текст ошибки
    - Последние строки лога (если переданы)
    - Кнопки: Повторить [R], Пропустить [S] (если skippable), Выйти [A]

    Args:
        console: Rich-консоль для вывода.
        stage_name: Название этапа, на котором произошла ошибка.
        error_msg: Текст сообщения об ошибке.
        log_lines: Последние строки лога для отображения (до 10 шт.).
        skippable: Можно ли пропустить этот этап.

    Returns:
        Строка действия: «retry», «skip» или «abort».
    """
    console.print()

    # ─── Заголовок ошибки ───────────────────────────────────
    title_text = Text()
    title_text.append(f"  {SYM_CROSS} ", style=f"bold {ERROR_RED}")
    title_text.append(
        t("error.title", stage=stage_name),
        style=f"bold {ERROR_RED}",
    )

    # ─── Описание ошибки ───────────────────────────────────
    error_text = Text()
    error_text.append("\n")
    # Разбиваем длинное сообщение по строкам
    for line in error_msg.splitlines():
        error_text.append(f"  {line}\n", style=ERROR_RED)

    # ─── Строки лога ────────────────────────────────────────
    log_section = Text()
    if log_lines:
        # Берём не больше _MAX_VISIBLE_LOG_LINES
        visible_lines = log_lines[-_MAX_VISIBLE_LOG_LINES:]
        count = len(visible_lines)

        log_section.append("\n")
        log_section.append(
            f"  {t('error.last_lines', count=count)}\n",
            style=f"bold {MUTED_GRAY}",
        )
        log_section.append("\n")

        for line in visible_lines:
            # Каждая строка лога с отступом и маркером
            log_section.append(f"  {SYM_ARROW} ", style=MUTED_GRAY)
            log_section.append(f"{line}\n", style=MUTED_GRAY)

    # ─── Кнопки действий ───────────────────────────────────
    buttons = Text()
    buttons.append("\n")

    # [R] Повторить — всегда доступна
    buttons.append(f"  {t('error.retry')}", style=f"bold {SUCCESS_GREEN}")

    # [S] Пропустить — только если этап можно пропустить
    if skippable:
        buttons.append(f"    {t('error.skip')}", style=f"bold {WARNING_AMBER}")

    # [A] Выйти — всегда доступна
    buttons.append(f"    {t('error.abort')}", style=f"bold {ERROR_RED}")

    buttons.append("\n")

    # ─── Собираем содержимое панели ─────────────────────────
    content = Text.assemble(
        title_text,
        error_text,
        log_section,
        buttons,
    )

    # Панель с красной двойной рамкой
    panel = Panel(
        content,
        border_style=f"bold {ERROR_RED}",
        padding=(1, 2),
        title=f"[bold {ERROR_RED}]{SYM_CROSS} ERROR[/]",
        title_align="center",
    )

    console.print(Align.center(panel, width=70))
    console.print()

    # ─── Допустимые клавиши ─────────────────────────────────
    valid_keys = {"r": "retry", "a": "abort"}
    if skippable:
        valid_keys["s"] = "skip"

    # Формируем подсказку ввода
    keys_hint = "/".join(k.upper() for k in sorted(valid_keys.keys()))

    # ─── Ожидание выбора пользователя ───────────────────────
    while True:
        try:
            choice = console.input(
                f"  [{ARCH_BLUE}]Выберите действие ({keys_hint}): [/]"
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C на экране ошибки = выход
            return "abort"

        if choice in valid_keys:
            return valid_keys[choice]

        # Неверный ввод — подсказываем допустимые варианты
        options_str = ", ".join(
            f"{k.upper()} = {v}" for k, v in sorted(valid_keys.items())
        )
        console.print(f"  [{ERROR_RED}]Неверный выбор. Допустимо: {options_str}[/]")
