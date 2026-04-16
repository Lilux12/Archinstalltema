# Промт для Claude Code: Персональный TUI-установщик Arch Linux

## Задача

Создай красивый многофайловый TUI-установщик Arch Linux на Python 3.11+ с интерфейсом в стиле `archinstall`, но с авторским дизайном. Установщик запускается из официального Arch Linux live-ISO и полностью автоматизирует установку персональной системы для разработки (GNOME + NVIDIA GTX 1050 Ti + инструменты разработчика + поддержка микроконтроллеров).

---

## Целевое окружение

- **Запуск**: официальный Arch Linux live-ISO (свежий, с archiso)
- **Права**: root (в live-ISO по умолчанию)
- **Архитектура**: x86_64
- **Железо**: ПК с NVIDIA GeForce GTX 1050 Ti (Pascal, GP107)
- **Интернет**: обязателен (проводной или Wi-Fi через `iwctl`)

---

## Структура проекта

```
arch-installer/
├── README.md                          # Подробная инструкция
├── LICENSE                            # MIT
├── install.sh                         # Bootstrap для live-ISO
├── requirements.txt                   # Python-зависимости
├── pyproject.toml                     # Метаданные пакета
├── .gitignore
├── arch_installer/
│   ├── __init__.py
│   ├── __main__.py                   # python -m arch_installer
│   ├── main.py                       # Оркестратор
│   ├── config.py                     # dataclass InstallConfig
│   ├── constants.py                  # Версии, пути, константы
│   ├── exceptions.py                 # Кастомные исключения
│   ├── i18n.py                       # Переводы RU/EN
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── theme.py                  # Цвета, символы, стили
│   │   ├── banner.py                 # ASCII-баннер Arch
│   │   ├── wizard.py                 # Диалоги выбора
│   │   ├── progress.py               # Split-layout: лог + прогресс
│   │   ├── summary.py                # Экран сводки
│   │   └── error_screen.py           # Экран ошибки с retry/skip/abort
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── base_stage.py             # Абстрактный класс Stage
│   │   ├── preflight.py              # Проверки окружения
│   │   ├── disk.py                   # Разметка и ФС
│   │   ├── base_install.py           # pacstrap + fstab
│   │   ├── system_config.py          # Локаль, hostname, users, sudo
│   │   ├── bootloader.py             # GRUB
│   │   ├── multilib.py               # Multilib-репо
│   │   ├── gnome.py                  # GNOME + GDM
│   │   ├── nvidia.py                 # Драйвер NVIDIA
│   │   ├── network.py                # NetworkManager + DNS
│   │   ├── dev_tools.py              # Инструменты разработки
│   │   ├── udev_rules.py             # Правила микроконтроллеров
│   │   ├── aur.py                    # yay + авто-обновления
│   │   ├── vscode_claude.py          # VS Code + Claude Code
│   │   └── finalize.py               # umount + reboot
│   └── utils/
│       ├── __init__.py
│       ├── shell.py                  # Запуск команд с стримингом
│       ├── chroot.py                 # arch-chroot helpers
│       ├── logger.py                 # Логирование
│       ├── validators.py             # Валидация ввода
│       └── system_info.py            # Инфо о железе
├── assets/
│   ├── udev/
│   │   └── 99-microcontrollers.rules
│   ├── pacman/
│   │   └── nvidia.hook
│   └── systemd/
│       ├── system-update.service
│       └── system-update.timer
└── tests/
    ├── __init__.py
    ├── test_validators.py
    ├── test_config.py
    └── test_ui_demo.py               # Демо-режим для просмотра UI без реальной установки
```

---

## Спецификация UI

### Общий стиль
- **Библиотеки**: `rich` (основа), опционально `textual` для сложных диалогов
- **Акцентный цвет**: `#1793D1` (голубой Arch Linux)
- **Успех**: `#00FF87` (яркий зелёный)
- **Предупреждение**: `#FFAF00` (янтарный)
- **Ошибка**: `#FF0055` (красно-розовый)
- **Фон**: тёмный, текст светлый
- **Рамки**: `box.DOUBLE` для главных панелей, `box.ROUNDED` для вложенных
- **Символы**: `✓` `✗` `⚠` `►` `◆` `●`

