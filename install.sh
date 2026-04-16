#!/usr/bin/env bash
set -euo pipefail

# Проверка что мы в Arch live-ISO
if ! grep -q "archiso" /proc/cmdline 2>/dev/null && [ ! -f /etc/arch-release ]; then
    echo "ERROR: Этот скрипт должен запускаться из Arch Linux live-ISO"
    exit 1
fi

# Проверка root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Нужны права root"
    exit 1
fi

# Проверка интернета
if ! ping -c 1 -W 3 archlinux.org &>/dev/null; then
    echo "ERROR: Нет интернета. Подключите сеть (iwctl для Wi-Fi)."
    exit 1
fi

echo "==> Синхронизация pacman..."
pacman -Sy --noconfirm

echo "==> Установка Python-зависимостей..."
pacman -S --noconfirm python python-rich python-pip git

# Textual может не быть в репо — пробуем из pip
if ! pacman -S --noconfirm python-textual 2>/dev/null; then
    pip install --break-system-packages textual 2>/dev/null || true
fi

echo "==> Запуск установщика..."
cd "$(dirname "$0")"
exec python -m arch_installer "$@"
