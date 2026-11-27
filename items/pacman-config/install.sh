#!/usr/bin/env bash
# pacman/makepkg ayarları: aria2 ile paralel indirme (pacman XferCommand, makepkg DLAGENTS) ve Chaotic-AUR deposu.
# Kullanım: install.sh [aria2] [makepkg-aria2] [chaotic]   (argümansız: ikisi de). Idempotenttir; tekrar çalıştırmak güvenlidir.
set -euo pipefail

CONF=/etc/pacman.conf
WANT=("$@")
[ ${#WANT[@]} -eq 0 ] && WANT=(aria2 makepkg-aria2 chaotic)

want() { local x; for x in "${WANT[@]}"; do [ "$x" = "$1" ] && return 0; done; return 1; }

[ -f "$CONF.dotsync.bak" ] || sudo cp -a "$CONF" "$CONF.dotsync.bak"

setup_aria2() {
    pacman -Q aria2 >/dev/null 2>&1 || sudo pacman -S --needed --noconfirm aria2
    # Eski/yorumlu/çift XferCommand satırlarını temizle, [options] altına tek satır ekle.
    sudo sed -i -E '/^#?XferCommand/d' "$CONF"
    sudo sed -i '/^\[options\]/a XferCommand = /usr/bin/aria2c -q --allow-overwrite=true -c -m 2 -s 16 -k 1M -j 10 -x 16 --summary-interval=0 -d / -o %o %u' "$CONF"
    echo "✓ aria2 XferCommand ayarlandı"
}

setup_makepkg_aria2() {
    pacman -Q aria2 >/dev/null 2>&1 || sudo pacman -S --needed --noconfirm aria2
    # AUR/makepkg kaynak indirmeleri (paru/yay dahil): ana dosyaya dokunmadan drop-in ile.
    sudo mkdir -p /etc/makepkg.conf.d
    sudo tee /etc/makepkg.conf.d/aria2.conf >/dev/null <<'CONF'
# dotsync: makepkg ilk eşleşen ajanı kullanır; bu yüzden aria2 girişleri varsayılanların ÖNÜNE konur.
# http/https/ftp aria2 ile; file/rsync/scp varsayılan kalır.
DLAGENTS=('ftp::/usr/bin/aria2c -q --allow-overwrite=true --auto-file-renaming=false -c -s 16 -x 16 -k 1M -o %o %u'
           'http::/usr/bin/aria2c -q --allow-overwrite=true --auto-file-renaming=false -c -s 16 -x 16 -k 1M -o %o %u'
           'https::/usr/bin/aria2c -q --allow-overwrite=true --auto-file-renaming=false -c -s 16 -x 16 -k 1M -o %o %u'
           "${DLAGENTS[@]}")
CONF
    echo "✓ makepkg DLAGENTS aria2 yapıldı (/etc/makepkg.conf.d/aria2.conf)"
}

setup_chaotic() {
    if ! pacman -Q chaotic-keyring chaotic-mirrorlist >/dev/null 2>&1; then
        # Depo eklenmeden önce anahtar + mirrorlist paketleri doğrudan indirilip kurulur.
        sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com
        sudo pacman-key --lsign-key 3056513887B78AEB
        sudo pacman -U --noconfirm \
            'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' \
            'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'
    fi
    if ! grep -q '^\[chaotic-aur\]' "$CONF"; then
        printf '\n[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist\n' | sudo tee -a "$CONF" >/dev/null
    fi
    sudo pacman -Sy
    echo "✓ Chaotic-AUR eklendi"
}

want aria2 && setup_aria2
want makepkg-aria2 && setup_makepkg_aria2
want chaotic && setup_chaotic
exit 0
