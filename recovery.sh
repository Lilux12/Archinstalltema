#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Arch Linux Recovery Script — проверка и доустановка компонентов
#  Использует AI (OpenRouter) для автоматического исправления ошибок
# ═══════════════════════════════════════════════════════════════
set -o pipefail

# ── Настройки ──────────────────────────────────────────────────
OPENROUTER_KEY="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"
AI_MODEL="nvidia/nemotron-3-super-120b-a12b:free"
LOG_FILE="/var/log/arch_recovery.log"
MAX_AI_RETRIES=3

# Цвета
RED='\033[0;91m'
GREEN='\033[0;92m'
YELLOW='\033[0;93m'
BLUE='\033[0;94m'
CYAN='\033[0;96m'
NC='\033[0m'
BOLD='\033[1m'

# ── Логирование ────────────────────────────────────────────────
log() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
ok()  { echo -e "${GREEN}[  OK]${NC} $1" | tee -a "$LOG_FILE"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
err() { echo -e "${RED}[ ERR]${NC} $1" | tee -a "$LOG_FILE"; }
header() { echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n" | tee -a "$LOG_FILE"; }

# ── Проверка root ──────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    err "Запустите от root: sudo bash $0"
    exit 1
fi

# Определяем имя пользователя (не root)
REAL_USER=$(ls /home/ | head -1)
if [ -z "$REAL_USER" ]; then
    err "Не найден пользователь в /home/"
    read -rp "Введите имя пользователя: " REAL_USER
fi

: > "$LOG_FILE" 2>/dev/null || LOG_FILE="/tmp/arch_recovery_$$.log"
header "Arch Linux Recovery — проверка и доустановка"
log "Пользователь: $REAL_USER"
log "Лог: $LOG_FILE"

# ── AI функция ─────────────────────────────────────────────────
ask_ai() {
    local question="$1"
    local response

    response=$(curl -s --max-time 30 -X POST "https://openrouter.ai/api/v1/chat/completions" \
        -H "Authorization: Bearer $OPENROUTER_KEY" \
        -H "Content-Type: application/json" \
        -d "$(cat <<JSONEOF
{
    "model": "$AI_MODEL",
    "messages": [
        {
            "role": "system",
            "content": "You are an Arch Linux expert. Answer ONLY with the exact bash command(s) to fix the problem. No explanations, no markdown, no code blocks. Just raw commands, one per line. If multiple commands needed, separate with newlines. If the package doesn't exist, suggest the closest alternative package name."
        },
        {
            "role": "user",
            "content": "$question"
        }
    ],
    "max_tokens": 300,
    "temperature": 0.1
}
JSONEOF
)" 2>/dev/null)

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['choices'][0]['message']['content'].strip())
except:
    print('')
" 2>/dev/null
}

# ── Установка пакета с AI-фиксом при ошибке ───────────────────
install_pkg() {
    local pkg="$1"
    local use_yay="$2"  # "yay" или "pacman"

    # Проверяем уже установлен ли
    if pacman -Qi "$pkg" &>/dev/null; then
        ok "$pkg уже установлен"
        return 0
    fi

    log "Установка $pkg..."

    local cmd
    local result
    if [ "$use_yay" = "yay" ]; then
        cmd="sudo -u $REAL_USER yay -S --noconfirm --needed $pkg"
    else
        cmd="pacman -S --noconfirm --needed $pkg"
    fi

    result=$(eval "$cmd" 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        ok "$pkg установлен"
        return 0
    fi

    # Ошибка — спрашиваем AI
    warn "$pkg не удалось установить, спрашиваем AI..."
    echo "$result" >> "$LOG_FILE"

    local ai_retry=0
    while [ $ai_retry -lt $MAX_AI_RETRIES ]; do
        ai_retry=$((ai_retry + 1))
        log "AI попытка $ai_retry/$MAX_AI_RETRIES для $pkg"

        local error_short
        error_short=$(echo "$result" | tail -5)
        local ai_fix
        ai_fix=$(ask_ai "Arch Linux pacman error installing package '$pkg': $error_short. What is the correct package name or fix command?")

        if [ -z "$ai_fix" ]; then
            warn "AI не ответил, пропускаем $pkg"
            return 1
        fi

        log "AI предлагает: $ai_fix"

        # Выполняем команду от AI (построчно)
        while IFS= read -r ai_cmd; do
            # Пропускаем пустые строки и комментарии
            [ -z "$ai_cmd" ] && continue
            [[ "$ai_cmd" =~ ^# ]] && continue
            # Убираем опасные команды
            [[ "$ai_cmd" =~ rm\ -rf\ / ]] && continue
            [[ "$ai_cmd" =~ mkfs ]] && continue
            [[ "$ai_cmd" =~ dd\ if= ]] && continue

            log "Выполняю: $ai_cmd"
            eval "$ai_cmd" >> "$LOG_FILE" 2>&1
            if [ $? -eq 0 ]; then
                ok "AI-фикс сработал: $ai_cmd"
                return 0
            fi
        done <<< "$ai_fix"
    done

    err "$pkg — не удалось установить даже с AI (пропуск)"
    return 1
}

# ── Установка группы пакетов ───────────────────────────────────
install_group() {
    local group_name="$1"
    local use_yay="$2"
    shift 2
    local packages=("$@")

    header "$group_name"

    local failed=0
    local installed=0
    local skipped=0

    for pkg in "${packages[@]}"; do
        if install_pkg "$pkg" "$use_yay"; then
            installed=$((installed + 1))
        else
            failed=$((failed + 1))
        fi
    done

    log "$group_name: установлено=$installed, ошибок=$failed"
}

# ── Включение сервиса ─────────────────────────────────────────
enable_svc() {
    local svc="$1"
    if systemctl is-enabled "$svc" &>/dev/null; then
        ok "Сервис $svc уже включён"
    else
        systemctl enable "$svc" 2>/dev/null
        ok "Сервис $svc включён"
    fi
}

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 1: Базовая система
# ═══════════════════════════════════════════════════════════════
install_group "Базовая система" "pacman" \
    base base-devel linux linux-firmware linux-headers \
    networkmanager nano vim sudo git man-db man-pages texinfo

enable_svc NetworkManager

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 2: Загрузчик GRUB
# ═══════════════════════════════════════════════════════════════
header "Загрузчик GRUB"
install_pkg "grub" "pacman"
install_pkg "os-prober" "pacman"
if [ -d /sys/firmware/efi/efivars ]; then
    install_pkg "efibootmgr" "pacman"
    if ! [ -f /boot/grub/grub.cfg ]; then
        log "Установка GRUB (UEFI)..."
        grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB 2>&1 | tee -a "$LOG_FILE"
        grub-mkconfig -o /boot/grub/grub.cfg 2>&1 | tee -a "$LOG_FILE"
        ok "GRUB установлен (UEFI)"
    else
        ok "GRUB уже настроен"
    fi
fi

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 3: Multilib
# ═══════════════════════════════════════════════════════════════
header "Multilib репозиторий"
if grep -q "^\[multilib\]" /etc/pacman.conf; then
    ok "[multilib] уже включён"
else
    log "Включаем [multilib]..."
    sed -i '/^#\[multilib\]/,/^#Include/ { s/^#// }' /etc/pacman.conf
    # Если sed не сработал — добавляем вручную
    if ! grep -q "^\[multilib\]" /etc/pacman.conf; then
        echo -e "\n[multilib]\nInclude = /etc/pacman.d/mirrorlist" >> /etc/pacman.conf
    fi
    pacman -Syy --noconfirm
    ok "[multilib] включён"
fi

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 4: GNOME
# ═══════════════════════════════════════════════════════════════
install_group "GNOME Desktop" "pacman" \
    xorg-server xorg-xinit \
    gnome gnome-tweaks gnome-shell-extensions \
    gdm gnome-terminal nautilus gnome-text-editor

enable_svc gdm

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 5: Сеть и DNS
# ═══════════════════════════════════════════════════════════════
header "Сеть и DNS"

# Конфигурация DNS для NetworkManager
NM_DNS_CONF="/etc/NetworkManager/conf.d/dns.conf"
if [ ! -f "$NM_DNS_CONF" ]; then
    mkdir -p /etc/NetworkManager/conf.d
    cat > "$NM_DNS_CONF" <<'DNSEOF'
# Пользовательские DNS-серверы
[global-dns-domain-*]
servers=111.88.96.50;111.88.96.51;2a00:ab00:1233:26::50;2a00:ab00:1233:26::51;
DNSEOF
    ok "DNS конфигурация создана"
else
    ok "DNS конфигурация уже есть"
fi

# systemd-resolved
systemctl disable systemd-resolved 2>/dev/null
systemctl mask systemd-resolved 2>/dev/null

# resolv.conf
if [ -L /etc/resolv.conf ] || [ ! -f /etc/resolv.conf ]; then
    rm -f /etc/resolv.conf
    cat > /etc/resolv.conf <<'RESOLVEOF'
# DNS-серверы (настроено установщиком)
nameserver 111.88.96.50
nameserver 111.88.96.51
nameserver 2a00:ab00:1233:26::50
nameserver 2a00:ab00:1233:26::51
RESOLVEOF
    ok "resolv.conf настроен"
fi

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 6: Инструменты разработки
# ═══════════════════════════════════════════════════════════════
install_group "Инструменты разработки" "pacman" \
    git python python-pip python-virtualenv python-pipx \
    nodejs npm rust cargo go \
    gcc clang lld make cmake ninja meson \
    gdb lldb strace ltrace valgrind \
    nasm yasm \
    qemu-full qemu-user-static \
    virt-manager libvirt edk2-ovmf dnsmasq iptables-nft \
    docker docker-compose docker-buildx \
    wget curl htop btop fastfetch \
    unzip p7zip tar openssh

enable_svc libvirtd
enable_svc docker

# Добавляем пользователя в группы
usermod -aG libvirt,docker,kvm,uucp,tty,plugdev "$REAL_USER" 2>/dev/null
ok "Пользователь $REAL_USER добавлен в группы dev"

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 7: Udev правила для микроконтроллеров
# ═══════════════════════════════════════════════════════════════
header "Udev правила"
UDEV_RULES="/etc/udev/rules.d/99-microcontrollers.rules"
if [ -f "$UDEV_RULES" ]; then
    ok "Udev правила уже установлены"
else
    # Скачиваем из репозитория
    curl -sL "https://raw.githubusercontent.com/Lilux12/Archinstalltema/main/assets/udev/99-microcontrollers.rules" \
        -o "$UDEV_RULES" 2>/dev/null
    if [ -f "$UDEV_RULES" ] && [ -s "$UDEV_RULES" ]; then
        ok "Udev правила установлены"
    else
        warn "Не удалось скачать udev правила"
    fi
fi
groupadd -f plugdev 2>/dev/null

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 8: AUR helper (yay)
# ═══════════════════════════════════════════════════════════════
header "AUR helper (yay)"
if command -v yay &>/dev/null; then
    ok "yay уже установлен"
else
    log "Установка yay..."
    sudo -u "$REAL_USER" bash -c '
        cd /tmp
        rm -rf yay-bin
        git clone https://aur.archlinux.org/yay-bin.git
        cd yay-bin
        makepkg -si --noconfirm
        cd /
        rm -rf /tmp/yay-bin
    ' 2>&1 | tee -a "$LOG_FILE"
    if command -v yay &>/dev/null; then
        ok "yay установлен"
    else
        err "yay не удалось установить"
    fi
fi

# Авто-обновления
TIMER_FILE="/etc/systemd/system/system-update.timer"
if [ ! -f "$TIMER_FILE" ]; then
    cat > /etc/systemd/system/system-update.service <<SVCEOF
[Unit]
Description=Weekly full system update (pacman + AUR)
After=network-online.target
Wants=network-online.target
ConditionACPower=true

[Service]
Type=oneshot
User=$REAL_USER
ExecStart=/usr/bin/yay -Syu --noconfirm --devel --answerclean All --answerdiff None
StandardOutput=journal
StandardError=journal
TimeoutStartSec=2h

[Install]
WantedBy=multi-user.target
SVCEOF

    cat > "$TIMER_FILE" <<'TIMEREOF'
[Unit]
Description=Run system update weekly

[Timer]
OnCalendar=Sun 03:00
Persistent=true
RandomizedDelaySec=2h

[Install]
WantedBy=timers.target
TIMEREOF

    systemctl enable system-update.timer 2>/dev/null
    ok "Авто-обновления настроены"
else
    ok "Авто-обновления уже настроены"
fi

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 9: NVIDIA драйвер (через yay)
# ═══════════════════════════════════════════════════════════════
header "NVIDIA драйвер (AUR)"

# Основные пакеты через yay
install_pkg "nvidia" "yay"
install_pkg "nvidia-utils" "yay"
install_pkg "nvidia-settings" "yay"
install_pkg "opencl-nvidia" "yay"
install_pkg "lib32-nvidia-utils" "yay"
install_pkg "lib32-opencl-nvidia" "yay"

# Настройка mkinitcpio
MKINIT="/etc/mkinitcpio.conf"
if grep -q "nvidia" "$MKINIT" 2>/dev/null; then
    ok "NVIDIA модули уже в mkinitcpio.conf"
else
    log "Настройка mkinitcpio.conf..."
    # Добавляем модули
    sed -i 's/^MODULES=(\(.*\))/MODULES=(\1 nvidia nvidia_modeset nvidia_uvm nvidia_drm)/' "$MKINIT"
    sed -i 's/( /(/g' "$MKINIT"
    # Удаляем kms
    sed -i 's/ kms / /g; s/ kms)/)/' "$MKINIT"
    ok "NVIDIA модули добавлены в mkinitcpio.conf"
fi

# modprobe
if [ ! -f /etc/modprobe.d/nvidia.conf ]; then
    cat > /etc/modprobe.d/nvidia.conf <<'NVIDIAEOF'
options nvidia_drm modeset=1
options nvidia_drm fbdev=1
options nvidia NVreg_PreserveVideoMemoryAllocations=1
NVIDIAEOF
    ok "modprobe nvidia.conf создан"
fi

if [ ! -f /etc/modprobe.d/blacklist-nouveau.conf ]; then
    cat > /etc/modprobe.d/blacklist-nouveau.conf <<'NOUVEAUEOF'
blacklist nouveau
options nouveau modeset=0
NOUVEAUEOF
    ok "nouveau заблокирован"
fi

# Pacman hook
mkdir -p /etc/pacman.d/hooks
HOOK_URL="https://raw.githubusercontent.com/Lilux12/Archinstalltema/main/assets/pacman/nvidia.hook"
if [ ! -f /etc/pacman.d/hooks/nvidia.hook ]; then
    curl -sL "$HOOK_URL" -o /etc/pacman.d/hooks/nvidia.hook 2>/dev/null
    ok "NVIDIA pacman hook установлен"
fi

# Пересборка initramfs
log "Пересборка initramfs..."
mkinitcpio -P 2>&1 | tee -a "$LOG_FILE"
ok "initramfs пересобран"

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 10: VS Code + Claude Code
# ═══════════════════════════════════════════════════════════════
header "VS Code + Claude Code"

install_pkg "visual-studio-code-bin" "yay"

# npm prefix для пользователя
sudo -u "$REAL_USER" bash -c '
    mkdir -p ~/.npm-global
    npm config set prefix ~/.npm-global 2>/dev/null
    grep -qxF "export PATH=\$HOME/.npm-global/bin:\$PATH" ~/.bashrc \
        || echo "export PATH=\$HOME/.npm-global/bin:\$PATH" >> ~/.bashrc
    export PATH=$HOME/.npm-global/bin:$PATH
    npm install -g @anthropic-ai/claude-code 2>/dev/null
' 2>&1 | tee -a "$LOG_FILE"
ok "VS Code + Claude Code настроены"

# ═══════════════════════════════════════════════════════════════
#  ПРОВЕРКА 11: Sudoers
# ═══════════════════════════════════════════════════════════════
header "Sudoers"

if [ ! -f /etc/sudoers.d/10-wheel ]; then
    echo "%wheel ALL=(ALL:ALL) ALL" > /etc/sudoers.d/10-wheel
    chmod 440 /etc/sudoers.d/10-wheel
    ok "sudoers wheel создан"
else
    ok "sudoers wheel уже есть"
fi

if [ ! -f /etc/sudoers.d/20-pacman-nopasswd ]; then
    echo "%wheel ALL=(ALL) NOPASSWD: /usr/bin/pacman, /usr/bin/yay" > /etc/sudoers.d/20-pacman-nopasswd
    chmod 440 /etc/sudoers.d/20-pacman-nopasswd
    ok "sudoers NOPASSWD создан"
else
    ok "sudoers NOPASSWD уже есть"
fi

visudo -c 2>&1 | tee -a "$LOG_FILE"

# ═══════════════════════════════════════════════════════════════
#  ИТОГОВЫЙ ОТЧЁТ
# ═══════════════════════════════════════════════════════════════
header "ИТОГОВЫЙ ОТЧЁТ"

echo ""
echo -e "${BOLD}Проверка установленных компонентов:${NC}"
echo ""

check_component() {
    local name="$1"
    local check_cmd="$2"

    if eval "$check_cmd" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $name"
    else
        echo -e "  ${RED}✗${NC} $name"
    fi
}

check_component "Linux kernel"          "pacman -Qi linux"
check_component "GRUB"                  "pacman -Qi grub"
check_component "NetworkManager"        "systemctl is-enabled NetworkManager"
check_component "GNOME"                 "pacman -Qi gnome-shell"
check_component "GDM"                   "systemctl is-enabled gdm"
check_component "NVIDIA driver"         "pacman -Qi nvidia || yay -Qi nvidia"
check_component "nvidia-utils"          "pacman -Qi nvidia-utils"
check_component "Docker"                "pacman -Qi docker"
check_component "libvirt"               "pacman -Qi libvirt"
check_component "Python"                "python --version"
check_component "Node.js"               "node --version"
check_component "Rust"                  "pacman -Qi rust"
check_component "Go"                    "pacman -Qi go"
check_component "GCC"                   "pacman -Qi gcc"
check_component "yay (AUR)"             "command -v yay"
check_component "VS Code"               "command -v code || yay -Qi visual-studio-code-bin"
check_component "Multilib"              "grep -q '^\[multilib\]' /etc/pacman.conf"
check_component "NVIDIA modprobe"       "test -f /etc/modprobe.d/nvidia.conf"
check_component "Nouveau blocked"       "test -f /etc/modprobe.d/blacklist-nouveau.conf"
check_component "Udev rules"            "test -f /etc/udev/rules.d/99-microcontrollers.rules"
check_component "Auto-update timer"     "systemctl is-enabled system-update.timer"

echo ""
echo -e "${BOLD}Пакетов установлено:${NC} $(pacman -Q | wc -l)"
echo -e "${BOLD}Лог:${NC} $LOG_FILE"
echo ""
echo -e "${GREEN}${BOLD}Готово! Перезагрузите систему: sudo reboot${NC}"
