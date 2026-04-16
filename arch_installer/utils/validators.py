"""Модуль валидации пользовательского ввода.

Проверяет корректность имени пользователя, пароля, имени хоста
и часового пояса перед применением в процессе установки.
"""

from __future__ import annotations

import re
from pathlib import Path

# Регулярное выражение для имени пользователя Linux
_RE_USERNAME = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")

# Запрещённые системные имена пользователей
_FORBIDDEN_USERNAMES = frozenset({
    "root",
    "daemon",
    "bin",
    "sys",
    "nobody",
})

# Минимальная длина пароля
_MIN_PASSWORD_LENGTH = 6

# Регулярное выражение для имени хоста по RFC 1123
# Допускает буквы, цифры и дефисы; каждая метка до 63 символов;
# общая длина до 253 символов; не начинается/не заканчивается дефисом.
_RE_HOSTNAME_LABEL = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")

# Максимальная длина хостнейма
_MAX_HOSTNAME_LENGTH = 253

# Базовый путь к файлам часовых поясов
_ZONEINFO_PATH = Path("/usr/share/zoneinfo")


def validate_username(name: str) -> tuple[bool, str]:
    """Проверить корректность имени пользователя Linux.

    Требования:
    - Начинается с буквы a-z или подчёркивания
    - Содержит только a-z, 0-9, подчёркивание и дефис
    - Длина от 1 до 32 символов
    - Не совпадает с системными именами (root, daemon и др.)

    Args:
        name: Имя пользователя для проверки.

    Returns:
        Кортеж (is_valid, error_message). Если имя корректно,
        error_message будет пустой строкой.
    """
    if not name:
        return False, "Имя пользователя не может быть пустым"

    if name in _FORBIDDEN_USERNAMES:
        return False, f"Имя '{name}' зарезервировано системой"

    if not _RE_USERNAME.match(name):
        return False, (
            "Имя пользователя должно начинаться с буквы (a-z) или подчёркивания, "
            "содержать только строчные буквы, цифры, подчёркивания и дефисы, "
            "длина от 1 до 32 символов"
        )

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Проверить корректность пароля.

    Требования:
    - Минимум 6 символов

    Args:
        password: Пароль для проверки.

    Returns:
        Кортеж (is_valid, error_message).
    """
    if not password:
        return False, "Пароль не может быть пустым"

    if len(password) < _MIN_PASSWORD_LENGTH:
        return False, (
            f"Пароль слишком короткий: минимум {_MIN_PASSWORD_LENGTH} символов "
            f"(сейчас {len(password)})"
        )

    return True, ""


def validate_hostname(hostname: str) -> tuple[bool, str]:
    """Проверить корректность имени хоста по RFC 1123.

    Требования:
    - Общая длина не более 253 символов
    - Каждая метка (разделённая точками) от 1 до 63 символов
    - Содержит только буквы, цифры и дефисы
    - Метка не начинается и не заканчивается дефисом

    Args:
        hostname: Имя хоста для проверки.

    Returns:
        Кортеж (is_valid, error_message).
    """
    if not hostname:
        return False, "Имя хоста не может быть пустым"

    if len(hostname) > _MAX_HOSTNAME_LENGTH:
        return False, (
            f"Имя хоста слишком длинное: максимум {_MAX_HOSTNAME_LENGTH} символов "
            f"(сейчас {len(hostname)})"
        )

    # Разбиваем на метки по точкам
    labels = hostname.split(".")

    for label in labels:
        if not label:
            return False, "Имя хоста содержит пустую метку (двойная точка или точка в начале/конце)"

        if not _RE_HOSTNAME_LABEL.match(label):
            return False, (
                f"Метка '{label}' некорректна: допускаются только буквы, цифры и дефисы, "
                "метка не должна начинаться или заканчиваться дефисом, "
                "длина метки от 1 до 63 символов"
            )

    return True, ""


def validate_timezone(tz: str) -> tuple[bool, str]:
    """Проверить существование часового пояса.

    Проверяет наличие соответствующего файла в /usr/share/zoneinfo.

    Args:
        tz: Часовой пояс в формате Region/City (например, Europe/Moscow).

    Returns:
        Кортеж (is_valid, error_message).
    """
    if not tz:
        return False, "Часовой пояс не может быть пустым"

    # Защита от path traversal
    if ".." in tz or tz.startswith("/"):
        return False, "Недопустимый формат часового пояса"

    tz_path = _ZONEINFO_PATH / tz

    # Проверяем, что путь не вышел за пределы zoneinfo (защита от симлинков)
    try:
        resolved = tz_path.resolve()
        if not str(resolved).startswith(str(_ZONEINFO_PATH.resolve())):
            return False, "Недопустимый путь часового пояса"
    except OSError:
        return False, f"Часовой пояс '{tz}' не найден"

    if not tz_path.is_file():
        return False, (
            f"Часовой пояс '{tz}' не найден в {_ZONEINFO_PATH}. "
            "Используйте формат Region/City, например: Europe/Moscow"
        )

    return True, ""
