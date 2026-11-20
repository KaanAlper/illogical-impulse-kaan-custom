#!/usr/bin/env bash
set -euo pipefail
if [ "$EUID" -ne 0 ]; then
    echo "sudo ile calistir: sudo bash $0" >&2
    exit 1
fi
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="/usr/share/plymouth/themes/xana"
rm -rf "$DEST"
mkdir -p "$DEST"
cp "$SRC/watermark.png" "$SRC/throbber-0001.png" "$SRC/xana.plymouth" "$DEST/"
plymouth-set-default-theme -R xana
echo "✓ XANA Plymouth temasi (two-step, her monitorde tam ortali) kuruldu ve initramfs guncellendi."
