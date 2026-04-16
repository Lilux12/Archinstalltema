"""Базовый абстрактный класс для всех этапов установки.

Определяет интерфейс, которому должен следовать каждый этап:
обязательный метод run(), опциональный rollback(), а также
метаданные (имя, вес для прогресса, возможность пропуска).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import InstallConfig


class BaseStage(ABC):
    """Абстрактный базовый класс этапа установки.

    Каждый этап наследуется от этого класса и реализует
    метод run(). При ошибке оркестратор может вызвать
    rollback() для отката изменений.

    Attributes:
        name: Человекочитаемое название этапа.
        weight: Относительный вес этапа для расчёта прогресса.
        skippable: Можно ли пропустить этап при ошибке.
    """

    name: str
    weight: int = 1
    skippable: bool = False

    def __init__(self, config: InstallConfig, ui: object) -> None:
        """Инициализация этапа.

        Args:
            config: Конфигурация установки с параметрами пользователя.
            ui: Объект ProgressUI для отображения прогресса и логов.
        """
        self.config = config
        self.ui = ui

    @abstractmethod
    def run(self) -> None:
        """Выполнить этап установки.

        Raises:
            StageError: При ошибке выполнения команды.
            PreflightError: При критической проблеме (только preflight).
        """
        ...

    def rollback(self) -> None:
        """Откатить изменения, сделанные этапом.

        По умолчанию ничего не делает. Переопределяется
        в этапах, которые могут выполнить корректный откат.
        """
