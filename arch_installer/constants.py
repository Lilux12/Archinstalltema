"""Константы установщика Arch Linux.

Содержит все неизменяемые значения: версию, пути, пороговые значения,
списки пакетов, имена этапов и прочие параметры конфигурации.
"""

from __future__ import annotations

from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  Основные параметры приложения
# ═══════════════════════════════════════════════════════════════

VERSION: str = "1.0.0"
APP_NAME: str = "Arch Installer"

# ═══════════════════════════════════════════════════════════════
#  Пути
# ═══════════════════════════════════════════════════════════════

MOUNT_POINT: Path = Path("/mnt")
LOG_FILE: Path = Path("/tmp/arch_install.log")

# ═══════════════════════════════════════════════════════════════
#  Пороговые значения ресурсов
# ═══════════════════════════════════════════════════════════════

# Минимальный объём ОЗУ (GiB) — установка не запустится
MIN_RAM_GIB: int = 2

# Рекомендуемый объём ОЗУ (GiB) — ниже будет предупреждение
WARN_RAM_GIB: int = 4

# Минимум свободного места в tmpfs live-ISO (MiB)
MIN_FREE_SPACE_MIB: int = 500

# Минимальный размер целевого диска (GiB)
MIN_DISK_SIZE_GIB: int = 10

# ═══════════════════════════════════════════════════════════════
#  Валидация пользователей
# ═══════════════════════════════════════════════════════════════

FORBIDDEN_USERNAMES: frozenset[str] = frozenset({
    "root",
    "daemon",
    "bin",
    "sys",
    "nobody",
})

# ═══════════════════════════════════════════════════════════════
#  Списки пакетов
# ═══════════════════════════════════════════════════════════════

# Базовые пакеты для pacstrap
BASE_PACKAGES: list[str] = [
    "base",
    "base-devel",
    "linux",
    "linux-firmware",
    "linux-headers",
    "networkmanager",
    "nano",
    "vim",
    "sudo",
    "git",
    "man-db",
    "man-pages",
    "texinfo",
]

# Пакеты рабочего окружения GNOME
GNOME_PACKAGES: list[str] = [
    "xorg-server",
    "xorg-xinit",
    "gnome",
    "gnome-tweaks",
    "gnome-shell-extensions",
    "gdm",
    "gnome-terminal",
    "nautilus",
    "gnome-text-editor",
]

# Проприетарный драйвер NVIDIA (для Pascal GP107 / GTX 1050 Ti)
NVIDIA_PACKAGES: list[str] = [
    "nvidia",
    "nvidia-utils",
    "nvidia-settings",
    "lib32-nvidia-utils",
    "opencl-nvidia",
    "lib32-opencl-nvidia",
]

# Инструменты разработки
DEV_PACKAGES: list[str] = [
    # Языки и среды выполнения
    "git",
    "python",
    "python-pip",
    "python-virtualenv",
    "python-pipx",
    "nodejs",
    "npm",
    "rust",
    "cargo",
    "go",
    # Компиляторы и сборка
    "gcc",
    "clang",
    "lld",
    "make",
    "cmake",
    "ninja",
    "meson",
    # Отладка и профилирование
    "gdb",
    "lldb",
    "strace",
    "ltrace",
    "valgrind",
    # Ассемблеры
    "nasm",
    "yasm",
    # Виртуализация
    "qemu-full",
    "qemu-user-static",
    "virt-manager",
    "libvirt",
    "edk2-ovmf",
    "dnsmasq",
    "iptables-nft",
    # Контейнеризация
    "docker",
    "docker-compose",
    "docker-buildx",
    # Утилиты
    "wget",
    "curl",
    "htop",
    "btop",
    "fastfetch",
    "unzip",
    "p7zip",
    "tar",
    "openssh",
]

# Сервисы, включаемые после установки dev-пакетов
DEV_SERVICES: list[str] = [
    "libvirtd",
    "docker",
]

# Группы, в которые добавляется пользователь для dev-инструментов
DEV_GROUPS: list[str] = [
    "libvirt",
    "docker",
    "kvm",
    "uucp",
    "tty",
]

# Основные группы пользователя системы
USER_GROUPS: list[str] = [
    "wheel",
    "video",
    "audio",
    "input",
    "storage",
    "optical",
    "network",
    "uucp",
]

# ═══════════════════════════════════════════════════════════════
#  Этапы установки
# ═══════════════════════════════════════════════════════════════

# Общее количество этапов
TOTAL_STAGES: int = 14

# Сопоставление номера этапа с его названием на русском
STAGE_NAMES: dict[int, str] = {
    0: "Предварительные проверки",
    1: "Мастер настройки",
    2: "Разметка диска",
    3: "Установка базовой системы",
    4: "Системная конфигурация",
    5: "Загрузчик",
    6: "Multilib-репозиторий",
    7: "Установка GNOME",
    8: "Драйвер NVIDIA",
    9: "Сеть и DNS",
    10: "Инструменты разработки",
    11: "Udev-правила микроконтроллеров",
    12: "AUR helper и авто-обновления",
    13: "VS Code и Claude Code",
    14: "Финализация",
}

# ═══════════════════════════════════════════════════════════════
#  Сеть и DNS
# ═══════════════════════════════════════════════════════════════

# DNS-серверы для NetworkManager (IPv4 + IPv6)
DNS_SERVERS: list[str] = [
    "111.88.96.50",
    "111.88.96.51",
    "2a00:ab00:1233:26::50",
    "2a00:ab00:1233:26::51",
]
