#!/usr/bin/env bash
# Revert tty1 autologin and re-enable SDDM.
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Bu betik sudo ile calistirilmalidir: sudo bash $0" >&2
    exit 1
fi

rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
rmdir --ignore-fail-on-non-empty /etc/systemd/system/getty@tty1.service.d 2>/dev/null || true
systemctl daemon-reload
systemctl enable sddm.service
echo "✓ tty1 autologin kaldirildi, SDDM yeniden etkinlestirildi."
