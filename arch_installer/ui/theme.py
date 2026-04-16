"""Цвета, символы и стили для TUI."""

from rich.style import Style
from rich.theme import Theme

# Акцентные цвета
ARCH_BLUE = "#1793D1"
SUCCESS_GREEN = "#00FF87"
WARNING_AMBER = "#FFAF00"
ERROR_RED = "#FF0055"
MUTED_GRAY = "#888888"
TEXT_WHITE = "#EEEEEE"

# Символы
SYM_CHECK = "✓"
SYM_CROSS = "✗"
SYM_WARN = "⚠"
SYM_ARROW = "►"
SYM_DIAMOND = "◆"
SYM_CIRCLE = "●"
SYM_CIRCLE_EMPTY = "○"

# Rich-стили
STYLE_TITLE = Style(color=ARCH_BLUE, bold=True)
STYLE_SUCCESS = Style(color=SUCCESS_GREEN)
STYLE_WARNING = Style(color=WARNING_AMBER)
STYLE_ERROR = Style(color=ERROR_RED, bold=True)
STYLE_MUTED = Style(color=MUTED_GRAY)
STYLE_COMMAND = Style(color="#87CEEB")
STYLE_HEADER = Style(color=ARCH_BLUE, bold=True)
STYLE_PROGRESS_BAR = Style(color=ARCH_BLUE)
STYLE_PROGRESS_DONE = Style(color=SUCCESS_GREEN)

# Тема для Rich Console
INSTALLER_THEME = Theme(
    {
        "title": STYLE_TITLE,
        "success": STYLE_SUCCESS,
        "warning": STYLE_WARNING,
        "error": STYLE_ERROR,
        "muted": STYLE_MUTED,
        "command": STYLE_COMMAND,
        "header": STYLE_HEADER,
        "info": Style(color=TEXT_WHITE),
    }
)
