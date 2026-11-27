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
    pacman -Rcns --noconfirm sddm
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

# Keep Plymouth logo on screen until greetd releases DRM master right before start-hyprland (no deadlock, no flicker)
systemctl mask plymouth-quit-wait.service 2>/dev/null || true
mkdir -p /etc/systemd/system/greetd.service.d
cat > /etc/systemd/system/greetd.service.d/plymouth.conf <<'EOF'
[Unit]
After=
After=systemd-user-sessions.service plymouth-start.service getty@tty1.service
Conflicts=getty@tty1.service plymouth-quit.service

[Service]
ExecStartPre=-/usr/bin/plymouth quit --retain-splash
EOF

systemctl daemon-reload
systemctl enable greetd.service

# Enable native Quickshell lock.launchOnStartup (locks on Frame 0 before desktop/keyring popup)
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
II_CFG="$USER_HOME/.config/illogical-impulse/config.json"
if [ -f "$II_CFG" ]; then
    sudo -u "$USER_NAME" python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d.setdefault("lock",{})["launchOnStartup"]=True; json.dump(d,open(p,"w"),indent=4)' "$II_CFG" || true
fi

# Hide tty kernel/udev boot text and blinking cursor on GRUB systems
if [ -f /etc/default/grub ] && ! grep -q "vt.global_cursor_default=0" /etc/default/grub; then
    sed -i 's|splash loglevel=3|quiet splash loglevel=3 rd.udev.log_level=3 vt.global_cursor_default=0|' /etc/default/grub
    grub-mkconfig -o /boot/grub/grub.cfg || true
fi
echo "✓ Diger giris ekranlari (SDDM/DM) iptal edildi, greetd ($USER_NAME -> start-hyprland) etkinlestirildi."
echo "  Yeniden baslatinca tty1/SDDM gorunmeden dogrudan Hyprland + ii Super+L kilit ekraninda acilacaktir."