### Стартовый экран
ASCII-баннер Arch Linux (большая буква "A" из блоков), под ней:
```
        ╔══════════════════════════════════════════════════╗
        ║   Arch Installer — Персональная сборка           ║
        ║   v1.0.0  │  GNOME + NVIDIA + Dev Environment    ║
        ╚══════════════════════════════════════════════════╝

                  [ Нажмите ENTER чтобы начать ]
```

### Экран Wizard (каждый шаг)
В шапке: `Шаг 3 из 8  •  Выбор диска`
Прогресс wizard-а: `●●●○○○○○` (закрашенные/пустые круги)
Внизу подсказка: `[Enter] Далее  •  [Esc] Назад  •  [Ctrl+C] Выход`

### ГЛАВНЫЙ ЭКРАН УСТАНОВКИ (split-layout)

Использовать `rich.live.Live` + `rich.layout.Layout`. Две панели:

```
┌─ Журнал команд ──────────────────────────────────── 72% ─┐
│                                                            │
│  ► Этап 4: Установка базовой системы                       │
│                                                            │
│  $ timedatectl set-ntp true                                │
│  ✓ NTP синхронизация включена                              │
│                                                            │
│  $ reflector --country Russia,Germany --age 12 ...         │
│  ✓ Зеркала обновлены (15 шт.)                              │
│                                                            │
│  $ pacstrap -K /mnt base base-devel linux ...              │
│    :: Synchronizing package databases...                   │
│     core                     155.3 KiB   2.1 MiB/s         │
│     extra                      8.4 MiB   9.8 MiB/s         │
│    :: Installing packages...                               │
│     installing linux (6.x.x-arch1-1)                       │
│     installing linux-firmware (20260101-1)                 │
│     [скроллируется последние 20 строк]                     │
│                                                            │
├─ Прогресс ─────────────────────────────────────────── 28% ─┤
│                                                            │
│  Общий прогресс:  Этап 4 из 14                             │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  28%              │
│                                                            │
│  Текущий этап:   Установка базовой системы                 │
│  Операция:       Загрузка linux-firmware                   │
│  ██████████████████████░░░░░░░░░░  67%  (423/632 пакетов)  │
│                                                            │
│  ⏱  Прошло: 04:32    ⏳ Осталось ≈ 11:40                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Детали реализации**:
- Верхняя панель — scrollable console history (последние 20-25 строк)
- Команды выводятся как `$ команда`, результат — `✓ описание` или `✗ ошибка`
- Stdout pacman парсится регуляркой `installing (\S+) \((\S+)\)` для обновления "Текущей операции"
- Прогресс пакетов pacman — регулярка `Packages \((\d+)\)` и счётчик `\((\d+)/(\d+)\)`
- ETA считается как `прошедшее_время / done_ratio - прошедшее_время`
- Окно обновляется 4 раза в секунду (`refresh_per_second=4`)

### Экран ошибки
Красный фон, центрированная панель:
```
        ╔═══════════════════════════════════════════╗
        ║  ✗ ОШИБКА НА ЭТАПЕ: Установка GNOME       ║
        ╠═══════════════════════════════════════════╣
        ║                                            ║
        ║  error: failed to commit transaction       ║
        ║  (conflicting files: gnome-shell...)       ║
        ║                                            ║
        ║  Последние 10 строк лога:                  ║
        ║  [...]                                     ║
        ║                                            ║
        ╠═══════════════════════════════════════════╣
        ║  [R] Повторить  [S] Пропустить  [A] Выйти ║
        ╚═══════════════════════════════════════════╝
```

### Финальный экран
Зелёная рамка с галочкой, сводка:
```
        ✓ Установка завершена успешно

        Время установки:       23:47
        Установлено пакетов:   1247
        Размер системы:        8.3 GiB

        Система готова к использованию.
        Не забудьте вытащить установочный носитель.

        [ Перезагрузить сейчас ]  [ Выйти в shell ]
