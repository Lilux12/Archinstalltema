"""Тесты конфигурации установщика."""

import pytest

from arch_installer.config import InstallConfig
from arch_installer.exceptions import ValidationError


class TestInstallConfig:
    """Тесты InstallConfig dataclass."""

    def test_default_values(self) -> None:
        """Проверка значений по умолчанию."""
        config = InstallConfig()
        assert config.lang == "ru"
        assert config.disk == ""
        assert config.username == ""
        assert config.hostname == "archlinux"
        assert config.timezone == "Europe/Moscow"
        assert config.locale == "ru_RU.UTF-8"
        assert config.is_uefi is True
        assert config.demo_mode is False
        assert config.debug is False

    def test_demo_mode_skips_validation(self) -> None:
        """В демо-режиме валидация пропускается."""
        config = InstallConfig(
            demo_mode=True,
            username="INVALID!!!",
            hostname="---invalid---",
        )
        assert config.username == "INVALID!!!"
        assert config.hostname == "---invalid---"

    def test_empty_fields_no_validation(self) -> None:
        """Пустые поля не вызывают ошибку валидации."""
        config = InstallConfig(username="", user_password="")
        assert config.username == ""
        assert config.user_password == ""

    def test_valid_config(self) -> None:
        """Корректная конфигурация проходит валидацию."""
        config = InstallConfig(
            username="ivan",
            user_password="secure123",
            root_password="rootpass1",
            hostname="myarch",
        )
        assert config.username == "ivan"
        assert config.hostname == "myarch"

    def test_invalid_username_raises(self) -> None:
        """Некорректное имя пользователя вызывает ошибку."""
        with pytest.raises(ValidationError):
            InstallConfig(username="root")

    def test_invalid_hostname_raises(self) -> None:
        """Некорректный hostname вызывает ошибку."""
        with pytest.raises(ValidationError):
            InstallConfig(hostname="-invalid")

    def test_short_password_raises(self) -> None:
        """Слишком короткий пароль вызывает ошибку."""
        with pytest.raises(ValidationError):
            InstallConfig(user_password="123")

    def test_custom_timezone(self) -> None:
        """Пользовательский часовой пояс."""
        config = InstallConfig(timezone="America/New_York")
        assert config.timezone == "America/New_York"

    def test_english_lang(self) -> None:
        """Английский язык интерфейса."""
        config = InstallConfig(lang="en")
        assert config.lang == "en"
