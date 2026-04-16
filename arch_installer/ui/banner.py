"""ASCII-баннер Arch Linux для стартового экрана."""

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..constants import VERSION
from ..i18n import t
from .theme import ARCH_BLUE, SYM_DIAMOND

# Большая буква "A" в стиле Arch Linux
ARCH_LOGO = r"""
                   [arch_blue]██[/]
                  [arch_blue]████[/]
                 [arch_blue]██[/][bold white]  [/][arch_blue]██[/]
                [arch_blue]██[/][bold white]    [/][arch_blue]██[/]
               [arch_blue]██[/][bold white]  ██  [/][arch_blue]██[/]
              [arch_blue]██[/][bold white]  ████  [/][arch_blue]██[/]
             [arch_blue]██[/][bold white]  ██████  [/][arch_blue]██[/]
            [arch_blue]██[/][bold white]  ██[/][arch_blue]██[/][bold white]████  [/][arch_blue]██[/]
           [arch_blue]██[/][bold white]  ██[/][arch_blue]████[/][bold white]████  [/][arch_blue]██[/]
          [arch_blue]██[/][bold white]        ████  [/][arch_blue]██[/]
         [arch_blue]██[/][bold white]          ████  [/][arch_blue]██[/]
        [arch_blue]██[/][bold white]                  [/][arch_blue]██[/]
       [arch_blue]████████████████████████[/]
"""


def show_banner(console: Console) -> None:
    """Показать стартовый баннер установщика."""
    console.clear()

    # Логотип
    console.print(Align.center(ARCH_LOGO), highlight=False)

    # Информационная панель
    title_text = t("welcome.title")
    subtitle_text = f"v{VERSION}  │  GNOME + NVIDIA + Dev Environment"

    info_panel = Panel(
        Align.center(
            Text.from_markup(
                f"[bold]{title_text}[/bold]\n"
                f"[dim]{subtitle_text}[/dim]"
            )
        ),
        border_style="bold blue",
        padding=(1, 4),
    )
    console.print(Align.center(info_panel, width=60))
    console.print()

    # Подсказка
    press_enter = t("welcome.press_enter")
    console.print(
        Align.center(
            Text.from_markup(f"[dim]{SYM_DIAMOND} {press_enter} {SYM_DIAMOND}[/dim]")
        )
    )
    console.print()


def wait_for_enter(console: Console) -> None:
    """Ждать нажатия Enter для начала."""
    try:
        console.input("")
    except (KeyboardInterrupt, EOFError):
        raise SystemExit(0)
