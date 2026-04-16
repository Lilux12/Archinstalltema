"""Финальный экран успешной установки Arch Linux.

Отображает итоговую информацию после завершения установки:
время, количество пакетов, размер системы. Предоставляет
пользователю выбор: перезагрузка или выход в shell.

┌──────────────────────────────────────────────────┐
│  ✓ Установка завершена успешно                    │
│                                                   │
│  Время установки:       23:47                     │
│  Установлено пакетов:   1247                      │
│  Размер системы:        8.3 GiB                   │
│                                                   │
│  [ Перезагрузить сейчас ]  [ Выйти в shell ]      │
└──────────────────────────────────────────────────┘
"""

from __future__ import annotations

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..i18n import t
from .theme import (
    ARCH_BLUE,
    ERROR_RED,
    MUTED_GRAY,
    SUCCESS_GREEN,
    SYM_CHECK,
    SYM_DIAMOND,
)

# ═══════════════════════════════════════════════════════════════
#  Вспомогательные функции
# ═══════════════════════════════════════════════════════════════


def _format_duration(seconds: float) -> str:
    """Отформатировать длительность в MM:SS или HH:MM:SS.

    Args:
        seconds: Количество секунд.

    Returns:
        Строка вида «23:47» или «1:04:32».
    """
    total = int(seconds)
    if total < 0:
        total = 0

    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# ═══════════════════════════════════════════════════════════════
#  Основная функция финального экрана
# ═══════════════════════════════════════════════════════════════


def show_final_screen(
    console: Console,
    elapsed_seconds: float,
    package_count: int,
    system_size: str,
) -> str:
    """Показать финальный экран успешной установки.

    Отображает панель с зелёной рамкой, итоговой статистикой
    и двумя кнопками выбора: перезагрузка или shell.

    Args:
        console: Rich-консоль для вывода.
        elapsed_seconds: Общее время установки в секундах.
        package_count: Количество установленных пакетов.
        system_size: Размер системы (например, «8.3 GiB»).

    Returns:
        Строка «reboot» или «shell» — выбор пользователя.
    """
    console.clear()

    # Заголовок успеха
    title_line = Text()
    title_line.append(f"  {SYM_CHECK} ", style=f"bold {SUCCESS_GREEN}")
    title_line.append(t("final.success"), style=f"bold {SUCCESS_GREEN}")

    # Форматируем время
    time_str = _format_duration(elapsed_seconds)

    # Таблица статистики
    stats_table = Table(
        show_header=False,
        show_edge=False,
        show_lines=False,
        pad_edge=False,
        padding=(0, 2),
        expand=False,
    )
    stats_table.add_column("Параметр", style=f"bold {ARCH_BLUE}", min_width=24)
    stats_table.add_column("Значение", min_width=16)

    stats_table.add_row(
        t("final.time", time="").rstrip(":").rstrip(),
        time_str,
    )
    stats_table.add_row(
        t("final.packages", count="").rstrip(":").rstrip(),
        str(package_count),
    )
    stats_table.add_row(
        t("final.size", size="").rstrip(":").rstrip(),
        system_size,
    )

    # Кнопки выбора
    buttons_line = Text()
    buttons_line.append("  [ 1 ] ", style=f"bold {SUCCESS_GREEN}")
    buttons_line.append(t("final.reboot"), style=SUCCESS_GREEN)
    buttons_line.append("    ", style=MUTED_GRAY)
    buttons_line.append("[ 2 ] ", style=f"bold {ARCH_BLUE}")
    buttons_line.append(t("final.shell"), style=ARCH_BLUE)

    # Сообщение о готовности
    ready_line = Text()
    ready_line.append(f"\n  {SYM_DIAMOND} ", style=MUTED_GRAY)
    ready_line.append(t("final.ready"), style=MUTED_GRAY)

    # Собираем содержимое панели
    content = Text()
    content.append_text(title_line)
    content.append("\n\n")

    # Главная панель с зелёной рамкой
    panel = Panel(
        Align.left(
            Text.assemble(
                title_line,
                "\n\n",
                stats_table,
                "\n\n",
                ready_line,
                "\n\n",
                buttons_line,
                "\n",
            )
        ),
        border_style=f"bold {SUCCESS_GREEN}",
        padding=(1, 3),
        title=f"[bold {SUCCESS_GREEN}]{SYM_CHECK} ARCH INSTALLER[/]",
        title_align="center",
    )

    console.print()
    console.print(Align.center(panel, width=60))
    console.print()

    # Ожидание выбора пользователя
    while True:
        try:
            choice = console.input(
                f"  [{ARCH_BLUE}]Выберите действие (1/2): [/]"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C на финальном экране — просто выходим в shell
            return "shell"

        if choice == "1":
            return "reboot"
        if choice == "2":
            return "shell"

        console.print(f"  [{ERROR_RED}]Введите 1 или 2[/]")
