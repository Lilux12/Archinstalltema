"""Интернационализация установщика Arch Linux.

Предоставляет механизм переводов UI-строк на русский и английский
языки. Все строки интерфейса должны получаться через функцию ``t()``,
что позволяет переключить язык в любой момент работы программы.

Использование::

    from arch_installer.i18n import t, set_lang

    set_lang("ru")
    print(t("welcome.title"))
    print(t("wizard.step", current=3, total=8))
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════
#  Словарь переводов
# ═══════════════════════════════════════════════════════════════

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ─── Русский ─────────────────────────────────────────────
    "ru": {
        # Стартовый экран
        "welcome.title": "Arch Installer — Персональная сборка",
        "welcome.subtitle": "v{version}  │  GNOME + NVIDIA + Dev Environment",
        "welcome.press_enter": "Нажмите ENTER чтобы начать",

        # Визард
        "wizard.step": "Шаг {current} из {total}",
        "wizard.language": "Язык интерфейса",
        "wizard.disk": "Выберите диск для установки",
        "wizard.disk_warning": (
            "⚠⚠⚠ ВНИМАНИЕ ⚠⚠⚠\n\n"
            "Диск {disk} ({model}, {size}) будет ПОЛНОСТЬЮ СТЁРТ.\n"
            "Все данные будут безвозвратно потеряны.\n\n"
            "Для подтверждения введите слово YES (заглавными буквами):"
        ),
        "wizard.username": "Имя пользователя",
        "wizard.password": "Пароль пользователя",
        "wizard.root_password": "Пароль root",
        "wizard.hostname": "Имя хоста",
        "wizard.timezone": "Часовой пояс",
        "wizard.summary": "Параметры установки",
        "wizard.confirm": "Начать установку?",

        # Прогресс установки
        "progress.stage": "Этап {current} из {total}",
        "progress.elapsed": "Прошло: {time}",
        "progress.remaining": "Осталось ≈ {time}",
        "progress.operation": "Операция: {operation}",
        "progress.packages": "{done}/{total} пакетов",

        # Ошибки
        "error.title": "ОШИБКА НА ЭТАПЕ: {stage}",
        "error.retry": "[R] Повторить",
        "error.skip": "[S] Пропустить",
        "error.abort": "[A] Выйти",
        "error.last_lines": "Последние {count} строк лога:",

        # Финальный экран
        "final.success": "Установка завершена успешно",
        "final.time": "Время установки: {time}",
        "final.packages": "Установлено пакетов: {count}",
        "final.size": "Размер системы: {size}",
        "final.ready": "Система готова к использованию.",
        "final.reboot": "Перезагрузить сейчас",
        "final.shell": "Выйти в shell",

        # Предварительные проверки
        "preflight.root": "Запуск от root",
        "preflight.iso": "Arch Linux live-ISO",
        "preflight.internet": "Подключение к интернету",
        "preflight.ram": "Объём оперативной памяти",
        "preflight.space": "Свободное место в tmpfs",
        "preflight.uefi": "Режим загрузки UEFI/BIOS",

        # Названия этапов (по номерам)
        "stage.0": "Предварительные проверки",
        "stage.1": "Мастер настройки",
        "stage.2": "Разметка диска",
        "stage.3": "Установка базовой системы",
        "stage.4": "Системная конфигурация",
        "stage.5": "Загрузчик",
        "stage.6": "Multilib-репозиторий",
        "stage.7": "Установка GNOME",
        "stage.8": "Драйвер NVIDIA",
        "stage.9": "Сеть и DNS",
        "stage.10": "Инструменты разработки",
        "stage.11": "Udev-правила микроконтроллеров",
        "stage.12": "AUR helper и авто-обновления",
        "stage.13": "VS Code и Claude Code",
        "stage.14": "Финализация",
    },

    # ─── English ─────────────────────────────────────────────
    "en": {
        # Welcome screen
        "welcome.title": "Arch Installer — Personal Build",
        "welcome.subtitle": "v{version}  │  GNOME + NVIDIA + Dev Environment",
        "welcome.press_enter": "Press ENTER to start",

        # Wizard
        "wizard.step": "Step {current} of {total}",
        "wizard.language": "Interface language",
        "wizard.disk": "Select installation disk",
        "wizard.disk_warning": (
            "⚠⚠⚠ WARNING ⚠⚠⚠\n\n"
            "Disk {disk} ({model}, {size}) will be COMPLETELY ERASED.\n"
            "All data will be permanently lost.\n\n"
            "Type YES (in capital letters) to confirm:"
        ),
        "wizard.username": "Username",
        "wizard.password": "User password",
        "wizard.root_password": "Root password",
        "wizard.hostname": "Hostname",
        "wizard.timezone": "Timezone",
        "wizard.summary": "Installation parameters",
        "wizard.confirm": "Start installation?",

        # Installation progress
        "progress.stage": "Stage {current} of {total}",
        "progress.elapsed": "Elapsed: {time}",
        "progress.remaining": "Remaining ≈ {time}",
        "progress.operation": "Operation: {operation}",
        "progress.packages": "{done}/{total} packages",

        # Errors
        "error.title": "ERROR AT STAGE: {stage}",
        "error.retry": "[R] Retry",
        "error.skip": "[S] Skip",
        "error.abort": "[A] Abort",
        "error.last_lines": "Last {count} log lines:",

        # Final screen
        "final.success": "Installation completed successfully",
        "final.time": "Installation time: {time}",
        "final.packages": "Packages installed: {count}",
        "final.size": "System size: {size}",
        "final.ready": "System is ready to use.",
        "final.reboot": "Reboot now",
        "final.shell": "Exit to shell",

        # Preflight checks
        "preflight.root": "Running as root",
        "preflight.iso": "Arch Linux live-ISO",
        "preflight.internet": "Internet connection",
        "preflight.ram": "RAM amount",
        "preflight.space": "Free space in tmpfs",
        "preflight.uefi": "Boot mode UEFI/BIOS",

        # Stage names (by number)
        "stage.0": "Preflight checks",
        "stage.1": "Setup wizard",
        "stage.2": "Disk partitioning",
        "stage.3": "Base system installation",
        "stage.4": "System configuration",
        "stage.5": "Bootloader",
        "stage.6": "Multilib repository",
        "stage.7": "GNOME installation",
        "stage.8": "NVIDIA driver",
        "stage.9": "Network and DNS",
        "stage.10": "Development tools",
        "stage.11": "Udev rules for microcontrollers",
        "stage.12": "AUR helper and auto-updates",
        "stage.13": "VS Code and Claude Code",
        "stage.14": "Finalization",
    },
}

# ═══════════════════════════════════════════════════════════════
#  Текущий язык (модульная переменная)
# ═══════════════════════════════════════════════════════════════

_current_lang: str = "ru"


# ═══════════════════════════════════════════════════════════════
#  Публичный API
# ═══════════════════════════════════════════════════════════════


def set_lang(lang: str) -> None:
    """Установить текущий язык интерфейса.

    Args:
        lang: Код языка (``ru`` или ``en``).

    Raises:
        ValueError: Если язык не поддерживается.
    """
    global _current_lang  # noqa: PLW0603

    if lang not in TRANSLATIONS:
        supported = ", ".join(sorted(TRANSLATIONS.keys()))
        raise ValueError(
            f"Язык '{lang}' не поддерживается. Доступные: {supported}"
        )

    _current_lang = lang


def t(key: str, **kwargs: object) -> str:
    """Получить переведённую строку по ключу.

    Подставляет именованные параметры через ``str.format()``.

    Args:
        key: Ключ перевода в формате ``section.name``
             (например, ``welcome.title``).
        **kwargs: Параметры для подстановки в шаблон
                  (например, ``current=3, total=8``).

    Returns:
        Переведённая строка с подставленными параметрами.
        Если ключ не найден, возвращается сам ключ в квадратных
        скобках как индикатор отсутствующего перевода.
    """
    lang_dict = TRANSLATIONS.get(_current_lang, TRANSLATIONS["ru"])
    template = lang_dict.get(key)

    if template is None:
        # Ключ не найден — возвращаем маркер для отладки
        return f"[{key}]"

    if kwargs:
        return template.format(**kwargs)

    return template
