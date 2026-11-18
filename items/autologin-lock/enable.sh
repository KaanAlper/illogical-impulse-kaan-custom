#!/usr/bin/env bash
# Disable SDDM and enable tty1 autologin -> Hyprland -> immediate Super+L lockscreen.
set -euo pipefail

USER_NAME="${SUDO_USER:-kaanalper}"
DROPIN_DIR="/etc/systemd/system/getty@tty1.service.d"

if [ "$EUID" -ne 0 ]; then
    echo "Bu betik sudo ile calistirilmalidir: sudo bash $0" >&2
    exit 1
fi

systemctl disable sddm.service || true
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_DIR/autologin.conf" <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty -o '-p -f -- \\u' --noclear --autologin $USER_NAME %I \$TERM
EOF

systemctl daemon-reload
echo "✓ SDDM devre disi birakildi, tty1 autologin ($USER_NAME) ayarlandi."
echo "  Yeniden baslatinca sistem dogrudan Super+L kilit ekraninda acilacaktir."