```

---

## Детальная спецификация этапов

### Этап 0: Preflight (stages/preflight.py)

Проверки перед началом:
1. Запуск от root (`os.geteuid() == 0`)
2. Arch live-ISO: наличие `/run/archiso/bootmnt` ИЛИ `/etc/arch-release` + проверка `uname -r` содержит `arch`
3. Интернет: `ping -c 1 -W 3 archlinux.org`
4. ОЗУ: минимум 2 GiB (предупреждение при <4 GiB)
5. Свободное место в tmpfs (live-ISO root): минимум 500 MiB
6. UEFI/BIOS: наличие `/sys/firmware/efi/efivars`
7. Проверка доступности pacman-mirrors

Всё записывается в `SystemInfo` dataclass и передаётся в `InstallConfig`.

При любой критической проблеме — показать понятное сообщение и выйти.

### Этап 1: Wizard (ui/wizard.py)

Последовательность:
1. **Язык интерфейса** — радио-кнопки: `Русский` / `English`. Все дальнейшие тексты через `i18n.t()`.
2. **Диск для установки** — таблица со столбцами:
   ```
   ╭──┬─────────┬────────┬──────────────────────┬──────╮
   │# │ Device  │ Size   │ Model                │ Type │
   ├──┼─────────┼────────┼──────────────────────┼──────┤
   │1 │ /dev/sda│ 500 GB │ Samsung SSD 870 EVO  │ SSD  │
   │2 │ /dev/sdb│ 2.0 TB │ WDC WD20EZBX         │ HDD  │
   ╰──┴─────────┴────────┴──────────────────────┴──────╯
   ```
   Фильтр: исключить `loop`, `rom`, устройства размером < 10 GiB, сам ISO-носитель.

3. **Страшное предупреждение**:
   ```
   ⚠⚠⚠ ВНИМАНИЕ ⚠⚠⚠

   Диск /dev/sda (Samsung SSD 870 EVO, 500 GB) будет ПОЛНОСТЬЮ СТЁРТ.
   Все данные будут безвозвратно потеряны.

   Для подтверждения введите слово YES (заглавными буквами):
   > _
   ```

4. **Имя пользователя** — валидация `^[a-z_][a-z0-9_-]{0,31}$`, запрещены: `root`, `daemon`, `bin`, `sys`, `nobody`.
5. **Пароль пользователя** — два раза, скрытый ввод, минимум 6 символов, проверка совпадения. Предупреждение если слабый (словарный).
6. **Пароль root** — аналогично, обязательно отличается от пользовательского (предупреждение).
7. **Hostname** — по умолчанию `archlinux`, валидация RFC 1123.
8. **Часовой пояс** — по умолчанию `Europe/Moscow`, с возможностью выбора из списка через fuzzy search.
9. **Сводка и финальное подтверждение**:
   ```
   ┌─ Параметры установки ──────────────────────────┐
   │                                                 │
   │  Язык:           Русский                        │
   │  Диск:           /dev/sda (500 GB)              │
   │  Разметка:       UEFI / GPT / ext4              │
   │  Часовой пояс:   Europe/Moscow                  │
   │  Hostname:       archlinux                      │
   │  Пользователь:   ivan                           │
   │  Пароль:         ••••••••                       │
   │  Root пароль:    ••••••••                       │
   │                                                 │
   │  Рабочее окружение:  GNOME                      │
   │  Видеодрайвер:       NVIDIA proprietary         │
   │  Доп. возможности:   Multilib, Dev tools,       │
   │                      AUR (yay), udev rules,     │
   │                      авто-обновления            │
   │                                                 │
   └─────────────────────────────────────────────────┘

         [ Начать установку ]    [ Отмена ]
   ```

### Этап 2: Разметка диска (stages/disk.py)

**UEFI путь** (GPT):
```bash
sgdisk --zap-all /dev/sdX
sgdisk -n 1:0:+1GiB -t 1:ef00 -c 1:"EFI" /dev/sdX
sgdisk -n 2:0:0     -t 2:8300 -c 2:"root" /dev/sdX
mkfs.fat -F32 -n EFI /dev/sdX1
mkfs.ext4 -L root /dev/sdX2
mount /dev/sdX2 /mnt
mount --mkdir /dev/sdX1 /mnt/boot
```

**BIOS путь** (MBR):
```bash
parted -s /dev/sdX mklabel msdos
parted -s /dev/sdX mkpart primary ext4 1MiB 100%
parted -s /dev/sdX set 1 boot on
mkfs.ext4 -L root /dev/sdX1
mount /dev/sdX1 /mnt
```

Каждая команда логируется в UI. После — `lsblk /dev/sdX` для визуального подтверждения.

### Этап 3: Базовая установка (stages/base_install.py)

```bash
timedatectl set-ntp true
pacman -Sy --noconfirm reflector
reflector --country Russia,Germany,Netherlands,Finland \
          --age 12 --protocol https --sort rate \
          --save /etc/pacman.d/mirrorlist

