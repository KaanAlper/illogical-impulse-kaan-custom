#!/usr/bin/env bash
# Install GRUB (if missing on systems using rEFInd, systemd-boot, Limine, Syslinux, Clover, etc.),
# apply Marathon-NewCascadia theme, configure /etc/default/grub, and optionally clean up old bootloaders.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$REPO/items/grub-theme/Marathon-NewCascadia"
DEST="/boot/grub/themes/Marathon-NewCascadia"
GRUB_CFG="/etc/default/grub"
FEATS="${DOTSYNC_FEATURES:-}"

if [ ! -d "$SRC" ]; then
    echo "✗ Tema klasörü bulunamadı: $SRC" >&2
    exit 1
fi

find_esp() {
    for d in /boot/efi /efi /boot; do
        if [ -d "$d" ] && [ "$(findmnt -no FSTYPE "$d" 2>/dev/null || true)" = "vfat" ]; then
            echo "$d"
            return 0
        fi
    done
    return 1
}

detect_other_bootloaders() {
    local found=()
    if sudo bootctl is-installed >/dev/null 2>&1 || pacman -Q systemd-boot-manager >/dev/null 2>&1 || [ -d /boot/loader ]; then
        found+=("systemd-boot")
    fi
    for pkg in refind limine limine-mkinitcpio-hook limine-snapper-sync syslinux clover-efi; do
        if pacman -Q "$pkg" >/dev/null 2>&1; then
            found+=("$pkg")
        fi
    done
    if [ -n "${ESP:-}" ] && [ -d "$ESP/EFI" ]; then
        local d base
        for d in "$ESP/EFI"/*; do
            [ -d "$d" ] || continue
            base="$(basename "$d")"
            case "${base,,}" in
                grub|boot|microsoft|apple|linux) ;;
                *) found+=("EFI/$base") ;;
            esac
        done
    fi
    echo "${found[*]:-}"
}

ESP="$(find_esp || true)"
OTHER_BLS="$(detect_other_bootloaders)"
if [ -n "$OTHER_BLS" ]; then
    echo "→ Algılanan mevcut önyükleyiciler: $OTHER_BLS"
fi

if ! pacman -Q grub >/dev/null 2>&1 || [ ! -f "$GRUB_CFG" ]; then
    echo "→ GRUB paketi kuruluyor (varsayılan önyükleyici yapılıyor)"
    sudo pacman -S --needed --noconfirm grub efibootmgr
    if [ -d /sys/firmware/efi ]; then
        if [ -z "$ESP" ]; then
            echo "✗ EFI sistem bölümü (/boot/efi, /efi veya /boot vfat) bulunamadı." >&2
            exit 1
        fi
        echo "→ GRUB EFI kurulumu yapılıyor ($ESP)"
        sudo grub-install --target=x86_64-efi --efi-directory="$ESP" --bootloader-id=GRUB
    fi
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

case ",$FEATS," in
    *,cleanup-old-bootloaders,*)
        echo "→ Eski önyükleyiciler temizleniyor (systemd-boot, rEFInd, Limine, Syslinux, Clover vb.)"
        if sudo bootctl is-installed >/dev/null 2>&1; then
            sudo bootctl remove || true
        fi
        for pkg in systemd-boot-manager refind limine-snapper-sync limine-mkinitcpio-hook limine syslinux clover-efi; do
            if pacman -Q "$pkg" >/dev/null 2>&1; then
                sudo pacman -Rns --noconfirm "$pkg" || true
            fi
        done

        for p in /boot/loader /boot/limine /boot/limine.conf /boot/syslinux; do
            [ -e "$p" ] && sudo rm -rf "$p"
        done

        if [ -n "$ESP" ] && [ -d "$ESP/EFI" ]; then
            [ -d "$ESP/loader" ] && sudo rm -rf "$ESP/loader"
            for d in "$ESP/EFI"/*; do
                [ -d "$d" ] || continue
                base="$(basename "$d")"
                case "${base,,}" in
                    grub|boot|microsoft|apple|linux) ;;
                    *)
                        echo "  - Kaldırılıyor: $d"
                        sudo rm -rf "$d"
                        ;;
                esac
            done
        fi

        if command -v efibootmgr >/dev/null 2>&1; then
            for bootnum in $(efibootmgr 2>/dev/null | awk '/rEFInd|Linux Boot Manager|systemd-boot|Limine|Clover|Syslinux/ {sub(/^Boot/, "", $1); sub(/\*$/, "", $1); print $1}'); do
                sudo efibootmgr -b "$bootnum" -B || true
            done
        fi

        if [ -d /sys/firmware/efi ] && [ -n "$ESP" ]; then
            sudo grub-install --target=x86_64-efi --efi-directory="$ESP" --bootloader-id=GRUB
        fi
        echo "✓ Eski önyükleyiciler temizlendi; GRUB varsayılan."
        ;;
esac

echo "✓ GRUB teması (Marathon-NewCascadia) kuruldu."
