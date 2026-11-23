#!/bin/bash
# Canlı duvar kâğıdı bağımlılıkları: ffmpeg (ffprobe dahil), qt6-multimedia-ffmpeg, jq
set -euo pipefail
PKGS=(ffmpeg qt6-multimedia-ffmpeg jq)
missing=()
for p in "${PKGS[@]}"; do pacman -Q "$p" >/dev/null 2>&1 || missing+=("$p"); done
[ ${#missing[@]} -eq 0 ] && { echo "Canlı duvar kâğıdı bağımlılıkları zaten kurulu."; exit 0; }
echo "Kuruluyor: ${missing[*]}"
if sudo -n true 2>/dev/null; then
    sudo pacman -S --needed --noconfirm "${missing[@]}"
elif command -v pkexec >/dev/null 2>&1 && [ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]; then
    pkexec pacman -S --needed --noconfirm "${missing[@]}"
else
    sudo pacman -S --needed --noconfirm "${missing[@]}"
fi
echo "Canlı duvar kâğıdı bağımlılıkları hazır."
