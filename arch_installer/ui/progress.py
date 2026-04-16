"""Панель прогресса установки Arch Linux с разделённым макетом.

Отображает два региона через rich.layout.Layout внутри rich.live.Live:

┌─ Журнал команд ─────────────────────────── 72% ─┐
│  ► Этап 4: Установка базовой системы              │
│  $ timedatectl set-ntp true                       │
│  ✓ NTP синхронизация включена                     │
│  ...последние 25 строк прокручиваются...          │
├─ Прогресс ──────────────────────────────── 28% ─┤
│  Общий прогресс:  Этап 4 из 14                    │
│  ████████████░░░░░░  28%                          │
│  Текущий этап:   Установка базовой системы        │
│  ⏱  Прошло: 04:32    ⏳ Осталось ≈ 11:40          │
└──────────────────────────────────────────────────┘

Класс ProgressUI управляет всем жизненным циклом отображения:
запуск, обновление этапов, логирование команд и результатов,
расчёт ETA, остановка.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Optional

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.text import Text

from ..constants import TOTAL_STAGES
from ..i18n import t
from .theme import (
    ARCH_BLUE,
    ERROR_RED,
    MUTED_GRAY,
    SUCCESS_GREEN,
    WARNING_AMBER,
    STYLE_COMMAND,
    STYLE_ERROR,
    STYLE_MUTED,
    STYLE_SUCCESS,
    STYLE_WARNING,
    SYM_ARROW,
    SYM_CHECK,
    SYM_CROSS,
    SYM_WARN,
)

# ═══════════════════════════════════════════════════════════════
#  Константы модуля
# ═══════════════════════════════════════════════════════════════

# Максимальное количество строк в буфере лога
_MAX_LOG_LINES: int = 25

# Частота обновления Live-дисплея (кадров в секунду)
_REFRESH_PER_SECOND: int = 4

# Символ заполненного блока прогресс-бара
_BAR_FILLED: str = "█"

# Символ пустого блока прогресс-бара
_BAR_EMPTY: str = "░"

# Ширина прогресс-бара в символах
_BAR_WIDTH: int = 40


# ═══════════════════════════════════════════════════════════════
#  Вспомогательные функции
# ═══════════════════════════════════════════════════════════════


def _format_duration(seconds: float) -> str:
    """Отформатировать длительность в MM:SS или HH:MM:SS.

    Args:
        seconds: Количество секунд.

    Returns:
        Строка вида «04:32» или «1:04:32».
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


def _build_progress_bar(percent: float, width: int = _BAR_WIDTH) -> Text:
    """Построить текстовый прогресс-бар с процентами.

    Args:
        percent: Процент завершения (0.0–100.0).
        width: Ширина бара в символах.

    Returns:
        Rich Text объект с раскрашенным прогресс-баром.
    """
    # Ограничиваем в допустимых пределах
    percent = max(0.0, min(100.0, percent))
    filled = int(width * percent / 100.0)
    empty = width - filled

    bar_text = Text()
    bar_text.append(_BAR_FILLED * filled, style=SUCCESS_GREEN)
    bar_text.append(_BAR_EMPTY * empty, style=MUTED_GRAY)
    bar_text.append(f"  {percent:.0f}%", style=f"bold {SUCCESS_GREEN}")
    return bar_text


# ═══════════════════════════════════════════════════════════════
#  Основной класс прогресса
# ═══════════════════════════════════════════════════════════════


