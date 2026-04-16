# Arch Installer — Персональная сборка

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?logo=arch-linux&logoColor=white)](https://archlinux.org/)

Красивый TUI-установщик Arch Linux с интерфейсом в стиле `archinstall`, но с авторским дизайном. Полностью автоматизирует установку персональной системы для разработки.

```
                   ██
                  ████
                 ██  ██
                ██    ██
               ██  ██  ██
              ██  ████  ██
             ██  ██████  ██
            ██████████████████

   ╔══════════════════════════════════════════════════╗
   ║   Arch Installer — Персональная сборка           ║
   ║   v1.0.0  │  GNOME + NVIDIA + Dev Environment    ║
   ╚══════════════════════════════════════════════════╝
```

## Что устанавливается

| Этап | Описание | Пакеты |
|------|----------|--------|
| Базовая система | Linux kernel + firmware | `base base-devel linux linux-headers` |
| Рабочий стол | GNOME + GDM | `gnome gnome-tweaks gdm xorg-server` |
| Видеодрайвер | NVIDIA proprietary (GTX 1050 Ti) | `nvidia nvidia-utils nvidia-settings` |
| Сеть | NetworkManager + DNS | `networkmanager` |
| Разработка | Языки, компиляторы, инструменты | Python, Node.js, Rust, Go, GCC, Docker, QEMU |
| Микроконтроллеры | Udev-правила | Arduino, ESP32, STM32, RP2040 и др. |
| AUR | yay + авто-обновления | `yay-bin` + systemd timer |
| IDE | VS Code + Claude Code | `visual-studio-code-bin` + `@anthropic-ai/claude-code` |

## Требования

- **Запуск**: Arch Linux live-ISO (свежий, с archiso)
- **Архитектура**: x86_64
- **Видеокарта**: NVIDIA GeForce GTX 1050 Ti (Pascal)
- **ОЗУ**: минимум 2 GiB (рекомендуется 4+ GiB)
- **Диск**: минимум 10 GiB
- **Интернет**: обязателен (проводной или Wi-Fi)

## Подготовка USB

1. Скачайте [образ Arch Linux](https://archlinux.org/download/)
2. Запишите на USB:
   ```bash
   # Linux/macOS
   sudo dd if=archlinux-*.iso of=/dev/sdX bs=4M status=progress oflag=sync

   # Или используйте Ventoy / Rufus (Windows)
   ```
3. Загрузитесь с USB

## Загрузка с ISO и подключение к сети

```bash
# Раскладка клавиатуры
loadkeys us

# Wi-Fi (если нужен)
iwctl
[iwd]# device list
[iwd]# station wlan0 connect "SSID"
[iwd]# exit

# Проверка подключения
ping -c 3 archlinux.org
```

## Запуск установщика

```bash
pacman -Sy git --noconfirm
git clone https://github.com/lilux12/archinstalltema.git
cd archinstalltema
./install.sh
```

### Аргументы командной строки

```bash
# Демо-режим (без реальных команд, для просмотра UI)
./install.sh --demo

# Режим отладки
./install.sh --debug

# Английский интерфейс
./install.sh --lang en

# Прямой запуск через Python
python -m arch_installer --demo
```

## Интерфейс

### Wizard (пошаговая настройка)

Пошаговый мастер с 9 шагами:
1. Язык интерфейса (Русский / English)
2. Выбор диска
3. Подтверждение стирания диска
4. Имя пользователя
5. Пароль пользователя
6. Пароль root
7. Hostname
8. Часовой пояс
9. Сводка и подтверждение

### Экран установки (split-layout)

Два панели: журнал команд + прогресс. Обновляется 4 раза в секунду.

### Обработка ошибок

При ошибке — диалог с тремя вариантами:
- **[R] Повторить** — запустить этап заново
- **[S] Пропустить** — перейти к следующему (если этап допускает)
- **[A] Выйти** — прервать установку

## После установки

### Логи
```bash
# Лог установки сохраняется в систему
cat /var/log/arch_install.log
```

### Авто-обновления
Система настроена на еженедельные обновления (воскресенье 03:00):
```bash
# Проверить статус таймера
systemctl status system-update.timer

# Отключить авто-обновления
sudo systemctl disable system-update.timer
```

### Первые шаги
1. Войдите под своим пользователем в GDM
2. Откройте терминал
3. Запустите `neofetch` для проверки
4. VS Code доступен в меню приложений
5. Claude Code доступен из терминала: `claude`

## FAQ

### NVIDIA: чёрный экран после перезагрузки
Загрузитесь в TTY (Ctrl+Alt+F2) и проверьте:
```bash
lsmod | grep nvidia
journalctl -b -p err
```

### Нет звука
```bash
sudo pacman -S pipewire pipewire-pulse wireplumber
systemctl --user enable pipewire pipewire-pulse wireplumber
```

### Wi-Fi не подключается
```bash
nmcli device wifi list
nmcli device wifi connect "SSID" password "PASS"
```

## Для разработчиков

### Демо-режим
```bash
# Запуск UI без реальных команд
python -m arch_installer --demo
```

### Тесты
```bash
pip install pytest
pytest tests/
```

### Проверка кода
```bash
pip install ruff mypy
ruff check arch_installer/
mypy --strict arch_installer/
```

### Структура проекта
```
arch_installer/
├── __main__.py      # CLI точка входа
├── main.py          # Оркестратор
├── config.py        # InstallConfig dataclass
├── constants.py     # Версии, пакеты, пути
├── exceptions.py    # Кастомные исключения
├── i18n.py          # Переводы RU/EN
├── ui/              # TUI-компоненты
│   ├── theme.py     # Цвета и стили
│   ├── banner.py    # ASCII-баннер
│   ├── wizard.py    # Пошаговый мастер
│   ├── progress.py  # Split-layout прогресс
│   ├── summary.py   # Финальный экран
│   └── error_screen.py
├── stages/          # Этапы установки
│   ├── base_stage.py
│   ├── preflight.py → finalize.py
│   └── ...
└── utils/           # Утилиты
    ├── shell.py     # Запуск команд
    ├── chroot.py    # arch-chroot
    ├── logger.py    # Логирование
    ├── validators.py
    └── system_info.py
```

## Лицензия

MIT — см. [LICENSE](LICENSE)
