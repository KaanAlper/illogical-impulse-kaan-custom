#!/bin/bash
# illogical-impulse-kaan-custom tek satır kurulum:
#   curl -fsSL https://raw.githubusercontent.com/KaanAlper/illogical-impulse-kaan-custom/main/install.sh | bash
#
# Akış: ~/kaan-dots'u klonlar (varsa günceller) -> kurulum penceresi açılır:
#   1) "Kuruluma hoş geldin": installer (dotsync) kurulur  [yalnızca ilk kurulumda]
#   2) "Neleri kuralım?": sistemde olmayanlar onay kutularıyla listelenir
# Sonraki açılışlarda yalnızca 2. ekran, o da yalnızca eksik varsa gelir.
# Sistem dosyalarına dokunmaz; "İndir" demeden hiçbir ayar/paket kurulmaz.
set -euo pipefail

REPO="${KAAN_DOTS_REPO:-KaanAlper/illogical-impulse-kaan-custom}"
DEST="${KAAN_DOTS_DIR:-$HOME/kaan-dots}"

missing_pkgs=()
command -v git >/dev/null || missing_pkgs+=(git)
command -v curl >/dev/null || missing_pkgs+=(curl)
command -v python3 >/dev/null || missing_pkgs+=(python)
if [ ${#missing_pkgs[@]} -gt 0 ]; then
    echo "→ Eksik temel araçlar kuruluyor: ${missing_pkgs[*]}"
    sudo pacman -S --needed --noconfirm "${missing_pkgs[@]}"
fi

if [ -d "$DEST/.git" ]; then
    echo "→ $DEST güncelleniyor"
    git -C "$DEST" pull --ff-only
else
    echo "→ $REPO klonlanıyor: $DEST"
    git clone "https://github.com/$REPO.git" "$DEST"
fi

export PATH="$HOME/.local/bin:$PATH"

# Arayüz: quickshell + Wayland oturumu varsa pencere, yoksa metin modu.
if command -v qs >/dev/null && [ -n "${WAYLAND_DISPLAY:-}" ] && [ -z "${DOTSYNC_NO_UI:-}" ]; then
    echo "→ kurulum penceresi açılıyor"
    DOTSYNC_BIN="$DEST/dotsync/dotsync.py" DOTSYNC_BOOTSTRAP="$DEST/bootstrap.sh" \
        qs -p "$DEST/dotsync/ui" || true
fi

# Pencere açılamadıysa ya da kurulum tamamlanmadan kapatıldıysa: metin modunda tamamla.
if ! command -v dotsync >/dev/null; then
    echo "→ installer kuruluyor (metin modu)"
    "$DEST/bootstrap.sh"
    dotsync status | python3 -c "import json,sys; d=json.load(sys.stdin); print('Eksikler:', ', '.join(d['pending']) or 'yok')"
    echo "İndirmek için: dotsync apply <id>...   (liste: dotsync status)"
fi
echo "Tamam. Sonradan eksik kontrolü: dotsync setup"
