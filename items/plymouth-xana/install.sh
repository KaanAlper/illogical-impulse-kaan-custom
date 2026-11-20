#!/usr/bin/env bash
set -euo pipefail
if [ "$EUID" -ne 0 ]; then
    echo "sudo ile calistir: sudo bash $0" >&2
    exit 1
fi
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="/usr/share/plymouth/themes/xana"
mkdir -p "$DEST"
cp "$SRC/logo.png" "$SRC/xana.plymouth" "$SRC/xana.script" "$DEST/"
plymouth-set-default-theme -R xana
echo "✓ XANA Plymouth temasi kuruldu ve initramfs guncellendi."