pacstrap -K /mnt \
    base base-devel \
    linux linux-firmware linux-headers \
    networkmanager \
    nano vim sudo git \
    man-db man-pages texinfo

genfstab -U /mnt >> /mnt/etc/fstab
```

Прогресс pacstrap стримится в UI с парсингом.

### Этап 4: Системная конфигурация (stages/system_config.py)

Все команды через `arch-chroot /mnt`:

```bash
# Timezone
ln -sf /usr/share/zoneinfo/$TIMEZONE /etc/localtime
hwclock --systohc

# Локали
sed -i 's/^#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
sed -i 's/^#ru_RU.UTF-8/ru_RU.UTF-8/' /etc/locale.gen
locale-gen
echo "LANG=$CHOSEN_LOCALE" > /etc/locale.conf

# Keyboard
echo "KEYMAP=us" > /etc/vconsole.conf

# Hostname
echo "$HOSTNAME" > /etc/hostname
cat > /etc/hosts <<EOF
127.0.0.1   localhost
::1         localhost
127.0.1.1   $HOSTNAME.localdomain $HOSTNAME
EOF

# Пароль root
echo "root:$ROOT_PASSWORD" | chpasswd

# Пользователь с нужными группами
useradd -m \
    -G wheel,video,audio,input,storage,optical,network,uucp \
    -s /bin/bash "$USERNAME"
echo "$USERNAME:$USER_PASSWORD" | chpasswd

# Создаём группу plugdev
groupadd -f plugdev
usermod -aG plugdev "$USERNAME"

# Sudo с NOPASSWD только для pacman/yay
cat > /etc/sudoers.d/10-wheel <<EOF
%wheel ALL=(ALL:ALL) ALL
EOF
cat > /etc/sudoers.d/20-pacman-nopasswd <<EOF
%wheel ALL=(ALL) NOPASSWD: /usr/bin/pacman, /usr/bin/yay
EOF
chmod 440 /etc/sudoers.d/10-wheel
chmod 440 /etc/sudoers.d/20-pacman-nopasswd
visudo -c  # проверка синтаксиса

systemctl enable NetworkManager
```

### Этап 5: Bootloader (stages/bootloader.py)

**UEFI**:
```bash
pacman -S --noconfirm grub efibootmgr os-prober
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
```

**BIOS**:
```bash
pacman -S --noconfirm grub os-prober
grub-install --target=i386-pc /dev/sdX
grub-mkconfig -o /boot/grub/grub.cfg
```

### Этап 6: Multilib (stages/multilib.py)

**Важно: выполнять ДО установки NVIDIA, GNOME и dev-tools** (чтобы lib32-пакеты были доступны).

```bash
# Раскомментировать [multilib] в /etc/pacman.conf
sed -i '/^#\[multilib\]/,/^#Include/ { s/^#// }' /etc/pacman.conf
pacman -Syy
```

### Этап 7: GNOME (stages/gnome.py)

Стандартная тема, без кастомизаций:
```bash
pacman -S --noconfirm \
    xorg-server xorg-xinit \
    gnome gnome-tweaks gnome-shell-extensions \
    gdm \
    gnome-terminal nautilus gnome-text-editor

systemctl enable gdm
```

### Этап 8: NVIDIA (stages/nvidia.py)

**КРИТИЧНО**: для GTX 1050 Ti (Pascal/GP107) нужен именно `nvidia` из official repo. НЕ `nvidia-open` (это только для Turing RTX 20xx+), НЕ `nvidia-470xx` (это для ещё более старых карт). Никаких AUR-архивов.

```bash
pacman -S --noconfirm \
    nvidia nvidia-utils nvidia-settings \
    lib32-nvidia-utils \
    opencl-nvidia lib32-opencl-nvidia
