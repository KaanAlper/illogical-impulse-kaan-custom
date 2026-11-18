#!/usr/bin/env bash
# Builds/updates the user-space plocate database for instant Everything-style
# file search (# prefix in Quickshell overview, Win+H).
set -u

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/everything"
DB="$CACHE_DIR/plocate.db"
TMP="$CACHE_DIR/plocate.db.tmp.$$"

if ! command -v updatedb >/dev/null 2>&1; then
    echo "updatedb bulunamadı (plocate paketi gerekli)." >&2
    exit 1
fi

mkdir -p "$CACHE_DIR"
trap 'rm -f "$TMP"' EXIT

updatedb -l 0 -U / -o "$TMP" \
    --prunepaths="/proc /sys /dev /run /tmp /var/tmp /mnt /media $HOME/.cache $HOME/.local/share/Trash" \
    && mv -f "$TMP" "$DB"
