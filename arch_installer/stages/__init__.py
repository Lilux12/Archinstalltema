"""Этапы установки Arch Linux.

Экспортирует все классы этапов и список STAGE_ORDER,
определяющий порядок выполнения установки.
"""

from .aur import AurStage
from .base_install import BaseInstallStage
from .base_stage import BaseStage
from .bootloader import BootloaderStage
from .dev_tools import DevToolsStage
from .disk import DiskStage
from .finalize import FinalizeStage
from .gnome import GnomeStage
from .multilib import MultilibStage
from .network import NetworkStage
from .nvidia import NvidiaStage
from .preflight import PreflightStage
from .system_config import SystemConfigStage
from .udev_rules import UdevRulesStage
from .vscode_claude import VsCodeClaudeStage

# Порядок выполнения этапов установки.
# Этапы 0 (preflight) и 1 (wizard) выполняются оркестратором отдельно.
# Здесь перечислены этапы 2-14 в порядке выполнения.
STAGE_ORDER: list[type[BaseStage]] = [
    DiskStage,          # 2 — Разметка диска
    BaseInstallStage,   # 3 — Установка базовой системы
    SystemConfigStage,  # 4 — Системная конфигурация
    BootloaderStage,    # 5 — Загрузчик
    MultilibStage,      # 6 — Multilib-репозиторий
    GnomeStage,         # 7 — Установка GNOME
    NvidiaStage,        # 8 — Драйвер NVIDIA
    NetworkStage,       # 9 — Сеть и DNS
    DevToolsStage,      # 10 — Инструменты разработки
    UdevRulesStage,     # 11 — Udev-правила микроконтроллеров
    AurStage,           # 12 — AUR helper и авто-обновления
    VsCodeClaudeStage,  # 13 — VS Code и Claude Code
    FinalizeStage,      # 14 — Финализация
]

__all__ = [
    "AurStage",
    "BaseInstallStage",
    "BaseStage",
    "BootloaderStage",
    "DevToolsStage",
    "DiskStage",
    "FinalizeStage",
    "GnomeStage",
    "MultilibStage",
    "NetworkStage",
    "NvidiaStage",
    "PreflightStage",
    "STAGE_ORDER",
    "SystemConfigStage",
    "UdevRulesStage",
    "VsCodeClaudeStage",
]
