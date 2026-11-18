#!/bin/bash
# Flameshot kurulum ve yapılandırma betiği
set -euo pipefail

# 1. Paket kontrolü ve kurulumu
if ! pacman -Q flameshot >/dev/null 2>&1; then
    echo "Flameshot kuruluyor..."
    if sudo -n true 2>/dev/null; then
        sudo pacman -S --needed --noconfirm flameshot
    elif command -v pkexec >/dev/null 2>&1 && [ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]; then
        pkexec pacman -S --needed --noconfirm flameshot
    elif command -v paru >/dev/null 2>&1; then
        paru -S --needed --noconfirm flameshot
    else
        sudo pacman -S --needed --noconfirm flameshot
    fi
fi

# 2. Flameshot ayarları (grim adapter kapalı, Wayland portallarıyla uyumlu)
mkdir -p "$HOME/.config/flameshot"
cat << 'EOF' > "$HOME/.config/flameshot/flameshot.ini"
[General]
contrastOpacity=188
saveLastRegion=false
startupLaunch=true
EOF

# 3. Arka planda çalışan eski flameshot varsa yenile
killall flameshot 2>/dev/null || true

echo "Flameshot başarıyla hazırlandı."