```

Модули в `/etc/mkinitcpio.conf`:
```
MODULES=(nvidia nvidia_modeset nvidia_uvm nvidia_drm)
```
Убрать `kms` из `HOOKS`.

`/etc/modprobe.d/nvidia.conf`:
```
options nvidia_drm modeset=1
options nvidia NVreg_PreserveVideoMemoryAllocations=1
```

`/etc/modprobe.d/blacklist-nouveau.conf`:
```
blacklist nouveau
options nouveau modeset=0
```

Pacman hook `/etc/pacman.d/hooks/nvidia.hook` (копировать из `assets/pacman/nvidia.hook`):
```ini
[Trigger]
Operation=Install
Operation=Upgrade
Operation=Remove
Type=Package
Target=nvidia
Target=linux

[Action]
Description=Update NVIDIA module in initcpio
Depends=mkinitcpio
When=PostTransaction
NeedsTargets
Exec=/bin/sh -c 'while read -r trg; do case $trg in linux) exit 0; esac; done; /usr/bin/mkinitcpio -P'
```

Затем: `mkinitcpio -P`.

### Этап 9: Сеть и DNS (stages/network.py)

```bash
mkdir -p /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/dns-servers.conf <<'EOF'
[global-dns-domain-*]
servers=111.88.96.50,111.88.96.51,2a00:ab00:1233:26::50,2a00:ab00:1233:26::51
EOF

# Отключить systemd-resolved чтобы не конфликтовал
systemctl disable systemd-resolved 2>/dev/null || true
systemctl mask systemd-resolved 2>/dev/null || true

# /etc/resolv.conf — пусть управляет NetworkManager
rm -f /etc/resolv.conf
ln -sf /run/NetworkManager/resolv.conf /etc/resolv.conf
```

### Этап 10: Инструменты разработки (stages/dev_tools.py)

```bash
pacman -S --noconfirm \
    git \
    python python-pip python-virtualenv python-pipx \
    nodejs npm \
    gcc clang lld make cmake ninja meson \
    gdb lldb strace ltrace valgrind \
    nasm yasm \
    qemu-full qemu-user-static \
    virt-manager libvirt edk2-ovmf \
    dnsmasq bridge-utils iptables-nft \
    rust cargo \
    go \
    docker docker-compose docker-buildx \
    wget curl htop btop neofetch \
    unzip p7zip tar \
    openssh

systemctl enable libvirtd
systemctl enable docker

usermod -aG libvirt,docker,kvm,uucp,tty "$USERNAME"
```

### Этап 11: Udev-правила для микроконтроллеров (stages/udev_rules.py)

Скопировать `assets/udev/99-microcontrollers.rules` в `/mnt/etc/udev/rules.d/99-microcontrollers.rules`.

**Содержимое файла**:
```
# ═══════════════════════════════════════════════════════════════
#  Доступ к микроконтроллерам и программаторам без sudo
#  Пользователь должен быть в группах: uucp, plugdev
# ═══════════════════════════════════════════════════════════════

# ── USB-UART мосты ──────────────────────────────────────────────

# Silicon Labs CP210x (ESP32 DevKit, многие ESP8266)
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="uucp", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea70", MODE="0666", GROUP="uucp", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea71", MODE="0666", GROUP="uucp", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea80", MODE="0666", GROUP="uucp", TAG+="uaccess"

# WCH CH340/CH341 (дешёвые клоны Arduino Nano, многие ESP32 DevKit)
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", MODE="0666", GROUP="uucp", TAG+="uaccess"

# FTDI (FT232, FT2232, FT4232, FT232H)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", MODE="0666", GROUP="uucp", TAG+="uaccess"

# Prolific PL2303
SUBSYSTEM=="usb", ATTRS{idVendor}=="067b", MODE="0666", GROUP="uucp", TAG+="uaccess"

# ── Платформы разработки ────────────────────────────────────────

# Arduino (Uno, Mega, Leonardo, Micro, Nano, Due, Zero, MKR)
SUBSYSTEM=="usb", ATTRS{idVendor}=="2341", MODE="0666", GROUP="uucp", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="2a03", MODE="0666", GROUP="uucp", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1b4f", MODE="0666", GROUP="uucp", TAG+="uaccess"

