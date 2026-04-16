"""Конфигурация установки Arch Linux.

Содержит датакласс InstallConfig, который хранит все параметры,
выбранные пользователем в визарде, и валидирует их при инициализации.
"""

from __future__ import annotations

from dataclasses import dataclass

from .exceptions import ValidationError


@dataclass
class InstallConfig:
    """Конфигурация установки, заполняемая в визарде.

    Все параметры имеют разумные значения по умолчанию.
    Валидация выполняется в __post_init__ только для непустых полей
    и только когда demo_mode отключён.

    Attributes:
        lang: Язык интерфейса (``ru`` или ``en``).
        disk: Путь к целевому диску (например, ``/dev/sda``).
        username: Имя создаваемого пользователя.
        user_password: Пароль пользователя.
        root_password: Пароль root.
        hostname: Имя хоста (по умолчанию ``archlinux``).
        timezone: Часовой пояс (по умолчанию ``Europe/Moscow``).
        locale: Системная локаль (по умолчанию ``ru_RU.UTF-8``).
        is_uefi: Режим загрузки UEFI (True) или BIOS (False).
        demo_mode: Демонстрационный режим без реальных команд.
        debug: Режим отладки с расширенным логированием.
    """

    lang: str = "ru"
    disk: str = ""
    username: str = ""
    user_password: str = ""
    root_password: str = ""
    hostname: str = "archlinux"
    timezone: str = "Europe/Moscow"
    locale: str = "ru_RU.UTF-8"
    is_uefi: bool = True
    demo_mode: bool = False
    debug: bool = False

    def __post_init__(self) -> None:
        """Валидация полей после инициализации.

        В демо-режиме валидация пропускается.
        Пустые строковые поля не валидируются — они будут
        заполнены позже через визард.

        Raises:
            ValidationError: Если какое-либо поле не прошло проверку.
        """
        if self.demo_mode:
            return

        # Импорт внутри метода для избежания циклических зависимостей
        from .utils.validators import (
            validate_hostname,
            validate_password,
            validate_username,
        )

        # Валидируем только непустые поля
        if self.username:
            ok, msg = validate_username(self.username)
            if not ok:
                raise ValidationError(msg)

        if self.user_password:
            ok, msg = validate_password(self.user_password)
            if not ok:
                raise ValidationError(msg)

        if self.root_password:
            ok, msg = validate_password(self.root_password)
            if not ok:
                raise ValidationError(msg)

        if self.hostname:
            ok, msg = validate_hostname(self.hostname)
            if not ok:
                raise ValidationError(msg)
