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
USER_NAME="${SUDO_USER:-kaanalper}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
II_CFG="$USER_HOME/.config/illogical-impulse/config.json"
if [ -f "$II_CFG" ]; then
    sudo -u "$USER_NAME" python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d.setdefault("lock",{})["launchOnStartup"]=False; json.dump(d,open(p,"w"),indent=4)' "$II_CFG" || true
fi
echo "✓ greetd/autologin kaldirildi, SDDM yeniden etkinlestirildi."
