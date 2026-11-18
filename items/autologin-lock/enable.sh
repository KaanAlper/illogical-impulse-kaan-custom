#!/usr/bin/env bash
# Disable any active display manager (sddm, gdm, lightdm, greetd, ly, etc.)
# and enable tty1 autologin -> Hyprland -> immediate ii Super+L lockscreen.
set -euo pipefail

USER_NAME="${SUDO_USER:-kaanalper}"
DROPIN_DIR="/etc/systemd/system/getty@tty1.service.d"

if [ "$EUID" -ne 0 ]; then
    echo "Bu betik sudo ile calistirilmalidir: sudo bash $0" >&2
    exit 1
fi

for dm in sddm gdm lightdm lxdm ly greetd display-manager; do
    systemctl disable "${dm}.service" 2>/dev/null || true
done

if pacman -Q sddm >/dev/null 2>&1; then
    pacman -Rns --noconfirm sddm
fi

mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_DIR/autologin.conf" <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty -o '-p -f -- \\u' --noclear --autologin $USER_NAME %I \$TERM
EOF

systemctl daemon-reload
echo "✓ Diger giris ekranlari (SDDM/DM) iptal edildi, tty1 autologin ($USER_NAME) ayarlandi."
echo "  Yeniden baslatinca sistem dogrudan ii Super+L kilit ekraninda acilacaktir."
