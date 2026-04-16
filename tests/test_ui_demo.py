"""Smoke-тесты UI компонентов в демо-режиме."""

import pytest

from arch_installer.config import InstallConfig
from arch_installer.i18n import set_lang, t
from arch_installer.ui.theme import (
    ARCH_BLUE,
    ERROR_RED,
    SUCCESS_GREEN,
    SYM_CHECK,
    SYM_CROSS,
    SYM_WARN,
)


class TestTheme:
    """Тесты цветов и символов темы."""

    def test_colors_are_hex(self) -> None:
        assert ARCH_BLUE.startswith("#")
        assert SUCCESS_GREEN.startswith("#")
        assert ERROR_RED.startswith("#")

    def test_symbols_defined(self) -> None:
        assert SYM_CHECK == "✓"
        assert SYM_CROSS == "✗"
        assert SYM_WARN == "⚠"


class TestI18n:
    """Тесты системы переводов."""

    def test_russian_default(self) -> None:
        set_lang("ru")
        title = t("welcome.title")
        assert "Arch Installer" in title

    def test_english_translation(self) -> None:
        set_lang("en")
        title = t("welcome.title")
        assert "Arch Installer" in title
        set_lang("ru")

    def test_translation_with_params(self) -> None:
        set_lang("ru")
        step = t("wizard.step", current=3, total=8)
        assert "3" in step
        assert "8" in step

    def test_missing_key_returns_marker(self) -> None:
        result = t("nonexistent.key")
        assert "nonexistent.key" in result

    def test_all_stages_have_names(self) -> None:
        set_lang("ru")
        for i in range(15):
            name = t(f"stage.{i}")
            assert f"stage.{i}" not in name or name != f"stage.{i}"

    def test_invalid_lang_raises(self) -> None:
        with pytest.raises(ValueError):
            set_lang("fr")


class TestProgressUI:
    """Тесты ProgressUI без реального дисплея."""

    def test_progress_ui_creation(self) -> None:
        from arch_installer.ui.progress import ProgressUI

        ui = ProgressUI(total_stages=14)
        assert ui.total_stages == 14

    def test_log_methods(self) -> None:
        from arch_installer.ui.progress import ProgressUI

        ui = ProgressUI(total_stages=14)
        # Эти методы не должны падать без запущенного Live
        ui.log_command("pacman -Syu")
        ui.log_success("Пакеты обновлены")
        ui.log_error("Ошибка загрузки")
        ui.log_info("Информация")

    def test_set_stage(self) -> None:
        from arch_installer.ui.progress import ProgressUI

        ui = ProgressUI(total_stages=14)
        ui.set_stage(3, "Установка базовой системы")
        assert ui._current_stage == 3


class TestInstallConfigDemo:
    """Тесты конфигурации в демо-режиме."""

    def test_demo_config(self) -> None:
        config = InstallConfig(demo_mode=True)
        assert config.demo_mode is True
        assert config.disk == ""

    def test_demo_allows_invalid_data(self) -> None:
        config = InstallConfig(
            demo_mode=True,
            username="root",
            hostname="-bad-",
        )
        assert config.username == "root"