# Espressif официальные VID (ESP32-S2/S3/C3 с нативным USB)
SUBSYSTEM=="usb", ATTRS{idVendor}=="303a", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Raspberry Pi Pico и RP2040 (BOOTSEL и runtime)
SUBSYSTEM=="usb", ATTRS{idVendor}=="2e8a", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# STM32 (BOOT0, DFU, Virtual COM, ST-Link V1/V2/V2-1/V3)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Atmel / Microchip (AVRISP mkII, AVR Dragon, SAM-BA и т.д.)
SUBSYSTEM=="usb", ATTRS{idVendor}=="03eb", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# V-USB / Objective Development (USBasp, USBtinyISP и подобные)
SUBSYSTEM=="usb", ATTRS{idVendor}=="16c0", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# NXP / Freescale (LPC, Kinetis, i.MX RT — Teensy, MIMXRT)
SUBSYSTEM=="usb", ATTRS{idVendor}=="1fc9", MODE="0666", GROUP="plugdev", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="15a2", MODE="0666", GROUP="plugdev", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0d28", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Nordic Semiconductor (nRF51/nRF52/nRF53 DK, J-Link on-board)
SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Texas Instruments (MSP430, CC2xxx, Launchpad)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0451", MODE="0666", GROUP="plugdev", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="2047", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Cypress / Infineon (PSoC)
SUBSYSTEM=="usb", ATTRS{idVendor}=="04b4", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Renesas (Synergy, RA, RX)
SUBSYSTEM=="usb", ATTRS{idVendor}=="045b", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# ── Программаторы и отладчики ───────────────────────────────────

# SEGGER J-Link (все модели)
SUBSYSTEM=="usb", ATTRS{idVendor}=="1366", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# OpenMoko / CMSIS-DAP / DAPLink / Black Magic Probe
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d50", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# PicKit (Microchip)
SUBSYSTEM=="usb", ATTRS{idVendor}=="04d8", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Bus Pirate, Saleae Logic (FTDI-based обрабатывается выше)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0925", ATTRS{idProduct}=="3881", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Altera / Intel FPGA USB Blaster I/II
SUBSYSTEM=="usb", ATTRS{idVendor}=="09fb", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Xilinx Platform Cable USB
SUBSYSTEM=="usb", ATTRS{idVendor}=="03fd", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Lattice FPGA (HW-USBN-2B, iCEstick)
SUBSYSTEM=="usb", ATTRS{idVendor}=="1443", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# ── Serial-устройства в /dev ────────────────────────────────────

KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="uucp", TAG+="uaccess"
KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="uucp", TAG+="uaccess"
KERNEL=="ttyS[0-9]*",   MODE="0666", GROUP="uucp", TAG+="uaccess"

# HID для отладчиков с HID-интерфейсом (CMSIS-DAP, DAPLink)
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666", GROUP="plugdev", TAG+="uaccess"
```

После копирования (в chroot):
```bash
groupadd -f plugdev
udevadm control --reload-rules  # не сработает в chroot, но применится после reboot
```

### Этап 12: AUR helper + авто-обновления (stages/aur.py)

```bash
# Установка yay от имени пользователя
arch-chroot /mnt sudo -u "$USERNAME" bash <<'EOF'
cd /tmp
git clone https://aur.archlinux.org/yay-bin.git
cd yay-bin
makepkg -si --noconfirm
cd /
rm -rf /tmp/yay-bin
EOF
```

Копировать `assets/systemd/system-update.service` и `system-update.timer` в `/mnt/etc/systemd/system/`.

**system-update.service**:
```ini
[Unit]
Description=Weekly full system update (pacman + AUR)
After=network-online.target
Wants=network-online.target
ConditionACPower=true

[Service]
Type=oneshot
User=USERNAME_PLACEHOLDER
ExecStart=/usr/bin/yay -Syu --noconfirm --devel --answerclean All --answerdiff None
StandardOutput=journal
StandardError=journal
TimeoutStartSec=2h