class ProgressUI:
    """Управление отображением прогресса установки.

    Использует rich.live.Live для динамического обновления
    двухпанельного макета: журнал команд (сверху) и прогресс (снизу).

    Attributes:
        total_stages: Общее количество этапов установки.
    """

    def __init__(self, total_stages: int = TOTAL_STAGES) -> None:
        """Инициализация ProgressUI.

        Args:
            total_stages: Общее количество этапов установки.
        """
        # Общее число этапов
        self.total_stages: int = total_stages

        # Текущий номер этапа и его название
        self._current_stage: int = 0
        self._stage_name: str = ""

        # Текущая операция (отображается в панели прогресса)
        self._operation: str = ""

        # Счётчик пакетов (done/total)
        self._packages_done: int = 0
        self._packages_total: int = 0

        # Счётчик завершённых этапов и реальное кол-во этапов
        self._completed_stages: int = 0
        self._actual_total: int = 13  # этапы 2-14

        # Буфер строк лога (ограниченный deque)
        self._log_lines: deque[Text] = deque(maxlen=_MAX_LOG_LINES)

        # Таймеры для расчёта прошедшего времени и ETA
        self._start_time: float = 0.0
        self._stage_start_time: float = 0.0

        # Объект Rich Live для динамического отображения
        self._live: Optional[Live] = None

        # Rich Console (создаётся при start или передаётся извне)
        self._console: Optional[Console] = None

    # ─── Управление жизненным циклом ────────────────────────

    def start(self, console: Optional[Console] = None) -> None:
        """Запустить Live-дисплей прогресса.

        Args:
            console: Rich-консоль. Если None, создаётся новая.
        """
        self._console = console or Console()
        # Не сбрасываем таймер при повторном запуске (retry после ошибки)
        if self._start_time == 0.0:
            self._start_time = time.monotonic()
            self._stage_start_time = self._start_time

        self._live = Live(
            self._make_layout(),
            console=self._console,
            refresh_per_second=_REFRESH_PER_SECOND,
            transient=False,
        )
        self._live.start()

    def stop(self) -> None:
        """Остановить Live-дисплей прогресса."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    def get_elapsed(self) -> float:
        """Получить прошедшее время с начала установки.

        Returns:
            Прошедшее время в секундах.
        """
        if self._start_time == 0.0:
            return 0.0
        return time.monotonic() - self._start_time

    def log(self, msg: str) -> None:
        """Добавить произвольную строку в журнал (для shell streaming).

        Args:
            msg: Текст для добавления (может содержать Rich-разметку).
        """
        line = Text.from_markup(f"  {msg}")
        self._log_lines.append(line)
        self._refresh()

    # ─── Обновление состояния ───────────────────────────────

    def set_stage(self, num: int, name: str) -> None:
        """Установить текущий этап установки.

        Args:
            num: Номер этапа (начиная с 1).
            name: Название этапа.
        """
        self._current_stage = num
        self._stage_name = name
        self._stage_start_time = time.monotonic()
        self._operation = ""

        # Добавляем запись об этапе в лог
        line = Text()
        line.append(f"  {SYM_ARROW} ", style=f"bold {ARCH_BLUE}")
        line.append(
            t("progress.stage", current=num, total=self.total_stages),
            style=f"bold {ARCH_BLUE}",
        )
        line.append(f": {name}", style=f"bold {ARCH_BLUE}")
        self._log_lines.append(line)

        self._refresh()

    def log_command(self, cmd: str) -> None:
        """Добавить выполняемую команду в журнал.

        Args:
            cmd: Текст команды (например, «pacstrap /mnt base linux»).
        """
        line = Text()
        line.append("  $ ", style=STYLE_COMMAND)
        line.append(cmd, style=STYLE_COMMAND)
        self._log_lines.append(line)
        self._refresh()

    def log_success(self, msg: str) -> None:
        """Добавить сообщение об успехе в журнал.

        Args:
            msg: Текст сообщения.
        """
        line = Text()
        line.append(f"  {SYM_CHECK} ", style=STYLE_SUCCESS)
        line.append(msg, style=STYLE_SUCCESS)
        self._log_lines.append(line)
        self._refresh()

    def log_error(self, msg: str) -> None:
        """Добавить сообщение об ошибке в журнал.

        Args:
            msg: Текст ошибки.
        """
        line = Text()
        line.append(f"  {SYM_CROSS} ", style=STYLE_ERROR)
        line.append(msg, style=STYLE_ERROR)
        self._log_lines.append(line)
        self._refresh()

    def log_warning(self, msg: str) -> None:
        """Добавить предупреждение в журнал.

        Args:
            msg: Текст предупреждения.
        """
        line = Text()
        line.append(f"  {SYM_WARN} ", style=STYLE_WARNING)
        line.append(msg, style=STYLE_WARNING)
        self._log_lines.append(line)
        self._refresh()

    def log_info(self, msg: str) -> None:
        """Добавить информационное сообщение в журнал.

        Args:
            msg: Текст сообщения.
        """
        line = Text()
        line.append(f"  {msg}", style=STYLE_MUTED)
        self._log_lines.append(line)
        self._refresh()

    def mark_stage_completed(self) -> None:
        """Отметить текущий этап как завершённый."""
        self._completed_stages += 1
        self._refresh()

    def update_operation(self, op: str) -> None:
        """Обновить текст текущей операции.

        Args:
            op: Краткое описание выполняемой операции.
        """
        self._operation = op
        self._refresh()

    def update_packages(self, done: int, total: int) -> None:
        """Обновить счётчик установленных пакетов.

        Args:
            done: Количество установленных пакетов.
            total: Общее количество пакетов для установки.
        """
        self._packages_done = done
        self._packages_total = total
        self._refresh()

    # ─── Получение строк лога (для error_screen) ────────────

    def get_log_lines(self, count: int = 10) -> list[str]:
        """Вернуть последние N строк лога в виде простых строк.

        Args:
            count: Количество строк для извлечения.

        Returns:
            Список строк лога (без Rich-разметки).
        """
        lines = list(self._log_lines)
        tail = lines[-count:] if len(lines) >= count else lines
        return [line.plain for line in tail]

    # ─── Внутренние методы отрисовки ────────────────────────

    def _refresh(self) -> None:
        """Обновить Live-дисплей текущим состоянием."""
        if self._live is not None:
            self._live.update(self._make_layout())

    def _calc_percentage(self) -> float:
        """Рассчитать общий процент выполнения.

        Returns:
            Процент от 0.0 до 100.0.
        """
        if self._completed_stages == 0:
            return 0.0
        # Процент на основе фактически завершённых этапов
        return min(100.0, (self._completed_stages / self._actual_total) * 100.0)

    def _calc_eta(self, elapsed: float, percent: float) -> float:
        """Рассчитать оставшееся время (ETA).

        Args:
            elapsed: Прошедшее время в секундах.
            percent: Текущий процент выполнения.

        Returns:
            Оставшееся время в секундах (0 если нельзя вычислить).
        """
        if percent <= 0.0 or elapsed <= 0.0:
            return 0.0
        # Линейная экстраполяция
        total_estimated = elapsed / (percent / 100.0)
        remaining = total_estimated - elapsed
        return max(0.0, remaining)

    def _make_layout(self) -> Layout:
        """Построить двухпанельный макет.

        Returns:
            Rich Layout с панелями лога и прогресса.
        """
        layout = Layout()

        # Верхняя панель — журнал команд (занимает большую часть)
        layout.split_column(
            Layout(self._render_log(), name="log", ratio=3),
            Layout(self._render_progress(), name="progress", ratio=2),
        )

        return layout

    def _render_log(self) -> Panel:
        """Отрисовать панель журнала команд.

        Returns:
            Rich Panel с последними строками лога.
        """
        # Собираем содержимое лога
        if self._log_lines:
            content = Group(*self._log_lines)
        else:
            # Пустой лог — показываем заглушку
            placeholder = Text("  Ожидание команд...", style=STYLE_MUTED)
            content = Group(placeholder)

        # Заголовок панели с процентом
        percent = self._calc_percentage()
        title = f"Журнал команд ─── {percent:.0f}%"

        return Panel(
            content,
            title=f"[bold {ARCH_BLUE}]{title}[/]",
            title_align="left",
            border_style=ARCH_BLUE,
            padding=(0, 1),
        )

    def _render_progress(self) -> Panel:
        """Отрисовать панель прогресса.

        Returns:
            Rich Panel с прогресс-баром, таймерами и информацией.
        """
        now = time.monotonic()
        elapsed = now - self._start_time
        percent = self._calc_percentage()
        eta = self._calc_eta(elapsed, percent)

        # Строки панели прогресса
        lines: list[Text | str] = []

        # Строка 1: Общий прогресс — Этап N из M
        stage_info = Text()
        stage_info.append("  Общий прогресс:  ", style=f"bold {ARCH_BLUE}")
        stage_info.append(
            t("progress.stage", current=self._current_stage, total=self.total_stages),
        )
        lines.append(stage_info)

        # Строка 2: Прогресс-бар
        bar_line = Text("  ")
        bar_line.append_text(_build_progress_bar(percent))
        lines.append(bar_line)

        # Строка 3: Текущий этап
        if self._stage_name:
            stage_line = Text()
            stage_line.append("  Текущий этап:    ", style=f"bold {ARCH_BLUE}")
            stage_line.append(self._stage_name)
            lines.append(stage_line)

        # Строка 4: Текущая операция (если есть)
        if self._operation:
            op_line = Text()
            op_line.append("  Операция:        ", style=STYLE_MUTED)
            op_line.append(self._operation, style=STYLE_MUTED)
            lines.append(op_line)

        # Строка 5: Счётчик пакетов (если есть)
        if self._packages_total > 0:
            pkg_line = Text()
            pkg_line.append("  Пакеты:          ", style=STYLE_MUTED)
            pkg_line.append(
                t(
                    "progress.packages",
                    done=self._packages_done,
                    total=self._packages_total,
                ),
            )
            lines.append(pkg_line)

        # Строка 6: Таймеры (прошло / осталось)
        timer_line = Text()
        elapsed_str = _format_duration(elapsed)
        timer_line.append(f"  \u23f1  Прошло: {elapsed_str}", style=STYLE_MUTED)
        if percent > 0:
            eta_str = _format_duration(eta)
            timer_line.append(f"    \u23f3 Осталось \u2248 {eta_str}", style=STYLE_MUTED)
        lines.append(timer_line)

        content = Group(*lines)

        # Заголовок панели
        percent_display = percent
        title = f"Прогресс ─── {percent_display:.0f}%"

        return Panel(
            content,
            title=f"[bold {ARCH_BLUE}]{title}[/]",
            title_align="left",
            border_style=ARCH_BLUE,
            padding=(0, 1),
        )

    # ─── Контекстный менеджер ───────────────────────────────

    def __enter__(self) -> ProgressUI:
        """Поддержка использования как контекстного менеджера."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Гарантированная остановка Live-дисплея при выходе."""
        self.stop()
