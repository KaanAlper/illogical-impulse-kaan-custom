#!/usr/bin/env bash
# Revert greetd direct Hyprland boot and re-enable SDDM.
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Bu betik sudo ile calistirilmalidir: sudo bash $0" >&2
    exit 1
fi

systemctl disable greetd.service 2>/dev/null || true
systemctl unmask plymouth-quit-wait.service 2>/dev/null || true
rm -f /etc/systemd/system/greetd.service.d/plymouth.conf
rmdir --ignore-fail-on-non-empty /etc/systemd/system/greetd.service.d 2>/dev/null || true
rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
rmdir --ignore-fail-on-non-empty /etc/systemd/system/getty@tty1.service.d 2>/dev/null || true
systemctl daemon-reload
pacman -S --needed --noconfirm sddm
systemctl enable sddm.service
echo "✓ greetd/autologin kaldirildi, SDDM yeniden etkinlestirildi."
