"""Предварительные проверки системы перед установкой.

Проверяет: запуск от root, live-ISO окружение, интернет,
объём ОЗУ, свободное место, режим загрузки (UEFI/BIOS).
При критической проблеме бросает PreflightError.
"""

from __future__ import annotations

import time

from ..constants import MIN_FREE_SPACE_MIB, MIN_RAM_GIB, WARN_RAM_GIB
from ..exceptions import PreflightError
from ..i18n import t
from ..utils.system_info import gather_system_info
from .base_stage import BaseStage


class PreflightStage(BaseStage):
    """Этап предварительных проверок системы.

    Собирает информацию о системе и проверяет минимальные
    требования для начала установки. Результаты проверок
    записываются в config.is_uefi.
    """

    name = "Предварительные проверки"
    weight = 1
    skippable = False

    def run(self) -> None:
        """Выполнить все предварительные проверки.

        Raises:
            PreflightError: Если система не удовлетворяет
                минимальным требованиям.
        """

        if self.config.demo_mode:
            self._run_demo()
            return

        # Собираем информацию о системе
        self.ui.log_command("gather_system_info()")
        info = gather_system_info()

        # Проверка 1: Запуск от root
        self.ui.log_command(t("preflight.root"))
        if info.is_root:
            self.ui.log_success(t("preflight.root"))
        else:
            self.ui.log_error(t("preflight.root"))
            raise PreflightError(
                "Установщик должен быть запущен от имени root (sudo)."
            )

        # Проверка 2: Live-ISO окружение
        self.ui.log_command(t("preflight.iso"))
        if info.is_live_iso:
            self.ui.log_success(t("preflight.iso"))
        else:
            self.ui.log_error(t("preflight.iso"))
            raise PreflightError(
                "Установщик должен быть запущен из Arch Linux live-ISO."
            )

        # Проверка 3: Интернет-соединение
        self.ui.log_command(t("preflight.internet"))
        if info.has_internet:
            self.ui.log_success(t("preflight.internet"))
        else:
            self.ui.log_error(t("preflight.internet"))
            raise PreflightError(
                "Отсутствует подключение к интернету. "
                "Проверьте сетевое соединение."
            )

        # Проверка 4: Объём ОЗУ
        self.ui.log_command(f"{t('preflight.ram')}: {info.ram_gib:.1f} GiB")
        if info.ram_gib < MIN_RAM_GIB:
            self.ui.log_error(
                f"{t('preflight.ram')}: {info.ram_gib:.1f} GiB "
                f"(минимум {MIN_RAM_GIB} GiB)"
            )
            raise PreflightError(
                f"Недостаточно ОЗУ: {info.ram_gib:.1f} GiB "
                f"(требуется минимум {MIN_RAM_GIB} GiB)."
            )
        elif info.ram_gib < WARN_RAM_GIB:
            self.ui.log_warning(
                f"{t('preflight.ram')}: {info.ram_gib:.1f} GiB "
                f"(рекомендуется {WARN_RAM_GIB} GiB)"
            )
        else:
            self.ui.log_success(
                f"{t('preflight.ram')}: {info.ram_gib:.1f} GiB"
            )

        # Проверка 5: Свободное место в tmpfs (предупреждение, не критично —
        # пакеты скачиваются на целевой диск, а не в tmpfs)
        self.ui.log_command(
            f"{t('preflight.space')}: {info.free_space_mib} MiB"
        )
        if info.free_space_mib < MIN_FREE_SPACE_MIB:
            self.ui.log_warning(
                f"{t('preflight.space')}: {info.free_space_mib} MiB "
                f"(рекомендуется {MIN_FREE_SPACE_MIB} MiB, "
                f"установка может работать медленнее)"
            )
        else:
            self.ui.log_success(
                f"{t('preflight.space')}: {info.free_space_mib} MiB"
            )

        # Проверка 6: Режим загрузки UEFI/BIOS
        boot_mode = "UEFI" if info.is_uefi else "BIOS/Legacy"
        self.ui.log_command(f"{t('preflight.uefi')}: {boot_mode}")
        self.ui.log_success(f"{t('preflight.uefi')}: {boot_mode}")

        # Сохраняем режим загрузки в конфигурацию
        self.config.is_uefi = info.is_uefi

        self.ui.log_success("Все предварительные проверки пройдены")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация проверок без реальных команд."""
        # Имитация проверки root
        self.ui.log_command(t("preflight.root"))
        time.sleep(0.3)
        self.ui.log_success(t("preflight.root"))

        # Имитация проверки live-ISO
        self.ui.log_command(t("preflight.iso"))
        time.sleep(0.3)
        self.ui.log_success(t("preflight.iso"))

        # Имитация проверки интернета
        self.ui.log_command(t("preflight.internet"))
        time.sleep(0.5)
        self.ui.log_success(t("preflight.internet"))

        # Имитация проверки ОЗУ
        self.ui.log_command(f"{t('preflight.ram')}: 16.0 GiB")
        time.sleep(0.2)
        self.ui.log_success(f"{t('preflight.ram')}: 16.0 GiB")

        # Имитация проверки свободного места
        self.ui.log_command(f"{t('preflight.space')}: 2048 MiB")
        time.sleep(0.2)
        self.ui.log_success(f"{t('preflight.space')}: 2048 MiB")

        # Имитация проверки UEFI
        boot_mode = "UEFI" if self.config.is_uefi else "BIOS/Legacy"
        self.ui.log_command(f"{t('preflight.uefi')}: {boot_mode}")
        time.sleep(0.2)
        self.ui.log_success(f"{t('preflight.uefi')}: {boot_mode}")

        self.ui.log_success("Все предварительные проверки пройдены")