[Install]
WantedBy=multi-user.target
```
(В скрипте заменить `USERNAME_PLACEHOLDER` на реальное имя через `sed`.)

**system-update.timer**:
```ini
[Unit]
Description=Run system update weekly

[Timer]
OnCalendar=Sun 03:00
Persistent=true
RandomizedDelaySec=2h

[Install]
WantedBy=timers.target
```

Затем:
```bash
arch-chroot /mnt systemctl enable system-update.timer
```

### Этап 13: VS Code + Claude Code (stages/vscode_claude.py)

```bash
# VS Code из AUR (официальная бинарная сборка Microsoft)
arch-chroot /mnt sudo -u "$USERNAME" yay -S --noconfirm visual-studio-code-bin

# Настройка npm prefix для установки глобальных пакетов без sudo
arch-chroot /mnt sudo -u "$USERNAME" bash <<'EOF'
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
grep -qxF 'export PATH=$HOME/.npm-global/bin:$PATH' ~/.bashrc \
    || echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
export PATH=$HOME/.npm-global/bin:$PATH
npm install -g @anthropic-ai/claude-code
EOF
```

### Этап 14: Финализация (stages/finalize.py)

```bash
# Сохранить лог в систему для диагностики
cp /tmp/arch_install.log /mnt/var/log/arch_install.log

# Размонтировать
umount -R /mnt

# Показать красивый финальный экран с статистикой:
# - Общее время установки
# - Количество установленных пакетов (pacman -Q | wc -l в chroot — нужно сделать ДО umount)
# - Размер занятого места
```

Диалог `[Перезагрузить сейчас] [Выйти в shell]`. При выборе перезагрузки — `reboot`.

---

## Требования к коду

### Архитектура

1. **Абстрактный класс `BaseStage`** в `stages/base_stage.py`:
   ```python
   from abc import ABC, abstractmethod
   from ..config import InstallConfig

   class BaseStage(ABC):
       name: str
       weight: int = 1  # для расчёта общего прогресса

       def __init__(self, config: InstallConfig, ui: ProgressUI):
           self.config = config
           self.ui = ui

       @abstractmethod
       def run(self) -> None: ...

       def rollback(self) -> None:
           """Опциональный откат при ошибке"""
           pass
   ```

2. **`InstallConfig` dataclass** с валидацией через `__post_init__`.

3. **`shell.run()`** — единая точка запуска команд:
   ```python
   def run(
       cmd: list[str] | str,
       *,
       chroot: bool = False,
       stream_to_ui: bool = True,
       check: bool = True,
       env: dict | None = None,
       input_data: str | None = None,
   ) -> subprocess.CompletedProcess:
       ...
   ```
   - Логирует `$ команда` в UI и файл
   - Стримит stdout/stderr построчно
   - Парсит прогресс pacman
   - При `check=True` бросает `StageError` с информативным сообщением

### Обработка ошибок

- Кастомные исключения: `PreflightError`, `StageError`, `ValidationError`, `UserAbort`
- На каждом `stage.run()` — try/except в `main.py`, показ `ErrorScreen` с опциями:
  - `[R]` Повторить шаг (вызвать `run()` ещё раз)
  - `[S]` Пропустить (если `stage.skippable == True`)
  - `[A]` Прервать установку (выход с кодом 1)
- Все ошибки пишутся с полным traceback в `/tmp/arch_install.log`

### Логирование

`utils/logger.py`:
- Два handler'а: FileHandler (`/tmp/arch_install.log`, уровень DEBUG) и UIHandler (в верхнюю панель TUI, уровень INFO)
- Формат файла: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Формат UI: только текст с подсветкой через rich

### Идемпотентность

Перед каждым действием — проверка:
- Монтирование: `if not os.path.ismount('/mnt'): mount(...)`
- Создание файлов: если уже есть — пропустить или перезаписать по стратегии
- Установка пакетов: `pacman -Qi $pkg` → если установлен, не переустанавливать
- Группы: `groupadd -f` всегда

### Демо-режим

`python -m arch_installer --demo` — запускает UI без реальных команд:
- Wizard работает как обычно
- Install-экран проигрывает запись "fake install" из JSON-файла
- Полезно для тестирования UI и скриншотов

### i18n

`i18n.py`:
```python
TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        "welcome.title": "Arch Installer — Персональная сборка",
        "wizard.step": "Шаг {current} из {total}",
        # ...
    },
    "en": {
        "welcome.title": "Arch Installer — Personal Build",
        # ...
    },
}

