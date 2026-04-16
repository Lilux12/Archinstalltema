"""Модуль логирования установщика.

Настраивает двойное логирование: в файл (полный DEBUG-лог)
и в TUI-интерфейс (INFO и выше) через Rich-разметку.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Путь к файлу лога установки
LOG_FILE = Path("/tmp/arch_install.log")

# Формат записи в файл
FILE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Формат записи в UI (без временных меток — они загромождают интерфейс)
UI_FORMAT = "%(message)s"


class UIHandler(logging.Handler):
    """Обработчик логов, отправляющий сообщения в TUI-интерфейс.

    Хранит ссылку на объект прогресс-панели Rich. Если объект
    не установлен (None), сообщения молча отбрасываются.
    """

    def __init__(self, level: int = logging.INFO) -> None:
        """Инициализация обработчика.

        Args:
            level: Минимальный уровень логирования для UI.
        """
        super().__init__(level)
        self._ui: Any | None = None

    @property
    def ui(self) -> Any | None:
        """Текущий объект прогресс-панели UI."""
        return self._ui

    @ui.setter
    def ui(self, value: Any | None) -> None:
        """Установить объект прогресс-панели UI.

        Args:
            value: Объект UI с методом log() или None.
        """
        self._ui = value

    def emit(self, record: logging.LogRecord) -> None:
        """Отправить запись лога в UI.

        Если UI не установлен — запись отбрасывается.
        Уровни WARNING и выше выделяются цветом.

        Args:
            record: Запись лога для отображения.
        """
        if self._ui is None:
            return

        try:
            message = self.format(record)
            # Добавляем Rich-разметку в зависимости от уровня
            if record.levelno >= logging.ERROR:
                markup = f"[bold red]{message}[/bold red]"
            elif record.levelno >= logging.WARNING:
                markup = f"[yellow]{message}[/yellow]"
            elif record.levelno >= logging.INFO:
                markup = f"[dim white]{message}[/dim white]"
            else:
                markup = message

            # Вызываем метод log() у объекта UI
            if hasattr(self._ui, "log"):
                self._ui.log(markup)
        except Exception:  # noqa: BLE001
            # Ошибки логирования не должны прерывать установку
            self.handleError(record)


# Глобальный экземпляр UI-обработчика (один на всё приложение)
_ui_handler: UIHandler | None = None


def get_ui_handler() -> UIHandler | None:
    """Получить глобальный UI-обработчик.

    Returns:
        Экземпляр UIHandler или None, если логирование не настроено.
    """
    return _ui_handler


def setup_logging(*, ui: Any | None = None, debug: bool = False) -> logging.Logger:
    """Настроить систему логирования установщика.

    Создаёт два обработчика:
    - FileHandler: пишет в /tmp/arch_install.log на уровне DEBUG
    - UIHandler: отправляет сообщения в TUI на уровне INFO

    Args:
        ui: Объект прогресс-панели Rich (опционально).
        debug: Если True, корневой логгер работает на уровне DEBUG.

    Returns:
        Настроенный корневой логгер приложения.
    """
    global _ui_handler  # noqa: PLW0603

    # Корневой логгер приложения
    root_logger = logging.getLogger("arch_installer")
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Очищаем старые обработчики (при повторном вызове)
    root_logger.handlers.clear()

    # --- Файловый обработчик ---
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
    root_logger.addHandler(file_handler)

    # --- UI-обработчик ---
    _ui_handler = UIHandler(level=logging.INFO)
    _ui_handler.setFormatter(logging.Formatter(UI_FORMAT))
    _ui_handler.ui = ui
    root_logger.addHandler(_ui_handler)

    root_logger.debug("Логирование инициализировано, файл: %s", LOG_FILE)
    return root_logger
