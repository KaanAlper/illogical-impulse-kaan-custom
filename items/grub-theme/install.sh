#!/usr/bin/env bash
# Install Marathon-NewCascadia GRUB theme and configure /etc/default/grub.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$REPO/items/grub-theme/Marathon-NewCascadia"
DEST="/boot/grub/themes/Marathon-NewCascadia"
GRUB_CFG="/etc/default/grub"

if [ ! -d "$SRC" ]; then
    echo "✗ Tema klasörü bulunamadı: $SRC" >&2
    exit 1
fi

echo "→ GRUB teması kuruluyor: $DEST"
sudo install -d -m 755 "$DEST"
sudo cp -rf "$SRC"/. "$DEST"/
sudo chmod -R a+rX "$DEST"

echo "→ /etc/default/grub güncelleniyor"
sudo python3 - "$GRUB_CFG" <<'PY'
import pathlib, re, sys

p = pathlib.Path(sys.argv[1])
txt = p.read_text(encoding="utf-8")

def set_kv(text, key, val):
    pat = re.compile(rf"(?m)^#?\s*{re.escape(key)}=.*$")
    line = f"{key}={val}"
    if pat.search(text):
        return pat.sub(line, text, count=1)
    return text.rstrip() + "\n" + line + "\n"

txt = set_kv(txt, "GRUB_TIMEOUT", "'5'")
txt = set_kv(txt, "GRUB_TIMEOUT_STYLE", "menu")
txt = set_kv(txt, "GRUB_GFXMODE", "1920x1080x32")
txt = set_kv(txt, "GRUB_GFXPAYLOAD_LINUX", "keep")
txt = set_kv(txt, "GRUB_THEME", "'/boot/grub/themes/Marathon-NewCascadia/theme.txt'")

m = re.search(r"(?m)^GRUB_CMDLINE_LINUX_DEFAULT=(['\"])(.*)\1$", txt)
if m:
    q, args = m.group(1), m.group(2).split()
    for tok in ("quiet", "splash"):
        if tok not in args:
            args.append(tok)
    txt = txt[:m.start()] + f"GRUB_CMDLINE_LINUX_DEFAULT={q}{' '.join(args)}{q}" + txt[m.end():]

p.write_text(txt, encoding="utf-8")
PY

echo "→ grub.cfg yeniden oluşturuluyor"
sudo grub-mkconfig -o /boot/grub/grub.cfg
echo "✓ GRUB teması (Marathon-NewCascadia) kuruldu."
