#!/usr/bin/env bash
set -euo pipefail
if [ "$EUID" -ne 0 ]; then
    echo "sudo ile calistir: sudo bash $0" >&2
    exit 1
fi
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="/usr/share/plymouth/themes/xana"
SPINNER="/usr/share/plymouth/themes/spinner"

rm -rf "$DEST"
mkdir -p "$DEST"

# Copy required two-step dialog/UI assets from stock spinner theme (two-step aborts if missing)
for f in bullet.png capslock.png entry.png keyboard.png keymap-render.png lock.png; do
    if [ -f "$SPINNER/$f" ]; then
        cp "$SPINNER/$f" "$DEST/$f"
    fi
done

cp "$SRC/watermark.png" "$SRC/throbber-0001.png" "$SRC/xana.plymouth" "$DEST/"
cp "$SRC/throbber-0001.png" "$DEST/animation-0001.png"

plymouth-set-default-theme -R xana
echo "✓ XANA Plymouth temasi (two-step, tum gerekli varliklarla) kuruldu ve initramfs guncellendi."
