#!/bin/bash
# AI CLI kurulumu: ai-cli/install.sh <claude|codex|agy>
# Yönetici işlemleri düz `sudo` ile yapılır; dotsync uygulama içi parolayı sudo kabuğu ile sağlar.
set -euo pipefail
case "${1:-}" in
    claude) pkg=claude-code;   npm_pkg=@anthropic-ai/claude-code ;;
    codex)  pkg=openai-codex;  npm_pkg=@openai/codex ;;
    agy)    pkg=antigravity;   npm_pkg= ;;
    *) echo "kullanım: $0 claude|codex|agy" >&2; exit 2 ;;
esac
if pacman -Q "$pkg" >/dev/null 2>&1; then echo "$pkg zaten kurulu."; exit 0; fi
if pacman -Si "$pkg" >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm "$pkg"
elif command -v paru >/dev/null 2>&1; then
    paru -S --needed --noconfirm "$pkg"
elif command -v yay >/dev/null 2>&1; then
    yay -S --needed --noconfirm "$pkg"
elif [ -n "$npm_pkg" ] && command -v npm >/dev/null 2>&1; then
    npm install -g --prefix "$HOME/.local" "$npm_pkg"
else
    echo "HATA: $pkg kurulamadı (pacman/paru/yay/npm bulunamadı)" >&2; exit 1
fi
