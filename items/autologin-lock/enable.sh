#!/usr/bin/env bash
# Disable any other display manager (sddm, gdm, lightdm, ly, etc.)
# and enable direct greetd -> start-hyprland -> ii Super+L lockscreen (no tty1 flash).
set -euo pipefail

USER_NAME="${SUDO_USER:-kaanalper}"
DROPIN_DIR="/etc/systemd/system/getty@tty1.service.d"

if [ "$EUID" -ne 0 ]; then
    echo "Bu betik sudo ile calistirilmalidir: sudo bash $0" >&2
    exit 1
fi

for dm in sddm gdm lightdm lxdm ly display-manager; do
    systemctl disable "${dm}.service" 2>/dev/null || true
done

if pacman -Q sddm >/dev/null 2>&1; then
    pacman -Rns --noconfirm sddm
fi

# Clean up any legacy tty1 autologin drop-in
rm -f "$DROPIN_DIR/autologin.conf"
rmdir --ignore-fail-on-non-empty "$DROPIN_DIR" 2>/dev/null || true
systemctl daemon-reload

pacman -S --needed --noconfirm greetd
mkdir -p /etc/greetd
cat > /etc/greetd/config.toml <<EOF
[terminal]
vt = 1

[initial_session]
command = "start-hyprland"
user = "$USER_NAME"

[default_session]
command = "start-hyprland"
user = "$USER_NAME"
EOF

# Keep Plymouth splash on screen until Hyprland draws its first frame (no tty1 flash)
mkdir -p /etc/systemd/system/greetd.service.d
cat > /etc/systemd/system/greetd.service.d/plymouth.conf <<'EOF'
[Unit]
Conflicts=plymouth-quit.service
After=systemd-user-sessions.service plymouth-start.service

[Service]
ExecStartPre=-/usr/bin/plymouth quit --retain-splash
EOF

systemctl daemon-reload
systemctl enable greetd.service
echo "✓ Diger giris ekranlari (SDDM/DM) iptal edildi, greetd ($USER_NAME -> start-hyprland) etkinlestirildi."
echo "  Yeniden baslatinca tty1/SDDM gorunmeden dogrudan Hyprland + ii Super+L kilit ekraninda acilacaktir."