_current_lang = "ru"

def set_lang(lang: str) -> None:
    global _current_lang
    _current_lang = lang

def t(key: str, **kwargs) -> str:
    return TRANSLATIONS[_current_lang][key].format(**kwargs)
```

### Type hints и качество

- `mypy --strict` должен проходить
- `ruff check` без ошибок (настроить `pyproject.toml`)
- Все публичные функции — с docstring на русском
- Комментарии в коде — на русском

### Тесты

`tests/`:
- `test_validators.py` — валидация username, hostname, password
- `test_config.py` — проверка `InstallConfig` и его `__post_init__`
- `test_ui_demo.py` — smoke-тест что demo-режим не падает

Запуск: `pytest tests/`.

---

## Файл install.sh (bootstrap)

```bash
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
    pip install --break-system-packages textual
fi

echo "==> Запуск установщика..."
cd "$(dirname "$0")"
exec python -m arch_installer "$@"
```

---

## README.md (содержание)

1. **Заголовок** с бейджами и кратким описанием
2. **Скриншоты** (ASCII-арт превью TUI)
3. **Что ставится** — таблица по этапам
4. **Требования к железу**
5. **Подготовка USB** (dd / Rufus / Ventoy)
6. **Загрузка с ISO и подключение к сети**:
   ```
   # Раскладка
   loadkeys us

   # Wi-Fi
   iwctl
   [iwd]# device list
   [iwd]# station wlan0 connect "SSID"
   [iwd]# exit

   # Проверка
   ping archlinux.org
   ```
7. **Запуск установщика**:
   ```
   pacman -Sy git --noconfirm
   git clone https://github.com/USER/arch-installer.git
   cd arch-installer
   ./install.sh
   ```
8. **После установки** — что делать дальше, где логи, как отключить авто-обновления
9. **FAQ и известные проблемы**
10. **Для разработчиков** — как запустить демо-режим, тесты, contributing

---

## Порядок разработки (для Claude Code)

Делай строго последовательно, после каждого крупного блока показывай краткое резюме:

1. Создай структуру директорий и пустые `__init__.py`
2. Напиши `pyproject.toml`, `requirements.txt`, `.gitignore`, `LICENSE`
3. Напиши **README.md** с полной инструкцией
4. Напиши `utils/` — фундамент (logger, shell, validators, chroot, system_info)
5. Напиши `exceptions.py`, `constants.py`, `config.py`, `i18n.py`
6. Напиши `ui/theme.py` и `ui/banner.py`
7. Напиши `ui/wizard.py` — все диалоги
8. Напиши `ui/progress.py` — **САМОЕ ВАЖНОЕ**, split-layout с live-обновлением. Обязательно реализуй демо-режим с фейковой установкой.
9. Напиши `ui/summary.py` и `ui/error_screen.py`
10. Напиши `stages/base_stage.py`
11. Напиши все stages по порядку (preflight → finalize)
12. Напиши `main.py` — оркестратор, с правильной обработкой ошибок и передачей UI-объекта во все stages
13. Напиши `__main__.py` с CLI-аргументами (`--demo`, `--debug`, `--lang`)
14. Создай все файлы в `assets/`
15. Напиши `install.sh`
16. Напиши тесты в `tests/`
17. Запусти `ruff check` и `mypy --strict`, исправь ошибки
18. Запусти демо-режим, убедись что UI работает
19. Покажи финальное дерево проекта через `tree -I '__pycache__'`
20. Дай краткую инструкцию "как запустить на реальном железе"

**Важно**:
- Пиши понятный, читаемый код с осмысленными именами
- Каждый модуль должен быть самодостаточен
- Не используй `os.system` — только `subprocess.run` / `subprocess.Popen`
- Все пути — через `pathlib.Path`
- Не хардкодь пароли, пути диска, имена — всё через `InstallConfig`
- Обязательно реализуй корректный `signal` handler для `Ctrl+C` (красивый выход с откатом монтирования)

Начинай.
